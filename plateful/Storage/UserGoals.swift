import Foundation
import SwiftData

/// Цели человека. Не аккаунт: всё локально и уезжает в iCloud вместе с
/// остальными данными пользователя.
///
/// Обе цели необязательные — приложение обязано быть полезным тому, кто
/// никаких целей не ставил.
@Model
final class UserGoals {

    var calorieCeiling: Int?
    var proteinFloor: Int?
    var updatedAt: Date = Date.distantPast

    init(calorieCeiling: Int? = nil, proteinFloor: Int? = nil) {
        self.calorieCeiling = calorieCeiling
        self.proteinFloor = proteinFloor
        self.updatedAt = .now
    }

    var isEmpty: Bool { calorieCeiling == nil && proteinFloor == nil }

    var filter: MenuFilter {
        MenuFilter(maxCalories: calorieCeiling, minProtein: proteinFloor)
    }
}

extension UserDataStore {

    /// Единственная запись целей. CloudKit не умеет уникальность, поэтому
    /// лишние копии, приехавшие с другого устройства, схлопываем сами —
    /// побеждает последняя по времени правки.
    func goals() throws -> UserGoals {
        let existing = try context.fetch(FetchDescriptor<UserGoals>(
            sortBy: [SortDescriptor(\.updatedAt, order: .reverse)]))

        if let newest = existing.first {
            for duplicate in existing.dropFirst() { context.delete(duplicate) }
            return newest
        }

        let goals = UserGoals()
        context.insert(goals)
        return goals
    }

    func updateGoals(calorieCeiling: Int?, proteinFloor: Int?) throws {
        let goals = try goals()
        goals.calorieCeiling = calorieCeiling
        goals.proteinFloor = proteinFloor
        goals.updatedAt = .now
        try context.save()
    }
}
