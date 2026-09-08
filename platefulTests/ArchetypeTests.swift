import Foundation
import Testing

@testable import plateful

@Suite("Архетипы блюд")
struct ArchetypeTests {

    /// Архетип приходит из пака, а не считается на клиенте: неверно
    /// назначенная картинка должна чиниться публикацией пака, без релиза.
    @Test("архетип доезжает из пака в модель")
    func carriesArchetype() throws {
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": 1]],
            "items": [["chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
                       "kcal": 540, "protein": 25, "carbs": 46, "fat": 28,
                       "image": "cheeseburger"]],
        ]
        let catalog = MenuCatalog(
            pack: try MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
        #expect(catalog.items.first?.image == "cheeseburger")
    }

    /// Паки, выпущенные до появления картинок, обязаны читаться.
    @Test("пак без архетипов читается")
    func toleratesMissingArchetype() throws {
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": 1]],
            "items": [["chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
                       "kcal": 540, "protein": 25, "carbs": 46, "fat": 28]],
        ]
        let catalog = MenuCatalog(
            pack: try MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
        #expect(catalog.items.first?.image == nil)
    }

    /// Сид в бандле должен нести архетип у каждой позиции — иначе часть
    /// каталога останется без картинок молча.
    @Test("у всех позиций сида есть архетип")
    func seedIsFullyClassified() throws {
        let url = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"))
        let pack = try MenuPack.decode(from: Data(contentsOf: url))

        let missing = pack.items.filter { $0.image == nil || $0.image?.isEmpty == true }
        #expect(missing.isEmpty, "без архетипа: \(missing.count) позиций")

        let archetypes = Set(pack.items.compactMap(\.image))
        #expect(archetypes.count > 30, "архетипов подозрительно мало: \(archetypes.count)")
    }
}
