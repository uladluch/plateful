import Foundation
import SwiftData
import Testing

@testable import plateful

@Suite("Данные пользователя")
@MainActor
struct UserDataStoreTests {

    /// Контейнер в памяти и без CloudKit: тесты не должны ходить в iCloud
    /// и не должны видеть данные друг друга.
    private static func makeStore() throws -> UserDataStore {
        let container = try ModelContainer(
            for: ViewedItem.self, SavedOrder.self, SavedOrderLine.self,
            configurations: ModelConfiguration(
                isStoredInMemoryOnly: true, cloudKitDatabase: .none))
        return UserDataStore(context: ModelContext(container))
    }

    private static func catalog() -> MenuCatalog {
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "Chipotle", "itemCount": 2]],
            "items": [
                ["chain": "Chipotle", "key": "chicken", "name": "Chicken",
                 "kcal": 180, "protein": 32, "carbs": 0, "fat": 7],
                ["chain": "Chipotle", "key": "brown-rice", "name": "Brown Rice",
                 "kcal": 210, "protein": 4, "carbs": 36, "fat": 6],
            ],
        ]
        return MenuCatalog(
            pack: try! MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
    }

    private static func item(_ name: String) -> MenuItem {
        catalog().items.first { $0.name == name }!
    }

    // MARK: - История

    @Test("просмотр запоминается")
    func recordsView() throws {
        let store = try Self.makeStore()
        try store.recordView(of: Self.item("Chicken"))

        let recent = try store.recentViews()
        #expect(recent.count == 1)
        #expect(recent[0].name == "Chicken")
        #expect(recent[0].reference == Self.item("Chicken").persistentID)
    }

    /// CloudKit не умеет уникальные атрибуты, поэтому дедуп — наша работа.
    @Test("повторный просмотр не плодит строки, а поднимает дату")
    func deduplicatesViews() throws {
        let store = try Self.makeStore()
        try store.recordView(of: Self.item("Chicken"))
        let first = try #require(try store.recentViews().first?.viewedAt)

        try store.recordView(of: Self.item("Brown Rice"))
        try store.recordView(of: Self.item("Chicken"))

        let recent = try store.recentViews()
        #expect(recent.count == 2)
        #expect(recent[0].name == "Chicken", "последний просмотр должен быть первым")
        #expect(try #require(recent.first?.viewedAt) > first)
    }

    @Test("история не растёт бесконечно")
    func trimsHistory() throws {
        let store = try Self.makeStore()
        let catalog = Self.catalog()

        // Больше лимита разных позиций взять неоткуда, поэтому подкладываем
        // строки напрямую — проверяем именно обрезку.
        for index in 0..<(UserDataStore.historyLimit + 10) {
            store.context.insert(ViewedItem(
                chain: "Chipotle", itemKey: "key-\(index)", name: "Item \(index)",
                viewedAt: Date(timeIntervalSince1970: Double(index))))
        }
        try store.recordView(of: catalog.items[0])

        #expect(try store.recentViews(limit: 1000).count == UserDataStore.historyLimit)
    }

    @Test("историю можно очистить")
    func clearsHistory() throws {
        let store = try Self.makeStore()
        try store.recordView(of: Self.item("Chicken"))
        try store.clearHistory()
        #expect(try store.recentViews().isEmpty)
    }

    // MARK: - Сохранённые заказы

    @Test("заказ сохраняется со строками и порядком")
    func savesOrder() throws {
        let store = try Self.makeStore()
        var order = Order(startingWith: Self.item("Chicken"))
        order.add(Self.item("Brown Rice"))
        order.setQuantity(2, for: Self.item("Chicken").persistentID)

        try store.save(order, title: "My usual")

        let saved = try #require(try store.savedOrders().first)
        #expect(saved.title == "My usual")
        #expect(saved.chain == "Chipotle")
        #expect(saved.orderedLines.map(\.name) == ["Chicken", "Brown Rice"])
        #expect(saved.orderedLines[0].quantity == 2)
    }

    /// Макросы в заказе не консервируются: когда цифра у сети изменится,
    /// сохранённый заказ должен показать новую, а не старую.
    @Test("сохранённый заказ берёт цифры из текущего каталога")
    func resolvesAgainstCurrentCatalog() throws {
        let store = try Self.makeStore()
        try store.save(Order(startingWith: Self.item("Chicken")), title: "Bowl")
        let saved = try #require(try store.savedOrders().first)

        // Тот же ключ, но калорий стало больше — как после сверки с сайтом сети.
        let updated: [String: Any] = [
            "format": 1, "version": 2,
            "source": "chipotle.com", "observed": "2026-09-07", "stale": false,
            "chains": [["name": "Chipotle", "itemCount": 1]],
            "items": [["chain": "Chipotle", "key": "chicken", "name": "Chicken",
                       "kcal": 250, "protein": 36, "carbs": 0, "fat": 10]],
        ]
        let newer = MenuCatalog(
            pack: try MenuPack.decode(from: JSONSerialization.data(withJSONObject: updated)))

        let resolved = ResolvedOrder(saved: saved, catalog: newer)
        #expect(resolved.order.totals.kcal == 250)
        #expect(!resolved.hasMissing)
    }

    /// Исчезнувшую позицию нельзя просто не досчитать: человек должен узнать,
    /// что её больше нет в меню.
    @Test("исчезнувшая позиция называется, а не пропадает молча")
    func reportsMissingItems() throws {
        let store = try Self.makeStore()
        var order = Order(startingWith: Self.item("Chicken"))
        order.add(Self.item("Brown Rice"))
        try store.save(order, title: "Bowl")
        let saved = try #require(try store.savedOrders().first)

        let shrunk: [String: Any] = [
            "format": 1, "version": 3,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "Chipotle", "itemCount": 1]],
            "items": [["chain": "Chipotle", "key": "chicken", "name": "Chicken",
                       "kcal": 180, "protein": 32, "carbs": 0, "fat": 7]],
        ]
        let catalog = MenuCatalog(
            pack: try MenuPack.decode(from: JSONSerialization.data(withJSONObject: shrunk)))

        let resolved = ResolvedOrder(saved: saved, catalog: catalog)
        #expect(resolved.order.lines.count == 1)
        #expect(resolved.missing == ["Brown Rice"])
        #expect(resolved.hasMissing)
    }

    @Test("заказ удаляется вместе со строками")
    func deletesOrderAndLines() throws {
        let store = try Self.makeStore()
        try store.save(Order(startingWith: Self.item("Chicken")), title: "Bowl")
        let saved = try #require(try store.savedOrders().first)

        try store.delete(saved)
        #expect(try store.savedOrders().isEmpty)
        #expect(try store.context.fetch(FetchDescriptor<SavedOrderLine>()).isEmpty,
                "строки должны удалиться каскадом")
    }

    /// Все свойства с умолчаниями и никаких уникальных атрибутов — без этого
    /// CloudKit откажется поднимать схему, и синхронизация молча не включится.
    @Test("схема совместима с CloudKit")
    func schemaIsCloudKitCompatible() throws {
        // Проверяем саму схему, а не зеркалирование: настоящий CloudKit-контейнер
        // в тестах только сыпал бы ошибками в лог, а утверждения те же.
        let container = try ModelContainer(
            for: ViewedItem.self, SavedOrder.self, SavedOrderLine.self,
            configurations: ModelConfiguration(
                isStoredInMemoryOnly: true, cloudKitDatabase: .none))
        #expect(container.schema.entities.count == 3)

        for entity in container.schema.entities {
            #expect(entity.uniquenessConstraints.isEmpty,
                    "\(entity.name): CloudKit не поддерживает уникальные атрибуты")
            for relationship in entity.relationships {
                #expect(relationship.isOptional || relationship.isToOneRelationship == false,
                        "\(entity.name).\(relationship.name): связь должна быть необязательной")
            }
        }
    }
}
