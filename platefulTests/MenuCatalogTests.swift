import Foundation
import Testing

@testable import plateful

@Suite("Каталог и поиск")
struct MenuCatalogTests {

    /// Маленький каталог: тесты про поведение поиска, а не про содержимое сида.
    private static func makeCatalog(
        version: Int = 1,
        stale: Bool = true,
        items: [MenuPack.Item]
    ) -> MenuCatalog {
        let chains = Dictionary(grouping: items, by: \.chain)
            .map { MenuPack.Chain(name: $0.key, itemCount: $0.value.count) }
            .sorted { $0.name < $1.name }
        let json: [String: Any] = [
            "format": 1, "version": version,
            "source": "test", "observed": "2026-01-01", "stale": stale,
            "chains": chains.map { ["name": $0.name, "itemCount": $0.itemCount] },
            "items": items.map { item -> [String: Any] in
                var row: [String: Any] = [
                    "chain": item.chain, "key": item.key, "name": item.name,
                    "kcal": item.kcal, "protein": item.protein,
                    "carbs": item.carbs, "fat": item.fat,
                ]
                if let category = item.category { row["category"] = category }
                if let serving = item.serving { row["serving"] = serving }
                if let source = item.source { row["source"] = source }
                if let observed = item.observed { row["observed"] = observed }
                if let itemStale = item.stale { row["stale"] = itemStale }
                return row
            },
        ]
        let data = try! JSONSerialization.data(withJSONObject: json)
        return MenuCatalog(pack: try! MenuPack.decode(from: data))
    }

    private static func item(
        _ chain: String, _ name: String,
        kcal: Double = 100, source: String? = nil,
        observed: String? = nil, stale: Bool? = nil
    ) -> MenuPack.Item {
        MenuPack.Item(
            chain: chain,
            key: name.lowercased().replacingOccurrences(of: " ", with: "-"),
            name: name, category: nil, serving: nil,
            kcal: kcal, protein: 1, carbs: 2, fat: 3, image: nil, photo: nil, offMenu: nil,
            source: source, observed: observed, stale: stale)
    }

    private static let sample = makeCatalog(items: [
        item("McDonald's", "Big Mac", kcal: 540),
        item("McDonald's", "Big Mac Sauce", kcal: 90),
        item("McDonald's", "Quarter Pounder w/ Cheese", kcal: 530),
        item("Frisch's Big Boy", "Macaroni Salad", kcal: 300),
        item("Wendy's", "Baconator", kcal: 940),
    ])

    @Test("точное название поднимается выше похожих")
    func exactNameWins() {
        let results = Self.sample.search("big mac")
        #expect(results.first?.name == "Big Mac")
        #expect(results.contains { $0.name == "Big Mac Sauce" })
    }

    /// Ради этого поиск идёт и по названию сети: «mcdonalds big mac».
    @Test("сеть и блюдо в одном запросе")
    func matchesChainAndName() {
        #expect(Self.sample.search("mcdonalds big mac").first?.name == "Big Mac")
        #expect(Self.sample.search("mcdonald's big mac").first?.name == "Big Mac")
        #expect(Self.sample.search("wendys baconator").first?.name == "Baconator")
    }

    @Test("каждое слово запроса обязано найтись")
    func requiresEveryToken() {
        #expect(Self.sample.search("big mac zzz").isEmpty)
        #expect(Self.sample.search("baconator mcdonalds").isEmpty)
    }

    @Test("название блюда весит больше названия сети")
    func nameOutweighsChain() {
        // «big» есть и в блюде McDonald's, и в названии сети Frisch's Big Boy.
        let results = Self.sample.search("big")
        #expect(results.first?.chain == "McDonald's")
    }

    @Test("поиск внутри сети не выходит за её пределы")
    func scopedSearchStaysInChain() {
        let results = Self.sample.search("mac", in: "McDonald's")
        #expect(results.allSatisfy { $0.chain == "McDonald's" })
        #expect(!results.contains { $0.name == "Macaroni Salad" })
    }

    @Test("пустой и бессмысленный запрос ничего не ломают")
    func emptyAndGarbage() {
        #expect(Self.sample.search("").isEmpty)
        #expect(Self.sample.search("   ").isEmpty)
        #expect(Self.sample.search("zzzqqq").isEmpty)
        #expect(Self.sample.items(in: "Нет такой сети").isEmpty)
    }

    @Test("предел выдачи соблюдается")
    func respectsLimit() {
        #expect(Self.sample.search("a", limit: 2).count <= 2)
    }

    @Test("позиции сети отдаются целиком")
    func listsChainItems() {
        #expect(Self.sample.items(in: "McDonald's").count == 3)
        #expect(Self.sample.chains.first { $0.name == "McDonald's" }?.itemCount == 3)
    }

    /// Обещание «показывать дату и источник» держится на этом: у позиции
    /// свои значения только там, где была ручная правка.
    @Test("происхождение наследуется от пака, кроме правленых позиций")
    func provenanceFallsBackToPack() {
        let catalog = Self.makeCatalog(stale: true, items: [
            Self.item("McDonald's", "Big Mac", kcal: 580,
                      source: "mcdonalds.com", observed: "2026-09-07", stale: false),
            Self.item("McDonald's", "McDouble", kcal: 380),
        ])
        let bigMac = catalog.search("big mac", in: "McDonald's").first
        #expect(bigMac?.source == "mcdonalds.com")
        #expect(bigMac?.observed == "2026-09-07")
        #expect(bigMac?.isStale == false)

        let mcDouble = catalog.search("mcdouble", in: "McDonald's").first
        #expect(mcDouble?.source == "test")
        #expect(mcDouble?.isStale == true)
    }

    @Test("ссылка на позицию переживает обновление пака")
    func persistentIDIsStable() {
        let first = Self.sample.search("baconator").first!
        let reloaded = Self.makeCatalog(version: 2, items: [
            Self.item("Wendy's", "Baconator", kcal: 950)
        ])
        let again = reloaded.items(in: "Wendy's").first { $0.key == first.persistentID.key }
        #expect(again != nil)
        #expect(again?.kcal == 950)
    }
}
