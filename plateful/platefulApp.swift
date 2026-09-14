//
//  platefulApp.swift
//  plateful
//
//  Created by Ulad Luch on 07/09/2026.
//

import OSLog
import SwiftData
import SwiftUI

@main
struct platefulApp: App {

    /// Каталог живёт столько же, сколько приложение: он read-only и грузится
    /// один раз. Экраны получают его из окружения и не знают, приехал он из
    /// бандла или из скачанного пака.
    @State private var menu = MenuRepository()

    /// Что рядом — тоже один на приложение. Главный экран и вкладка «рядом»
    /// раньше заводили по своему и слали карте по залпу в 90 запросов; карта
    /// ограничивает частоту, и второй залп почти целиком получал отказ.
    @State private var nearby = NearbyStore()

    /// История, сохранённые заказы и цели.
    ///
    /// Конфигурация по умолчанию идёт с `cloudKitDatabase: .automatic`: при
    /// наличии entitlement данные синхронизируются через iCloud, аккаунт в
    /// приложении для этого не нужен.
    private let userData: ModelContainer = Self.makeUserDataContainer()

    private static let schema: [any PersistentModel.Type] = [
        ViewedItem.self, SavedOrder.self, SavedOrderLine.self, UserGoals.self,
    ]

    /// Лестница отступления, а не один запасной вариант.
    ///
    /// Порядок важен: сначала iCloud, потом локальный файл, и только в самом
    /// конце память. Уронить синхронизацию — неприятно, а свалиться сразу в
    /// память значит молча терять сохранённые заказы при каждом запуске,
    /// и человек об этом не узнает.
    private static func makeUserDataContainer() -> ModelContainer {
        let log = Logger(subsystem: "com.anluch.plateful", category: "storage")

        do {
            return try ModelContainer(for: Schema(schema))
        } catch {
            log.error("iCloud-хранилище не поднялось, остаюсь на локальном: \(error.localizedDescription)")
        }

        do {
            return try ModelContainer(
                for: Schema(schema),
                configurations: ModelConfiguration(cloudKitDatabase: .none))
        } catch {
            log.error("Локальное хранилище не поднялось: \(error.localizedDescription)")
        }

        // Справочник должен работать даже так: поиск и калории от истории
        // не зависят.
        do {
            return try ModelContainer(
                for: Schema(schema),
                configurations: ModelConfiguration(isStoredInMemoryOnly: true, cloudKitDatabase: .none))
        } catch {
            // Сюда не должно доходить никогда; если дошло — причина в логе,
            // а не безымянный `try!`.
            log.fault("Даже хранилище в памяти не поднялось: \(error.localizedDescription)")
            fatalError("In-memory ModelContainer failed: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(menu)
                .environment(nearby)
                .task {
                    await menu.load()
                    // Обновление — после того, как каталог уже показан:
                    // запуск не должен ждать сети.
                    await menu.checkForUpdate()
                }
        }
        .modelContainer(userData)
    }
}
