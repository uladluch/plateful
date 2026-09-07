import Foundation
import Testing

@testable import plateful

@Suite("Обновление пака")
struct PackUpdaterTests {

    /// Транспорт без сети: отдаёт заранее подготовленные байты по URL.
    private struct StubTransport: PackTransport {
        let responses: [URL: Result<Data, any Error>]

        func data(from url: URL) async throws -> Data {
            switch responses[url] {
            case .success(let data): return data
            case .failure(let error): throw error
            case nil: throw PackUpdater.UpdateError.badResponse(404)
            }
        }
    }

    private static let manifestURL = URL(
        string: "https://packs.example.com/storage/v1/object/public/packs/manifest.json")!
    private static let packURL = URL(
        string: "https://packs.example.com/storage/v1/object/public/packs/v2.deflate")!

    private static func packJSON(version: Int, kcal: Double) -> Data {
        let json: [String: Any] = [
            "format": 1, "version": version,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": 1]],
            "items": [["chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
                       "kcal": kcal, "protein": 25, "carbs": 46, "fat": 28]],
        ]
        return try! JSONSerialization.data(withJSONObject: json)
    }

    private static func manifestJSON(
        version: Int, sha256: String, url: URL = packURL, format: Int = 1
    ) -> Data {
        try! JSONSerialization.data(withJSONObject: [
            "format": format, "version": version, "url": url.absoluteString,
            "sha256": sha256, "itemCount": 1, "releasedAt": "2026-09-07",
        ])
    }

    private static func deflated(_ data: Data) throws -> Data {
        try (data as NSData).compressed(using: .zlib) as Data
    }

    /// Тот же способ, которым считает PackStore: тест проверяет договорённость
    /// о контрольной сумме, а не свою реализацию хеширования.
    private static func sha256(_ data: Data) -> String {
        PackStoreHashing.sha256Hex(data)
    }

    private struct Sandbox: ~Copyable {
        let directory: URL
        let store: PackStore

        init() throws {
            directory = FileManager.default.temporaryDirectory
                .appending(path: "updater-\(UUID().uuidString)", directoryHint: .isDirectory)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)

            let seedURL = directory.appending(path: "seed.json", directoryHint: .notDirectory)
            try PackUpdaterTests.packJSON(version: 1, kcal: 540).write(to: seedURL)
            store = PackStore(
                seedURL: seedURL,
                installedURL: directory.appending(path: "current.json", directoryHint: .notDirectory))
        }

        deinit { try? FileManager.default.removeItem(at: directory) }
    }

    private func makeUpdater(_ sandbox: borrowing Sandbox,
                             responses: [URL: Result<Data, any Error>]) -> PackUpdater {
        PackUpdater(store: sandbox.store,
                    transport: StubTransport(responses: responses),
                    manifestURL: Self.manifestURL)
    }

    @Test("новый пак скачивается и ставится")
    func installsNewerPack() async throws {
        let sandbox = try Sandbox()
        let compressed = try Self.deflated(Self.packJSON(version: 2, kcal: 580))
        let updater = makeUpdater(sandbox, responses: [
            Self.manifestURL: .success(Self.manifestJSON(version: 2, sha256: Self.sha256(compressed))),
            Self.packURL: .success(compressed),
        ])

        let outcome = try await updater.update(currentVersion: 1)
        #expect(outcome == .installed(version: 2, itemCount: 1))
        #expect(try sandbox.store.loadBest().version == 2)
    }

    @Test("пак не новее — сеть за ним не дёргается")
    func skipsWhenNotNewer() async throws {
        let sandbox = try Sandbox()
        // Пак в ответах отсутствует: если updater за ним пойдёт, будет 404.
        let updater = makeUpdater(sandbox, responses: [
            Self.manifestURL: .success(Self.manifestJSON(version: 2, sha256: "неважно")),
        ])

        #expect(try await updater.update(currentVersion: 2) == .upToDate(version: 2))
        #expect(try await updater.update(currentVersion: 5) == .upToDate(version: 5))
    }

    /// Подменённый манифест не должен уводить загрузку на чужой сервер.
    @Test("ссылка на пак с чужого хоста отвергается")
    func rejectsForeignHost() async throws {
        let sandbox = try Sandbox()
        let evil = URL(string: "https://attacker.example.net/pack.deflate")!
        let updater = makeUpdater(sandbox, responses: [
            Self.manifestURL: .success(
                Self.manifestJSON(version: 2, sha256: "неважно", url: evil)),
            evil: .success(Data("что угодно".utf8)),
        ])

        await #expect(throws: PackUpdater.UpdateError.self) {
            try await updater.update(currentVersion: 1)
        }
        #expect(try sandbox.store.loadBest().version == 1)
    }

    @Test("несовпавшая контрольная сумма не ставится")
    func rejectsBadChecksum() async throws {
        let sandbox = try Sandbox()
        let compressed = try Self.deflated(Self.packJSON(version: 2, kcal: 580))
        let updater = makeUpdater(sandbox, responses: [
            Self.manifestURL: .success(
                Self.manifestJSON(version: 2, sha256: String(repeating: "0", count: 64))),
            Self.packURL: .success(compressed),
        ])

        await #expect(throws: MenuPack.LoadError.self) {
            try await updater.update(currentVersion: 1)
        }
        #expect(try sandbox.store.loadBest().version == 1)
    }

    @Test("чужой формат манифеста отвергается")
    func rejectsUnsupportedFormat() async throws {
        let sandbox = try Sandbox()
        let updater = makeUpdater(sandbox, responses: [
            Self.manifestURL: .success(
                Self.manifestJSON(version: 99, sha256: "неважно", format: 99)),
        ])

        await #expect(throws: MenuPack.LoadError.self) {
            try await updater.update(currentVersion: 1)
        }
    }

    /// Сеть падает постоянно, и это не повод ломать справочник.
    @Test("недоступная сеть оставляет приложение на текущем паке")
    func survivesNetworkFailure() async throws {
        let sandbox = try Sandbox()
        let updater = makeUpdater(sandbox, responses: [
            Self.manifestURL: .failure(URLError(.notConnectedToInternet)),
        ])

        await #expect(throws: (any Error).self) {
            try await updater.update(currentVersion: 1)
        }
        #expect(try sandbox.store.loadBest().version == 1)
    }

    @Test("манифест-мусор отвергается")
    func rejectsGarbageManifest() async throws {
        let sandbox = try Sandbox()
        let updater = makeUpdater(sandbox, responses: [
            Self.manifestURL: .success(Data("не json".utf8)),
        ])

        await #expect(throws: MenuPack.LoadError.self) {
            try await updater.update(currentVersion: 1)
        }
    }
}
