import SwiftUI

/// Разведка каталога, подсказка блюда, аналитика, профиль.
///
/// Поиск раньше жил отдельной вкладкой с ролью `.search`; теперь он —
/// `.searchable` поверх сеток «Discovery», как поиск был устроен изначально.
/// Отдельная вкладка стоила места в панели ради жеста, который «Discovery»
/// и так умеет. «Рядом» — в тулбаре «Discovery»: разрез того же справочника,
/// а не отдельный раздел.
struct RootView: View {
    var body: some View {
        TabView {
            Tab("Discovery", systemImage: Tokens.Symbol.chain) {
                ChainsView()
            }
            Tab("Suggest Meal", systemImage: "wand.and.stars") {
                SavedOrdersView()
            }
            Tab("Analytics", systemImage: "chart.bar") {
                AnalyticsView()
            }
            Tab("Profile", systemImage: "person.crop.circle") {
                ProfileView()
            }
        }
    }
}

#Preview {
    RootView().environment(MenuRepository.preview)
}
