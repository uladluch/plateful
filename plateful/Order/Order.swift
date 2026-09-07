import Foundation

// Проект собран с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor; заказ — значение.

/// Строка заказа: позиция и сколько её взяли.
nonisolated struct OrderLine: Identifiable, Hashable, Sendable {
    var id: MenuItem.PersistentID { item.persistentID }
    let item: MenuItem
    var quantity: Int
}

/// Заказ, который человек собирает у кассы.
///
/// **Только сложение, никакого вычитания.** «Добавить курицу» и «двойное мясо»
/// считаются точно — это опубликованные сетью цифры отдельных позиций.
/// А «убрать соус из Биг Мака» посчитать честно нельзя: рецептуры позиции у
/// нас нет, и любое вычитание было бы выдуманным числом. Приложение обещает
/// честность про данные, поэтому такой функции нет.
///
/// Там, где сеть публикует ингредиенты отдельно — Chipotle, Subway, — сложения
/// достаточно: заказ собирается с нуля, и «без риса» это просто не добавить рис.
nonisolated struct Order: Hashable, Sendable {

    /// Сколько одной позиции можно взять. Верхняя граница — защита от
    /// случайного зажатого степпера, а не ограничение аппетита.
    static let quantityRange = 1...20

    /// Заказ всегда в пределах одной сети: у кассы выбирают из одного меню.
    let chain: String
    private(set) var lines: [OrderLine]

    init(chain: String, lines: [OrderLine] = []) {
        self.chain = chain
        self.lines = lines
    }

    init(startingWith item: MenuItem) {
        self.chain = item.chain
        self.lines = [OrderLine(item: item, quantity: 1)]
    }

    var isEmpty: Bool { lines.isEmpty }

    /// Сколько позиций в заказе с учётом количества.
    var itemCount: Int { lines.reduce(0) { $0 + $1.quantity } }

    var totals: Nutrition {
        lines.reduce(.zero) { $0 + $1.item.nutrition * $1.quantity }
    }

    /// Заказ настолько же свеж, насколько самая старая цифра в нём.
    /// Одна устаревшая позиция делает устаревшим весь итог — иначе подпись
    /// вводила бы в заблуждение.
    var isStale: Bool { lines.contains { $0.item.isStale } }

    // MARK: - Правки

    /// Добавляет позицию; если она уже есть — увеличивает количество.
    mutating func add(_ item: MenuItem) {
        guard item.chain == chain else { return }
        if let index = lines.firstIndex(where: { $0.id == item.persistentID }) {
            setQuantity(lines[index].quantity + 1, for: item.persistentID)
        } else {
            lines.append(OrderLine(item: item, quantity: 1))
        }
    }

    /// Количество вне допустимого — не ошибка ввода, а край степпера:
    /// ноль и меньше убирают строку, слишком много упирается в потолок.
    mutating func setQuantity(_ quantity: Int, for id: MenuItem.PersistentID) {
        guard let index = lines.firstIndex(where: { $0.id == id }) else { return }
        if quantity < Self.quantityRange.lowerBound {
            lines.remove(at: index)
        } else {
            lines[index].quantity = min(quantity, Self.quantityRange.upperBound)
        }
    }

    mutating func remove(_ id: MenuItem.PersistentID) {
        lines.removeAll { $0.id == id }
    }

    /// Свайп-удаление из списка. Реализовано вручную, а не через
    /// `Array.remove(atOffsets:)`: тот метод приходит из SwiftUI, а модель
    /// заказа не должна зависеть от слоя интерфейса.
    mutating func remove(atOffsets offsets: IndexSet) {
        lines = lines.enumerated()
            .filter { !offsets.contains($0.offset) }
            .map(\.element)
    }
}
