//
//  platefulApp.swift
//  plateful
//
//  Created by Ulad Luch on 07/09/2026.
//

import SwiftUI

@main
struct platefulApp: App {

    /// Каталог живёт столько же, сколько приложение: он read-only и грузится
    /// один раз. Экраны получают его из окружения и не знают, приехал он из
    /// бандла или из скачанного пака.
    @State private var menu = MenuRepository()

    var body: some Scene {
        WindowGroup {
            ChainsView()
                .environment(menu)
                .task { await menu.load() }
        }
    }
}
