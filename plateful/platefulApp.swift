//
//  platefulApp.swift
//  plateful
//
//  Created by Ulad Luch on 07/09/2026.
//

import SwiftData
import SwiftUI

@main
struct platefulApp: App {

    /// Каталог живёт столько же, сколько приложение: он read-only и грузится
    /// один раз. Экраны получают его из окружения и не знают, приехал он из
    /// бандла или из скачанного пака.
    @State private var menu = MenuRepository()

    /// История и сохранённые заказы. Конфигурация по умолчанию идёт с
    /// `cloudKitDatabase: .automatic`, поэтому данные начнут синхронизироваться
    /// через iCloud, как только у таргета появится entitlement, — без правок
    /// в моделях и без аккаунта в приложении.
    private let userData: ModelContainer = {
        do {
            return try ModelContainer(for: ViewedItem.self, SavedOrder.self, SavedOrderLine.self)
        } catch {
            // Хранилище пользователя не должно ронять справочник: поиск и
            // калории работают и без истории.
            return try! ModelContainer(
                for: ViewedItem.self, SavedOrder.self, SavedOrderLine.self,
                configurations: ModelConfiguration(isStoredInMemoryOnly: true))
        }
    }()

    var body: some Scene {
        WindowGroup {
            ChainsView()
                .environment(menu)
                .task { await menu.load() }
        }
        .modelContainer(userData)
    }
}
