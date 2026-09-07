import Foundation
import Testing

@testable import plateful

@Suite("Фильтры и сортировка меню")
struct MenuFilterTests {

    private static func catalog() -> MenuCatalog {
        let rows: [(String, String, Double, Double)] = [
            ("Burgers", "Big Mac", 540, 25),
            ("Burgers", "Hamburger", 250, 13),
            ("Burgers", "Double Quarter Pounder", 770, 51),
            ("Salads", "Side Salad", 20, 1),
            ("Drinks", "Diet Coke", 0, 0),
        ]
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": rows.count]],
            "items": rows.map { category, name, kcal, protein in
                ["chain": "McDonald's",
                 "key": name.lowercased().replacingOccurrences(of: " ", with: "-"),
                 "name": name, "category": category,
                 "kcal": kcal, "protein": protein, "carbs": 1, "fat": 1] as [String: Any]
            },
        ]
        return MenuCatalog(
            pack: try! MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
    }

    private static var items: [MenuItem] { catalog().items }
    private static var sections: [MenuSection] { catalog().sections(for: "McDonald's") }

    /// Тот, кто не ставил целей, должен видеть всё меню целиком.
    @Test("пустой фильтр ничего не отсекает и не переставляет")
    func emptyFilterIsTransparent() {
        let filter = MenuFilter.none
        #expect(!filter.isActive)
        #expect(!filter.isNarrowing)
        #expect(filter.apply(to: Self.items).map(\.name) == Self.items.map(\.name))
        #expect(filter.apply(to: Self.sections).count == Self.sections.count)
    }

    @Test("потолок калорий отсекает всё, что выше")
    func filtersByCalorieCeiling() {
        let result = MenuFilter(maxCalories: 300).apply(to: Self.items)
        #expect(Set(result.map(\.name)) == ["Hamburger", "Side Salad", "Diet Coke"])
    }

    @Test("минимум белка отсекает всё, что ниже")
    func filtersByProteinFloor() {
        let result = MenuFilter(minProtein: 25).apply(to: Self.items)
        #expect(Set(result.map(\.name)) == ["Big Mac", "Double Quarter Pounder"])
    }

    @Test("границы включительные")
    func boundsAreInclusive() {
        #expect(MenuFilter(maxCalories: 540).matches(Self.items.first { $0.name == "Big Mac" }!))
        #expect(MenuFilter(minProtein: 25).matches(Self.items.first { $0.name == "Big Mac" }!))
    }

    @Test("две цели работают вместе")
    func combinesGoals() {
        let result = MenuFilter(maxCalories: 600, minProtein: 20).apply(to: Self.items)
        #expect(result.map(\.name) == ["Big Mac"])
    }

    @Test("ничего не подошло — пустая выдача, а не падение")
    func toughGoalsYieldNothing() {
        #expect(MenuFilter(maxCalories: 10, minProtein: 90).apply(to: Self.items).isEmpty)
        #expect(MenuFilter(maxCalories: 10, minProtein: 90).apply(to: Self.sections).isEmpty)
    }

    @Test("сортировка по калориям и белку")
    func sorts() {
        let byCalories = MenuFilter(sort: .fewestCalories).apply(to: Self.items)
        #expect(byCalories.first?.name == "Diet Coke")
        #expect(byCalories.last?.name == "Double Quarter Pounder")

        let byProtein = MenuFilter(sort: .mostProtein).apply(to: Self.items)
        #expect(byProtein.first?.name == "Double Quarter Pounder")
        #expect(byProtein.last?.name == "Diet Coke")
    }

    /// Сортировка ничего не прячет — она только переставляет.
    @Test("сортировка не отсекает позиции")
    func sortKeepsEverything() {
        let sorted = MenuFilter(sort: .mostProtein)
        #expect(sorted.isActive)
        #expect(!sorted.isNarrowing)
        #expect(sorted.apply(to: Self.items).count == Self.items.count)
    }

    /// «Самое белковое в сети», а не «самое белковое в каждой категории»:
    /// при сортировке деление на разделы теряет смысл.
    @Test("сортировка схлопывает разделы в один список")
    func sortFlattensSections() {
        let result = MenuFilter(sort: .mostProtein).apply(to: Self.sections)
        #expect(result.count == 1)
        #expect(result.first?.title == MenuSort.mostProtein.title)
        #expect(result.first?.items.first?.name == "Double Quarter Pounder")
    }

    @Test("опустевшие разделы исчезают, остальные сохраняют порядок")
    func dropsEmptySections() {
        let result = MenuFilter(maxCalories: 300).apply(to: Self.sections)
        #expect(result.map(\.title) == ["Burgers", "Salads", "Drinks"])
        #expect(result.first?.items.map(\.name) == ["Hamburger"])
    }
}
