import Foundation
import Testing

@testable import plateful

@Suite("Архив снятых блюд")
struct ArchiveTests {

    private static func catalog() -> MenuCatalog {
        let rows: [(String, String, Bool)] = [
            ("Burgers", "Big Mac", false),
            ("Burgers", "Artisan Grilled Chicken Sandwich", true),
            ("Burgers", "McDouble", false),
            ("Salads", "Bacon Ranch Salad", true),
        ]
        let json: [String: Any] = [
            "format": 1, "version": 9,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": rows.count]],
            "items": rows.map { category, name, off -> [String: Any] in
                var row: [String: Any] = [
                    "chain": "McDonald's",
                    "key": name.lowercased().replacingOccurrences(of: " ", with: "-"),
                    "name": name, "category": category,
                    "kcal": 500, "protein": 20, "carbs": 40, "fat": 25,
                ]
                if off { row["offMenu"] = true }
                return row
            },
        ]
        return MenuCatalog(
            pack: try! MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
    }

    /// Держать снятые вперемешку с текущими — вводить в заблуждение:
    /// человек стоит у кассы и заказать их не может.
    @Test("снятые собираются в отдельный раздел в конце")
    func archiveSectionIsLast() {
        let sections = Self.catalog().sections(for: "McDonald's")

        #expect(sections.last?.title == "Archive")
        #expect(sections.last?.isArchive == true)
        #expect(sections.last?.items.count == 2)
        #expect(sections.dropLast().allSatisfy { section in
            section.items.allSatisfy { !$0.isOffMenu }
        })
    }

    @Test("в обычных разделах остаются только живые блюда")
    func categoriesKeepOnlyLive() {
        let sections = Self.catalog().sections(for: "McDonald's")
        let burgers = sections.first { $0.title == "Burgers" }

        #expect(burgers?.items.map(\.name) == ["Big Mac", "McDouble"])
        #expect(sections.contains { $0.title == "Salads" } == false,
                "раздел, где остались одни снятые блюда, пустым висеть не должен")
    }

    /// Не прячем: человек мог сохранить блюдо в заказ или прийти по истории,
    /// и его исчезновение выглядело бы как поломка.
    @Test("снятые находятся поиском, но идут после живых")
    func archivedRankLast() {
        let results = Self.catalog().search("chicken sandwich")
        #expect(!results.isEmpty)

        let archivedFirst = results.firstIndex { $0.isOffMenu }
        let liveLast = results.lastIndex { !$0.isOffMenu }
        if let archivedFirst, let liveLast {
            #expect(archivedFirst > liveLast, "снятое блюдо всплыло выше живого")
        }
    }

    @Test("снятые остаются доступны по прямому обращению")
    func archivedStayReachable() {
        let catalog = Self.catalog()
        let all = catalog.items(in: "McDonald's")
        #expect(all.count == 4)
        #expect(all.contains { $0.name == "Bacon Ranch Salad" })
    }
}
