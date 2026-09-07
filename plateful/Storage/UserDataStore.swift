import Foundation
import SwiftData

/// Всё, что пишет пользователь: история просмотров и сохранённые заказы.
///
/// Живёт на главном акторе, потому что работает с основным `ModelContext`,
/// из которого читают экраны.
@MainActor
struct UserDataStore {

    /// Сколько просмотров помним. Дальше история перестаёт быть полезной
    /// и начинает мешать — плюс это лишний трафик синхронизации iCloud.
    static let historyLimit = 50

    let context: ModelContext

    init(context: ModelContext) {
        self.context = context
    }

    // MARK: - История

    /// Запоминает открытую позицию.
    ///
    /// Повторный просмотр не плодит строки, а поднимает дату: CloudKit не
    /// поддерживает уникальные атрибуты, поэтому дедуплицируем вручную.
    func recordView(of item: MenuItem) throws {
        let reference = item.persistentID
        let existing = try context.fetch(FetchDescriptor<ViewedItem>()).filter {
            $0.reference == reference
        }

        if let first = existing.first {
            first.viewedAt = .now
            first.name = item.name
            // Дубли могли приехать из iCloud с другого устройства.
            for extra in existing.dropFirst() { context.delete(extra) }
        } else {
            context.insert(ViewedItem(
                chain: item.chain, itemKey: item.key, name: item.name, viewedAt: .now))
        }

        try trimHistory()
        try context.save()
    }

    func recentViews(limit: Int = historyLimit) throws -> [ViewedItem] {
        var descriptor = FetchDescriptor<ViewedItem>(
            sortBy: [SortDescriptor(\.viewedAt, order: .reverse)])
        descriptor.fetchLimit = limit
        return try context.fetch(descriptor)
    }

    func clearHistory() throws {
        for view in try context.fetch(FetchDescriptor<ViewedItem>()) {
            context.delete(view)
        }
        try context.save()
    }

    private func trimHistory() throws {
        let all = try context.fetch(FetchDescriptor<ViewedItem>(
            sortBy: [SortDescriptor(\.viewedAt, order: .reverse)]))
        for stale in all.dropFirst(Self.historyLimit) { context.delete(stale) }
    }

    // MARK: - Сохранённые заказы

    @discardableResult
    func save(_ order: Order, title: String) throws -> SavedOrder {
        let saved = SavedOrder(chain: order.chain, title: title, createdAt: .now)
        context.insert(saved)

        saved.lines = order.lines.enumerated().map { position, line in
            let stored = SavedOrderLine(
                chain: line.item.chain, itemKey: line.item.key, name: line.item.name,
                quantity: line.quantity, position: position)
            context.insert(stored)
            return stored
        }

        try context.save()
        return saved
    }

    func savedOrders() throws -> [SavedOrder] {
        try context.fetch(FetchDescriptor<SavedOrder>(
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]))
    }

    func delete(_ saved: SavedOrder) throws {
        context.delete(saved)
        try context.save()
    }
}
