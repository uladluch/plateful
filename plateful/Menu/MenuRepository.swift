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

    private let store: PackStore
    private let log = Logger(subsystem: "com.anluch.plateful", category: "menu")

    init(store: PackStore = .standard()) {
        self.store = store
    }

    /// Готовый каталог без обращения к диску — для превью и тестов.
    init(catalog: MenuCatalog) {
        self.store = .standard()
        self.state = .ready(catalog)
    }

    var catalog: MenuCatalog? {
        if case .ready(let catalog) = state { return catalog }
        return nil
    }

    var chains: [MenuChain] { catalog?.chains ?? [] }

    /// Разбор пака идёт вне главного потока: это мегабайты JSON, на главном
    /// они видны как подвисший запуск.
    /// Загружает каталог. Повторный вызов на готовом каталоге ничего не делает.
    ///
    /// `.task` может сработать не один раз за жизнь окна, а разбор пака стоит
    /// четверть секунды — повторять его незачем.
    func load(force: Bool = false) async {
        if case .ready = state, !force { return }

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

    func search(_ query: String, in chain: String? = nil, limit: Int = 50) -> [MenuItem] {
        catalog?.search(query, in: chain, limit: limit) ?? []
    }

    func items(in chain: String) -> [MenuItem] {
        catalog?.items(in: chain) ?? []
    }

    func sections(for chain: String) -> [MenuSection] {
        catalog?.sections(for: chain) ?? []
    }

    /// Позиция по ссылке, пережившей обновление пака, — для сохранённых
    /// заказов и истории.
    func item(_ id: MenuItem.PersistentID) -> MenuItem? {
        catalog?.items(in: id.chain).first { $0.key == id.key }
    }
}
