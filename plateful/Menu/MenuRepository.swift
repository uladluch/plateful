import Foundation
import OSLog
import Observation

/// Единственная граница между интерфейсом и данными.
///
/// Экраны не знают, откуда взялся каталог — из бандла или из скачанного
/// пака. Поэтому обновления по сети можно включить, не трогая ни одного вью.
@MainActor
@Observable
final class MenuRepository {

    enum State: Sendable {
        case loading
        case ready(MenuCatalog)
        case failed(String)
    }

    private(set) var state: State = .loading

    /// Идущая загрузка. Без неё параллельные вызовы гонятся, и поздно
    /// завершившийся разбор старого пака затирает уже загруженный новый —
    /// человек видит устаревшие цифры после успешного обновления.
    private var loading: Task<Void, Never>?

    private let store: PackStore
    private let updater: PackUpdater
    private let log = Logger(subsystem: "com.anluch.plateful", category: "menu")

    init(store: PackStore = .standard(), transport: PackTransport = NetworkPackTransport()) {
        self.store = store
        self.updater = PackUpdater(store: store, transport: transport)
    }

    /// Готовый каталог без обращения к диску — для превью и тестов.
    init(catalog: MenuCatalog) {
        let store = PackStore.standard()
        self.store = store
        self.updater = PackUpdater(store: store)
        self.state = .ready(catalog)
    }

    var catalog: MenuCatalog? {
        if case .ready(let catalog) = state { return catalog }
        return nil
    }

    var chains: [MenuChain] { catalog?.chains ?? [] }

    /// Разбор пака идёт вне главного потока: это мегабайты JSON, на главном
    /// они видны как подвисший запуск.
    /// Загружает каталог. Повторные и параллельные вызовы схлопываются в один.
    ///
    /// `.task` срабатывает не один раз за жизнь окна, а разбор пака стоит
    /// четверть секунды.
    func load(force: Bool = false) async {
        if let loading {
            await loading.value
            if !force { return }
        }
        if case .ready = state, !force { return }

        let task = Task { @MainActor [weak self] in
            await self?.performLoad()
            return ()
        }
        loading = task
        await task.value
        loading = nil
    }

    private func performLoad() async {
        state = .loading
        let store = store
        let started = ContinuousClock.now
        do {
            let catalog = try await Task.detached(priority: .userInitiated) {
                MenuCatalog(pack: try store.loadBest())
            }.value
            state = .ready(catalog)
            log.info("""
                Каталог готов: \(catalog.items.count) позиций, \
                \(catalog.chains.count) сетей, пак v\(catalog.version) \
                (\(catalog.source), \(catalog.observed)) за \
                \(started.duration(to: .now).formatted(.units(allowed: [.milliseconds])))
                """)
        } catch {
            state = .failed(error.localizedDescription)
            // Без указания, нашёлся ли сид, по логу не понять, чинить сборку
            // или искать файл.
            log.error("""
                Каталог не загрузился: \(error.localizedDescription). \
                Сид в бандле: \(store.seedURL?.lastPathComponent ?? "НЕ НАЙДЕН"), \
                скачанный пак: \(FileManager.default.fileExists(
                    atPath: store.installedURL.path(percentEncoded: false)) ? "есть" : "нет")
                """)
        }
    }

    /// Проверяет, не вышел ли пак новее, и подхватывает его.
    ///
    /// Обновление необязательно: каталог уже работает, поэтому любая неудача
    /// остаётся в логе и ничего не ломает. Экраны об этом даже не знают —
    /// каталог просто становится свежее.
    func checkForUpdate() async {
        guard let catalog else { return }
        do {
            switch try await updater.update(currentVersion: catalog.version) {
            case .upToDate(let version):
                log.info("Пак v\(version) — обновлений нет")
            case .installed(let version, let itemCount):
                log.info("Установлен пак v\(version): \(itemCount) позиций, перезагружаю каталог")
                await load(force: true)
            }
        } catch {
            log.info("Обновление не состоялось, остаёмся на текущем паке: \(error.localizedDescription)")
        }
    }

    func search(_ query: String, in chain: String? = nil, limit: Int = 50) -> [MenuItem] {
        catalog?.search(query, in: chain, limit: limit) ?? []
    }

    func items(in chain: String) -> [MenuItem] {
        catalog?.items(in: chain) ?? []
    }

    func sections(for chain: String) -> [MenuSection] {
        catalog?.sections(for: chain) ?? []
    }

    /// Все варианты одного блюда. Пусто, если он один.
    func variants(of item: MenuItem) -> [MenuItem] {
        catalog?.variants(of: item) ?? []
    }

    /// Свернуть варианты в одну строку. Применяется последней, уже после
    /// фильтра по целям.
    func collapsingVariants(_ items: [MenuItem]) -> [MenuItem] {
        catalog?.collapsingVariants(items) ?? items
    }

    func collapsingVariants(_ sections: [MenuSection]) -> [MenuSection] {
        catalog?.collapsingVariants(sections) ?? sections
    }

    /// Позиция по ссылке, пережившей обновление пака, — для сохранённых
    /// заказов и истории.
    func item(_ id: MenuItem.PersistentID) -> MenuItem? {
        catalog?.items(in: id.chain).first { $0.key == id.key }
    }
}
