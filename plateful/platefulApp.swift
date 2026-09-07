//
//  platefulApp.swift
//  plateful
//
//  Created by Ulad Luch on 07/09/2026.
//

import SwiftUI
import SwiftData

@main
struct platefulApp: App {
    var sharedModelContainer: ModelContainer = {
        let schema = Schema([
            Item.self,
        ])
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)

        do {
            return try ModelContainer(for: schema, configurations: [modelConfiguration])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()

    /// Каталог живёт столько же, сколько приложение: он read-only и грузится
    /// один раз. Экраны получают его из окружения и не знают, приехал он из
    /// бандла или из скачанного пака.
    @State private var menu = MenuRepository()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(menu)
                .task { await menu.load() }
        }
        .modelContainer(sharedModelContainer)
    }
}
