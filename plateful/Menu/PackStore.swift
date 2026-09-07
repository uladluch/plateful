import CryptoKit
import Foundation

/// Где живут паки и какой из них брать.
///
/// Сид в бандле есть всегда — приложение отвечает без сети и переживает
/// недоступность Storage. Скачанный пак кладётся рядом и вытесняет сид,
/// только если он новее и целиком прошёл проверку.
// Проект собирается с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor — это верно
// для SwiftUI, но не для слоя данных: каталог разбирается и строится вне
// главного потока. Отсюда `nonisolated` на типах ниже.
/// Хеширование пака. Вынесено, чтобы конвейер, приложение и тесты считали
/// контрольную сумму одним и тем же способом.
nonisolated enum PackStoreHashing {
    static func sha256Hex(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
}

nonisolated struct PackStore: Sendable {

    /// Имя сида в бандле. Кладётся туда конвейером: `backend/scripts/build_seed.py`.
    static let seedResource = "seed-pack"

    /// Откуда брать сид.
    enum Seed: Sendable {
        /// Искать в бандле — **при каждом обращении**.
        ///
        /// Раньше путь вычислялся один раз при создании хранилища, и разовый
        /// промах `Bundle.main.url` отравлял всю сессию: приложение до
        /// перезапуска считало, что сида нет. Наблюдалось в симуляторе, когда
        /// запуск пришёлся на подмену бандла при установке.
        case bundle
        /// Явный файл — для тестов; `nil` означает «сида нет вовсе».
        case file(URL?)
    }

    let seed: Seed
    let installedURL: URL

    init(seed: Seed, installedURL: URL) {
        self.seed = seed
        self.installedURL = installedURL
    }

    init(seedURL: URL?, installedURL: URL) {
        self.init(seed: .file(seedURL), installedURL: installedURL)
    }

    var seedURL: URL? {
        switch seed {
        case .bundle: Bundle.main.url(forResource: Self.seedResource, withExtension: "json")
        case .file(let url): url
        }
    }

    /// Обычная конфигурация приложения.
    static func standard(fileManager: FileManager = .default) -> PackStore {
        let support = (try? fileManager.url(
            for: .applicationSupportDirectory, in: .userDomainMask,
            appropriateFor: nil, create: true)) ?? fileManager.temporaryDirectory
        let directory = support.appending(path: "MenuPacks", directoryHint: .isDirectory)
        try? fileManager.createDirectory(at: directory, withIntermediateDirectories: true)

        return PackStore(
            seed: .bundle,
            installedURL: directory.appending(path: "current.json", directoryHint: .notDirectory))
    }

    // MARK: - Чтение

    /// Пак с наибольшей версией из доступных.
    ///
    /// Битый или несовместимый скачанный пак не должен ронять приложение:
    /// он удаляется, и мы честно откатываемся на сид.
    func loadBest() throws -> MenuPack {
        let installed = loadInstalled()

        // Ошибку сида нельзя глушить `try?`: тогда «сид не разобрался»
        // становится неотличим от «сида нет», и настоящая причина теряется.
        var seed: MenuPack?
        var seedFailure: Error?
        if let seedURL {
            do {
                seed = try MenuPack.decode(from: Data(contentsOf: seedURL))
            } catch {
                seedFailure = error
            }
        }

        switch (installed, seed) {
        case let (installed?, seed?):
            return installed.version > seed.version ? installed : seed
        case let (installed?, nil):
            return installed
        case let (nil, seed?):
            return seed
        case (nil, nil):
            throw seedFailure ?? MenuPack.LoadError.noPackAvailable
        }
    }

    private func loadInstalled() -> MenuPack? {
        guard let data = try? Data(contentsOf: installedURL) else { return nil }
        do {
            return try MenuPack.decode(from: data)
        } catch {
            // Не оставляем мусор лежать: следующий запуск не должен спотыкаться
            // о тот же файл.
            try? FileManager.default.removeItem(at: installedURL)
            return nil
        }
    }

    // MARK: - Установка

    enum InstallResult: Sendable {
        case installed(MenuPack)
        /// Пришло не новее того, что уже есть, — файл не трогали.
        case skipped(version: Int)
    }

    /// Ставит скачанный пак: хеш → распаковка → разбор → атомарная подмена.
    ///
    /// Хеш считается по сжатым байтам, ровно как его пишет манифест: так
    /// повреждение ловится до того, как мы потратим память на распаковку.
    @discardableResult
    func install(compressed: Data, expectedSHA256: String, newerThan currentVersion: Int) throws -> InstallResult {
        let digest = PackStoreHashing.sha256Hex(compressed)
        guard digest == expectedSHA256.lowercased() else {
            throw MenuPack.LoadError.checksumMismatch
        }

        // Apple называет `.zlib` сырой DEFLATE — без zlib-контейнера.
        // Конвейер жмёт именно так, см. pack.py::_raw_deflate.
        guard let raw = try? (compressed as NSData).decompressed(using: .zlib) as Data else {
            throw MenuPack.LoadError.decompressionFailed
        }

        let pack = try MenuPack.decode(from: raw)
        guard pack.version > currentVersion else { return .skipped(version: pack.version) }

        try writeAtomically(raw)
        return .installed(pack)
    }

    private func writeAtomically(_ data: Data) throws {
        let temporary = installedURL.deletingLastPathComponent()
            .appending(path: "incoming-\(UUID().uuidString).json", directoryHint: .notDirectory)
        try data.write(to: temporary, options: .atomic)
        defer { try? FileManager.default.removeItem(at: temporary) }

        if FileManager.default.fileExists(atPath: installedURL.path(percentEncoded: false)) {
            _ = try FileManager.default.replaceItemAt(installedURL, withItemAt: temporary)
        } else {
            try FileManager.default.moveItem(at: temporary, to: installedURL)
        }
    }

    /// Откат на сид — например, если данные скачанного пака оказались негодными.
    func removeInstalled() {
        try? FileManager.default.removeItem(at: installedURL)
    }
}
