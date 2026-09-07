import Foundation
import Testing

@testable import plateful

@Suite("Сравнение блюд")
struct ComparisonTests {

    private static func catalog() -> MenuCatalog {
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": 2],
                       ["name": "Chick-Fil-A", "itemCount": 2]],
            "items": [
                ["chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
                 "kcal": 540, "protein": 25, "carbs": 46, "fat": 28],
                ["chain": "McDonald's", "key": "twin", "name": "Twin",
                 "kcal": 540, "protein": 25, "carbs": 46, "fat": 28],
                ["chain": "Chick-Fil-A", "key": "chicken-sandwich", "name": "Chicken Sandwich",
                 "kcal": 440, "protein": 28, "carbs": 40, "fat": 19],
                ["chain": "Chick-Fil-A", "key": "verified", "name": "Verified Wrap",
                 "kcal": 350, "protein": 30, "carbs": 30, "fat": 12,
                 "source": "chick-fil-a.com", "observed": "2026-09-07", "stale": false],
            ],
        ]
        return MenuCatalog(
            pack: try! MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
    }

    private static func item(_ name: String) -> MenuItem {
        catalog().items.first { $0.name == name }!
    }

    private static var bigMacVsSandwich: Comparison {
        Comparison(left: item("Big Mac"), right: item("Chicken Sandwich"))
    }

    @Test("строки идут в фиксированном порядке")
    func rowsAreOrdered() {
        #expect(Self.bigMacVsSandwich.rows.map(\.nutrient)
            == [.calories, .protein, .carbs, .fat])
    }

    @Test("разница считается как правое минус левое")
    func differenceIsRightMinusLeft() {
        let rows = Self.bigMacVsSandwich.rows
        #expect(rows[0].difference == -100)   // 440 − 540
        #expect(rows[1].difference == 3)      // 28 − 25
        #expect(rows[2].difference == -6)
        #expect(rows[3].difference == -9)
        #expect(Self.bigMacVsSandwich.hasDifferences)
    }

    /// Без знака непонятно, в какую сторону отличается правое блюдо.
    @Test("разница показывается со знаком, калории без единиц")
    func formatsDifferenceWithSign() throws {
        let rows = Self.bigMacVsSandwich.rows
        let calories = try #require(rows[0].differenceText)
        let protein = try #require(rows[1].differenceText)

        #expect(calories.contains("100"))
        #expect(calories.contains("-") || calories.contains("−"))
        #expect(!calories.contains("g"))
        #expect(protein.contains("+"))
        #expect(protein.hasSuffix("g"))
    }

    @Test("совпавшие значения не показывают разницу")
    func equalValuesHaveNoDifference() {
        let same = Comparison(left: Self.item("Big Mac"), right: Self.item("Twin"))
        let allEqual = same.rows.allSatisfy(\.isEqual)
        let noDifferenceShown = same.rows.allSatisfy { $0.differenceText == nil }

        #expect(allEqual)
        #expect(noDifferenceShown)
        #expect(!same.hasDifferences)
    }

    @Test("значения форматируются по типу нутриента")
    func formatsValues() {
        let rows = Self.bigMacVsSandwich.rows
        #expect(rows[0].leftText == "540")
        #expect(rows[1].leftText.contains("25"))
        #expect(rows[1].leftText.contains("g"))
    }

    /// Победителя не объявляем: «лучше» зависит от того, что человеку нужно.
    /// Единственное, что мы вправе сказать, — подходит ли блюдо под его
    /// собственную цель.
    @Test("без целей соответствие не считается")
    func noGoalsNoVerdict() {
        #expect(Self.bigMacVsSandwich.meetsGoals(.none) == nil)
        #expect(Self.bigMacVsSandwich.meetsGoals(MenuFilter(sort: .mostProtein)) == nil,
                "сортировка — не цель, вердикта из неё не следует")
    }

    @Test("с целями считается соответствие каждого блюда")
    func evaluatesAgainstGoals() throws {
        let fit = try #require(
            Self.bigMacVsSandwich.meetsGoals(MenuFilter(maxCalories: 500, minProtein: 26)))
        #expect(fit.left == false)   // Big Mac: 540 ккал и 25 г белка
        #expect(fit.right == true)   // Chicken Sandwich: 440 и 28
    }

    /// Ставить свежую цифру рядом со старой молча — вводить в заблуждение.
    @Test("устаревшая цифра с любой стороны помечает сравнение")
    func flagsStaleFigures() {
        let mixed = Comparison(left: Self.item("Verified Wrap"), right: Self.item("Big Mac"))
        #expect(mixed.isStale)

        let bothFresh = Comparison(left: Self.item("Verified Wrap"),
                                   right: Self.item("Verified Wrap"))
        #expect(!bothFresh.isStale)
    }

    @Test("сравниваются блюда разных сетей")
    func comparesAcrossChains() {
        let comparison = Self.bigMacVsSandwich
        #expect(comparison.left.chain != comparison.right.chain)
        #expect(comparison.rows.count == 4)
    }
}
