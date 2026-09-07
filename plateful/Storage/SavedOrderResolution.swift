import Foundation

/// Восстановление сохранённого заказа из текущего каталога.
///
/// Отдельно от модели: сама модель не должна знать про каталог, а каталог —
/// про хранилище.
@MainActor
struct ResolvedOrder {

    /// Строки, которые нашлись в текущем каталоге.
    let order: Order
    /// Названия строк, которых в каталоге больше нет.
    ///
    /// Их не выбрасываем молча: исчезнувшая позиция — это факт про меню сети,
    /// и человеку честнее увидеть «этого больше нет», чем недосчитаться
    /// калорий в итоге.
    let missing: [String]

    var hasMissing: Bool { !missing.isEmpty }

    init(saved: SavedOrder, catalog: MenuCatalog) {
        var lines: [OrderLine] = []
        var missing: [String] = []

        for stored in saved.orderedLines {
            if let item = catalog.items(in: stored.chain).first(where: { $0.key == stored.itemKey }) {
                lines.append(OrderLine(item: item, quantity: stored.quantity))
            } else {
                missing.append(stored.name)
            }
        }

        self.order = Order(chain: saved.chain, lines: lines)
        self.missing = missing
    }
}
