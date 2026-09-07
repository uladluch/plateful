import Foundation
import SwiftData

// Модели спроектированы под ограничения CloudKit с самого начала:
//   • у каждого свойства есть значение по умолчанию,
//   • нет @Attribute(.unique) — CloudKit его не поддерживает,
//   • связи необязательные и с обратной ссылкой.
// `ModelConfiguration` по умолчанию идёт с `cloudKitDatabase: .automatic`,
// поэтому синхронизация включится сама, как только у таргета появится
// entitlement iCloud. Переписывать модели не придётся.

/// Позиция, которую человек открывал. История бесплатна и живёт локально.
@Model
final class ViewedItem {
    var chain: String = ""
    var itemKey: String = ""
    /// Снимок названия: если позиция исчезнет из меню, показать всё равно есть что.
    var name: String = ""
    var viewedAt: Date = Date.distantPast

    init(chain: String = "", itemKey: String = "", name: String = "", viewedAt: Date = .now) {
        self.chain = chain
        self.itemKey = itemKey
        self.name = name
        self.viewedAt = viewedAt
    }

    var reference: MenuItem.PersistentID {
        MenuItem.PersistentID(chain: chain, key: itemKey)
    }
}

/// Сохранённый заказ — «моё обычное» у конкретной сети.
@Model
final class SavedOrder {
    var id: UUID = UUID()
    var chain: String = ""
    var title: String = ""
    var createdAt: Date = Date.distantPast

    @Relationship(deleteRule: .cascade, inverse: \SavedOrderLine.order)
    var lines: [SavedOrderLine]? = []

    init(id: UUID = UUID(), chain: String = "", title: String = "", createdAt: Date = .now) {
        self.id = id
        self.chain = chain
        self.title = title
        self.createdAt = createdAt
    }

    /// Строки в том порядке, в каком их добавляли: CloudKit не хранит порядок
    /// связи, поэтому сортируем сами.
    var orderedLines: [SavedOrderLine] {
        (lines ?? []).sorted { $0.position < $1.position }
    }
}

/// Строка сохранённого заказа.
///
/// Макросы здесь **не хранятся**. Заказ ссылается на позицию, а цифры берутся
/// из текущего каталога: когда Big Mac переедет с 540 на 580, сохранённый
/// заказ покажет новое число, а не законсервированное старое. Снимок имени
/// нужен только чтобы было что показать, если позиция исчезнет из меню.
@Model
final class SavedOrderLine {
    var chain: String = ""
    var itemKey: String = ""
    var name: String = ""
    var quantity: Int = 1
    var position: Int = 0
    var order: SavedOrder?

    init(chain: String = "", itemKey: String = "", name: String = "",
         quantity: Int = 1, position: Int = 0) {
        self.chain = chain
        self.itemKey = itemKey
        self.name = name
        self.quantity = quantity
        self.position = position
    }

    var reference: MenuItem.PersistentID {
        MenuItem.PersistentID(chain: chain, key: itemKey)
    }
}
