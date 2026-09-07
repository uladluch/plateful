import Foundation
import Testing

@testable import plateful

@Suite("Сборка заказа")
struct OrderTests {

    private static func catalog() -> MenuCatalog {
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "Chipotle", "itemCount": 3],
                       ["name": "McDonald's", "itemCount": 1]],
            "items": [
                ["chain": "Chipotle", "key": "chicken", "name": "Chicken",
                 "category": "Toppings & Ingredients",
                 "kcal": 180, "protein": 32, "carbs": 0, "fat": 7],
                ["chain": "Chipotle", "key": "brown-rice", "name": "Brown Rice",
                 "category": "Toppings & Ingredients",
                 "kcal": 210, "protein": 4, "carbs": 36, "fat": 6],
                ["chain": "Chipotle", "key": "guacamole", "name": "Guacamole",
                 "category": "Toppings & Ingredients",
                 "kcal": 230, "protein": 2, "carbs": 8, "fat": 22,
                 "source": "chipotle.com", "observed": "2026-09-07", "stale": false],
                ["chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
                 "kcal": 540, "protein": 25, "carbs": 46, "fat": 28],
            ],
        ]
        let data = try! JSONSerialization.data(withJSONObject: json)
        return MenuCatalog(pack: try! MenuPack.decode(from: data))
    }

    private static func item(_ name: String) -> MenuItem {
        catalog().items.first { $0.name == name }!
    }

    @Test("заказ начинается с одной позиции")
    func startsWithOneItem() {
        let order = Order(startingWith: Self.item("Chicken"))
        #expect(order.chain == "Chipotle")
        #expect(order.lines.count == 1)
        #expect(order.itemCount == 1)
        #expect(order.totals.kcal == 180)
    }

    @Test("итог складывается по всем строкам и количествам")
    func sumsEverything() {
        var order = Order(startingWith: Self.item("Chicken"))
        order.add(Self.item("Brown Rice"))
        order.setQuantity(2, for: Self.item("Chicken").persistentID)

        #expect(order.itemCount == 3)
        #expect(order.totals.kcal == 180 * 2 + 210)
        #expect(order.totals.protein == 32 * 2 + 4)
        #expect(order.totals.carbs == 36)
        #expect(order.totals.fat == 7 * 2 + 6)
    }

    /// «Добавить курицу» — не новая строка, а вторая порция той же.
    @Test("повторное добавление увеличивает количество")
    func addingTwiceBumpsQuantity() {
        var order = Order(startingWith: Self.item("Chicken"))
        order.add(Self.item("Chicken"))

        #expect(order.lines.count == 1)
        #expect(order.lines[0].quantity == 2)
        #expect(order.totals.kcal == 360)
    }

    /// Заказ у кассы — из одного меню; чужая позиция туда попасть не должна.
    @Test("позиция другой сети не добавляется")
    func rejectsForeignChain() {
        var order = Order(startingWith: Self.item("Chicken"))
        order.add(Self.item("Big Mac"))

        #expect(order.lines.count == 1)
        #expect(order.totals.kcal == 180)
    }

    @Test("количество ниже единицы убирает строку")
    func zeroRemovesLine() {
        var order = Order(startingWith: Self.item("Chicken"))
        order.add(Self.item("Brown Rice"))
        order.setQuantity(0, for: Self.item("Chicken").persistentID)

        #expect(order.lines.count == 1)
        #expect(order.lines[0].item.name == "Brown Rice")
    }

    @Test("количество упирается в потолок, а не растёт бесконечно")
    func clampsToUpperBound() {
        var order = Order(startingWith: Self.item("Chicken"))
        order.setQuantity(999, for: Self.item("Chicken").persistentID)

        #expect(order.lines[0].quantity == Order.quantityRange.upperBound)
    }

    @Test("правка несуществующей строки ничего не делает")
    func ignoresUnknownLine() {
        var order = Order(startingWith: Self.item("Chicken"))
        order.setQuantity(5, for: Self.item("Big Mac").persistentID)

        #expect(order.lines.count == 1)
        #expect(order.lines[0].quantity == 1)
    }

    @Test("удаление по строке и свайпом")
    func removesLines() {
        var order = Order(startingWith: Self.item("Chicken"))
        order.add(Self.item("Brown Rice"))
        order.add(Self.item("Guacamole"))

        order.remove(Self.item("Brown Rice").persistentID)
        #expect(order.lines.map(\.item.name) == ["Chicken", "Guacamole"])

        order.remove(atOffsets: IndexSet(integer: 0))
        #expect(order.lines.map(\.item.name) == ["Guacamole"])
    }

    @Test("пустой заказ считается нулём, а не падает")
    func emptyOrderIsZero() {
        var order = Order(startingWith: Self.item("Chicken"))
        order.remove(Self.item("Chicken").persistentID)

        #expect(order.isEmpty)
        #expect(order.itemCount == 0)
        #expect(order.totals == .zero)
        #expect(!order.isStale)
    }

    /// Одна устаревшая цифра делает устаревшим весь итог — иначе подпись
    /// под суммой вводила бы в заблуждение.
    @Test("устаревшая позиция делает устаревшим весь заказ")
    func stalenessPropagates() {
        var fresh = Order(startingWith: Self.item("Guacamole"))
        #expect(!fresh.isStale)

        fresh.add(Self.item("Chicken"))
        #expect(fresh.isStale)
    }

    @Test("арифметика макросов")
    func nutritionArithmetic() {
        let a = Nutrition(kcal: 100, protein: 10, carbs: 20, fat: 5)
        let b = Nutrition(kcal: 50, protein: 5, carbs: 0, fat: 2)

        #expect(a + b == Nutrition(kcal: 150, protein: 15, carbs: 20, fat: 7))
        #expect(a * 3 == Nutrition(kcal: 300, protein: 30, carbs: 60, fat: 15))
        #expect(a * 0 == .zero)
        #expect(Nutrition.zero + a == a)
    }
}
