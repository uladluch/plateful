import Foundation
import SwiftData
import Testing

@testable import plateful

@Suite("Цели пользователя")
@MainActor
struct UserGoalsTests {

    private static func makeStore() throws -> UserDataStore {
        let container = try ModelContainer(
            for: ViewedItem.self, SavedOrder.self, SavedOrderLine.self, UserGoals.self,
            configurations: ModelConfiguration(
                isStoredInMemoryOnly: true, cloudKitDatabase: .none))
        return UserDataStore(context: ModelContext(container))
    }

    @Test("по умолчанию целей нет")
    func startsEmpty() throws {
        let goals = try Self.makeStore().goals()
        #expect(goals.isEmpty)
        #expect(!goals.filter.isActive)
    }

    @Test("цели сохраняются и становятся фильтром")
    func savesGoals() throws {
        let store = try Self.makeStore()
        try store.updateGoals(calorieCeiling: 600, proteinFloor: 25)

        let goals = try store.goals()
        #expect(goals.calorieCeiling == 600)
        #expect(goals.proteinFloor == 25)
        #expect(goals.filter == MenuFilter(maxCalories: 600, minProtein: 25))
    }

    @Test("цель можно снять")
    func clearsGoal() throws {
        let store = try Self.makeStore()
        try store.updateGoals(calorieCeiling: 600, proteinFloor: 25)
        try store.updateGoals(calorieCeiling: nil, proteinFloor: 25)

        let goals = try store.goals()
        #expect(goals.calorieCeiling == nil)
        #expect(goals.proteinFloor == 25)
        #expect(!goals.isEmpty)
    }

    @Test("запись целей одна, а не плодится")
    func keepsSingleRecord() throws {
        let store = try Self.makeStore()
        try store.updateGoals(calorieCeiling: 600, proteinFloor: nil)
        try store.updateGoals(calorieCeiling: 700, proteinFloor: nil)

        #expect(try store.context.fetch(FetchDescriptor<UserGoals>()).count == 1)
        #expect(try store.goals().calorieCeiling == 700)
    }

    /// CloudKit не умеет уникальность, поэтому дубли могут приехать с другого
    /// устройства. Побеждает последняя по времени правки.
    @Test("дубли из iCloud схлопываются в последнюю правку")
    func mergesDuplicates() throws {
        let store = try Self.makeStore()

        let older = UserGoals(calorieCeiling: 500, proteinFloor: nil)
        older.updatedAt = Date(timeIntervalSince1970: 1000)
        let newer = UserGoals(calorieCeiling: 900, proteinFloor: 40)
        newer.updatedAt = Date(timeIntervalSince1970: 2000)
        store.context.insert(older)
        store.context.insert(newer)

        let goals = try store.goals()
        #expect(goals.calorieCeiling == 900)
        #expect(goals.proteinFloor == 40)
        #expect(try store.context.fetch(FetchDescriptor<UserGoals>()).count == 1)
    }
}
