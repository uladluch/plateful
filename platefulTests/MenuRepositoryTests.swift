import Foundation
import Testing

@testable import plateful

@Suite("Репозиторий")
@MainActor
struct MenuRepositoryTests {

    /// Настоящий сид из бандла приложения — заодно проверка, что конвейер
    /// действительно положил файл туда, откуда его ждёт PackStore.
    @Test("сид из бандла грузится и содержит ключевые сети")
    func loadsBundledSeed() async throws {
        let seedURL = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"),
            "seed-pack.json нет в бандле — проверьте build_seed.py")

        let directory = FileManager.default.temporaryDirectory
            .appending(path: "repo-\(UUID().uuidString)", directoryHint: .isDirectory)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }

        let repository = MenuRepository(store: PackStore(
            seedURL: seedURL,
            installedURL: directory.appending(path: "current.json", directoryHint: .notDirectory)))

        await repository.load()

        let catalog = try #require(repository.catalog, "каталог не загрузился")
        #expect(catalog.items.count > 20_000)
        #expect(catalog.chains.count == 96)

        for chain in ["McDonald's", "Chick-Fil-A", "Starbucks", "Subway",
                      "Chipotle", "Panera Bread", "Taco Bell", "Wendy's"] {
            #expect(!repository.items(in: chain).isEmpty, "нет позиций у \(chain)")
        }
    }

    @Test("поиск через репозиторий находит ожидаемое")
    func searchThroughRepository() async throws {
        let repository = try await loadedRepository()
        #expect(repository.search("big mac").first?.name == "Big Mac")
        #expect(repository.search("mcdonalds big mac").first?.chain == "McDonald's")
        #expect(repository.search("baconator").first?.chain == "Wendy's")
    }

    @Test("позиция достаётся по устойчивой ссылке")
    func resolvesPersistentID() async throws {
        let repository = try await loadedRepository()
        let bigMac = try #require(repository.search("big mac", in: "McDonald's").first)
        let resolved = repository.item(bigMac.persistentID)
        #expect(resolved?.name == bigMac.name)
        #expect(resolved?.kcal == bigMac.kcal)
    }

    @Test("до загрузки репозиторий отвечает пусто, а не падает")
    func emptyBeforeLoad() {
        let repository = MenuRepository(store: PackStore(
            seedURL: nil,
            installedURL: FileManager.default.temporaryDirectory
                .appending(path: "none.json", directoryHint: .notDirectory)))
        #expect(repository.catalog == nil)
        #expect(repository.chains.isEmpty)
        #expect(repository.search("big mac").isEmpty)
        #expect(repository.items(in: "McDonald's").isEmpty)
    }

    @Test("отсутствие паков переводит репозиторий в состояние ошибки")
    func reportsFailure() async {
        let repository = MenuRepository(store: PackStore(
            seedURL: nil,
            installedURL: FileManager.default.temporaryDirectory
                .appending(path: "missing-\(UUID().uuidString).json", directoryHint: .notDirectory)))
        await repository.load()

        guard case .failed = repository.state else {
            Issue.record("ожидалось .failed, получено \(repository.state)")
            return
        }
    }

    private func loadedRepository() async throws -> MenuRepository {
        let seedURL = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"))
        let directory = FileManager.default.temporaryDirectory
            .appending(path: "repo-\(UUID().uuidString)", directoryHint: .isDirectory)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)

        let repository = MenuRepository(store: PackStore(
            seedURL: seedURL,
            installedURL: directory.appending(path: "current.json", directoryHint: .notDirectory)))
        await repository.load()
        return repository
    }
}
