import Foundation
import Testing

@testable import plateful

/// Порядок и состав разделов меню.
///
/// У источника порядка нет вовсе: раньше разделы шли по алфавиту первого
/// блюда, и меню McDonald's открывалось напитками, а соусы стояли выше
/// картошки. Порядок приходит из пака — значит меняется публикацией.
@Suite("Разделы меню")
struct MenuSectionOrderTests {

    private static func catalog(sections: [String]?,
                               rows: [(name: String, section: String)]) -> MenuCatalog {
        var json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": rows.count]],
            "items": rows.map { row in
                [
                    "chain": "McDonald's",
                    "key": row.name.lowercased().replacingOccurrences(of: " ", with: "-"),
                    "name": row.name, "category": row.section, "section": row.section,
                    "kcal": 100, "protein": 1, "carbs": 2, "fat": 3,
                ] as [String: Any]
            },
        ]
        if let sections { json["sections"] = sections }
        return MenuCatalog(
            pack: try! MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
    }

    private static let rows = [
        (name: "Coca Cola", section: "Beverages"),
        (name: "Ketchup", section: "Toppings & Ingredients"),
        (name: "Egg McMuffin", section: "Breakfast"),
        (name: "Big Mac", section: "Burgers"),
    ]

    @Test("порядок разделов берётся из пака, а не из алфавита")
    func followsThePackOrder() {
        let sections = Self.catalog(
            sections: ["Breakfast", "Burgers", "Beverages", "Toppings & Ingredients"],
            rows: Self.rows).sections(for: "McDonald's")

        #expect(sections.map(\.title)
            == ["Breakfast", "Burgers", "Beverages", "Toppings & Ingredients"])
    }

    /// Пак, выпущенный до того, как порядок появился, его не несёт.
    /// Алфавит там был бы хуже: он ставит напитки первыми.
    @Test("пак без объявленного порядка сохраняет порядок появления")
    func fallsBackToFirstAppearance() {
        let sections = Self.catalog(sections: nil, rows: Self.rows)
            .sections(for: "McDonald's")

        #expect(sections.map(\.title)
            == ["Beverages", "Toppings & Ingredients", "Breakfast", "Burgers"])
    }

    @Test("незнакомый раздел уезжает в конец, но не исчезает")
    func unknownSectionGoesLast() {
        let sections = Self.catalog(
            sections: ["Breakfast", "Burgers"],
            rows: Self.rows + [(name: "Mystery", section: "Seasonal")])
            .sections(for: "McDonald's")

        #expect(sections.first?.title == "Breakfast")
        #expect(sections.map(\.title).contains("Seasonal"))
    }

    /// Завтрак — это время дня, а не категория, и в источнике он размазан
    /// по сэндвичам и горячему: у McDonald's из 14 «сэндвичей» 11 завтраки.
    @Test("в паке из бандла завтрак вынесен в свой раздел")
    func realSeedHasBreakfast() throws {
        let url = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"))
        let catalog = MenuCatalog(pack: try MenuPack.decode(from: Data(contentsOf: url)))
        let sections = catalog.sections(for: "McDonald's")
        let breakfast = try #require(sections.first { $0.title == "Breakfast" })
        let names = breakfast.items.map(\.name)

        #expect(sections.first?.title == "Breakfast")
        #expect(names.contains("Egg McMuffin"))
        #expect(names.contains("Hash Browns"))
        // Рыба и курица завтраком не стали.
        #expect(!names.contains("Filet O Fish"))
        #expect(!names.contains("McChicken"))
        // Напитки остались напитками.
        #expect(sections.last { !$0.isArchive }?.title == "Toppings & Ingredients")
    }
}
