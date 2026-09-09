import Foundation
import Testing

@testable import plateful

@Suite("Репозиторий")
@MainActor
struct MenuRepositoryTests {

    /// Настоящий сид из бандла приложения — заодно проверка, что конвейер
    /// действительно положил файл туда, откуда его ждёт PackStore.
    ///
    /// В бандле лежит **опубликованный** пак, а не весь каталог: сеть едет
    /// в приложение целиком или не едет вовсе, и отбор делает
    /// `export_pack.py`. Поэтому сетей здесь единицы, а не девяносто шесть,
    /// и проверять надо не их число, а что каждая пришла не пустой.
    @Test("сид из бандла грузится и каждая его сеть непуста")
    func loadsBundledSeed() async throws {
        let seedURL = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"),
            "seed-pack.json нет в бандле — кладёт его publish_pack.sh")

        let directory = FileManager.default.temporaryDirectory
            .appending(path: "repo-\(UUID().uuidString)", directoryHint: .isDirectory)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }

        let repository = MenuRepository(store: PackStore(
            seedURL: seedURL,
            installedURL: directory.appending(path: "current.json", directoryHint: .notDirectory)))

        await repository.load()

        let catalog = try #require(repository.catalog, "каталог не загрузился")
        #expect(catalog.items.count > 1_000)
        #expect(!catalog.chains.isEmpty)

        // Сеть, объявленная в паке, обязана иметь позиции: пустая строка в
        // списке — это дыра в отборе, а не «сеть без блюд».
        for chain in catalog.chains {
            #expect(!repository.items(in: chain.name).isEmpty,
                    "нет позиций у \(chain.name)")
        }
        #expect(repository.items(in: "McDonald's").count > 100)
    }

    @Test("поиск через репозиторий находит ожидаемое")
    func searchThroughRepository() async throws {
        let repository = try await loadedRepository()
        #expect(repository.search("big mac").first?.name == "Big Mac")
        #expect(repository.search("mcdonalds big mac").first?.chain == "McDonald's")
        #expect(repository.search("whopper").first?.chain == "Burger King")
    }

    @Test("позиция достаётся по устойчивой ссылке")
    func resolvesPersistentID() async throws {
        let repository = try await loadedRepository()
        let bigMac = try #require(repository.search("big mac", in: "McDonald's").first)
        let resolved = repository.item(bigMac.persistentID)
        #expect(resolved?.name == bigMac.name)
        #expect(resolved?.kcal == bigMac.kcal)
    }

    /// `.task` может сработать не один раз за жизнь окна, а разбор пака стоит
    /// четверть секунды. Повторный вызов должен быть бесплатным.
    @Test("повторная загрузка не пересобирает каталог")
    func reloadIsIdempotent() async throws {
        let repository = try await loadedRepository()
        let first = try #require(repository.catalog)

        await repository.load()
        let second = try #require(repository.catalog)
        #expect(first.items.count == second.items.count)

        guard case .ready = repository.state else {
            Issue.record("состояние должно остаться .ready, а не уйти в .loading")
            return
        }
    }

    /// В симуляторе `.task` запускал загрузку шесть раз подряд, и поздно
    /// завершившийся разбор старого пака затирал уже загруженный новый.
    /// Параллельные вызовы обязаны схлопываться в один.
    @Test("параллельные загрузки схлопываются и не затирают результат")
    func concurrentLoadsCoalesce() async throws {
        let seedURL = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"))
        let directory = FileManager.default.temporaryDirectory
            .appending(path: "race-\(UUID().uuidString)", directoryHint: .isDirectory)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }

        let repository = MenuRepository(store: PackStore(
            seedURL: seedURL,
            installedURL: directory.appending(path: "current.json", directoryHint: .notDirectory)))

        // Все вызовы на главном акторе, как и в приложении: гонка возникает
        // не от параллелизма, а от повторного входа на точках await.
        let attempts = (0..<6).map { _ in
            Task { @MainActor in await repository.load() }
        }
        for attempt in attempts { await attempt.value }

        let catalog = try #require(repository.catalog)
        #expect(catalog.items.count > 1_000)
        guard case .ready = repository.state else {
            Issue.record("после гонки состояние должно быть .ready, а не \(repository.state)")
            return
        }
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
