import CryptoKit
import Foundation
import Testing

@testable import plateful

@Suite("Хранилище паков")
struct PackStoreTests {

    /// Песочница на один тест: PackStore пишет на диск, и тесты не должны
    /// видеть следы друг друга.
    private struct Sandbox: ~Copyable {
        let directory: URL
        let store: PackStore

        init(seedVersion: Int = 1) throws {
            directory = FileManager.default.temporaryDirectory
                .appending(path: "packstore-\(UUID().uuidString)", directoryHint: .isDirectory)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)

            let seedURL = directory.appending(path: "seed.json", directoryHint: .notDirectory)
            try PackStoreTests.packJSON(version: seedVersion, kcal: 540).write(to: seedURL)

            store = PackStore(
                seedURL: seedURL,
                installedURL: directory.appending(path: "current.json", directoryHint: .notDirectory))
        }

        deinit { try? FileManager.default.removeItem(at: directory) }
    }

    private static func packJSON(version: Int, kcal: Double,
                                 source: String = "menustat-2018") -> Data {
        let json: [String: Any] = [
            "format": 1, "version": version,
            "source": source, "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": 1]],
            "items": [[
                "chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
                "kcal": kcal, "protein": 25, "carbs": 46, "fat": 28,
            ]],
        ]
        return try! JSONSerialization.data(withJSONObject: json)
    }

    private static func deflated(_ data: Data) throws -> Data {
        // У Apple `.zlib` — сырой DEFLATE, тот же формат, что пишет конвейер
        // (см. pack.py::_raw_deflate). Симметричность сжатия и распаковки
        // здесь и проверяется.
        try (data as NSData).compressed(using: .zlib) as Data
    }

    private static func sha256(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }

    @Test("без скачанного пака берётся сид")
    func fallsBackToSeed() throws {
        let sandbox = try Sandbox()
        #expect(try sandbox.store.loadBest().version == 1)
    }

    @Test("нет ни одного пака — честная ошибка")
    func noPackAtAll() throws {
        let directory = FileManager.default.temporaryDirectory
            .appending(path: "empty-\(UUID().uuidString)", directoryHint: .isDirectory)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }

        let store = PackStore(
            seedURL: nil,
            installedURL: directory.appending(path: "current.json", directoryHint: .notDirectory))
        #expect(throws: MenuPack.LoadError.self) { try store.loadBest() }
    }

    @Test("новый пак вытесняет сид")
    func newerPackWins() throws {
        let sandbox = try Sandbox()
        let payload = Self.packJSON(version: 2, kcal: 580)
        let compressed = try Self.deflated(payload)

        let result = try sandbox.store.install(
            compressed: compressed, expectedSHA256: Self.sha256(compressed), newerThan: 1)
        guard case .installed(let pack) = result else {
            Issue.record("ожидалась установка, получено \(result)")
            return
        }
        #expect(pack.version == 2)
        #expect(try sandbox.store.loadBest().version == 2)

        let catalog = MenuCatalog(pack: try sandbox.store.loadBest())
        #expect(catalog.search("big mac").first?.kcal == 580)
    }

    @Test("пак не новее текущего не ставится")
    func skipsOlderPack() throws {
        let sandbox = try Sandbox()
        let compressed = try Self.deflated(Self.packJSON(version: 2, kcal: 580))

        let result = try sandbox.store.install(
            compressed: compressed, expectedSHA256: Self.sha256(compressed), newerThan: 2)
        guard case .skipped(let version) = result else {
            Issue.record("ожидался пропуск, получено \(result)")
            return
        }
        #expect(version == 2)
        #expect(try sandbox.store.loadBest().version == 1)
    }

    /// Хеш считается до распаковки: повреждение ловится, не потратив память.
    @Test("несовпавшая контрольная сумма отклоняется и ничего не пишет")
    func rejectsBadChecksum() throws {
        let sandbox = try Sandbox()
        let compressed = try Self.deflated(Self.packJSON(version: 2, kcal: 580))

        #expect(throws: MenuPack.LoadError.self) {
            try sandbox.store.install(compressed: compressed,
                                      expectedSHA256: String(repeating: "0", count: 64),
                                      newerThan: 1)
        }
        #expect(try sandbox.store.loadBest().version == 1)
    }

    @Test("битые байты с верной суммой не распаковываются")
    func rejectsCorruptPayload() throws {
        let sandbox = try Sandbox()
        var broken = try Self.deflated(Self.packJSON(version: 2, kcal: 580))
        broken.replaceSubrange(broken.startIndex..<broken.index(broken.startIndex, offsetBy: 8),
                               with: Data(repeating: 0xAB, count: 8))

        #expect(throws: MenuPack.LoadError.self) {
            try sandbox.store.install(compressed: broken,
                                      expectedSHA256: Self.sha256(broken), newerThan: 1)
        }
        #expect(try sandbox.store.loadBest().version == 1)
    }

    @Test("чужой формат пака отвергается целиком")
    func rejectsUnsupportedFormat() throws {
        var json = try JSONSerialization.jsonObject(
            with: Self.packJSON(version: 2, kcal: 580)) as! [String: Any]
        json["format"] = 99
        let data = try JSONSerialization.data(withJSONObject: json)

        #expect(throws: MenuPack.LoadError.self) { try MenuPack.decode(from: data) }
    }

    @Test("пак без позиций отвергается")
    func rejectsEmptyPack() throws {
        var json = try JSONSerialization.jsonObject(
            with: Self.packJSON(version: 2, kcal: 580)) as! [String: Any]
        json["items"] = []
        let data = try JSONSerialization.data(withJSONObject: json)

        #expect(throws: MenuPack.LoadError.self) { try MenuPack.decode(from: data) }
    }

    /// Испорченный файл не должен ронять каждый следующий запуск.
    @Test("повреждённый установленный пак удаляется, работа продолжается на сиде")
    func discardsCorruptInstalledPack() throws {
        let sandbox = try Sandbox()
        try Data("не json".utf8).write(to: sandbox.store.installedURL)

        #expect(try sandbox.store.loadBest().version == 1)
        #expect(!FileManager.default.fileExists(
            atPath: sandbox.store.installedURL.path(percentEncoded: false)))
    }

    @Test("откат на сид по требованию")
    func removeInstalledRevertsToSeed() throws {
        let sandbox = try Sandbox()
        let compressed = try Self.deflated(Self.packJSON(version: 2, kcal: 580))
        _ = try sandbox.store.install(compressed: compressed,
                                      expectedSHA256: Self.sha256(compressed), newerThan: 1)
        #expect(try sandbox.store.loadBest().version == 2)

        sandbox.store.removeInstalled()
        #expect(try sandbox.store.loadBest().version == 1)
    }
}
