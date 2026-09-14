import SwiftUI

/// Разведка каталога, подсказка блюда, аналитика, профиль.
///
/// Поиск раньше жил отдельной вкладкой с ролью `.search`; теперь он —
/// `.searchable` поверх сеток «Discovery», как поиск был устроен изначально.
/// Отдельная вкладка стоила места в панели ради жеста, который «Discovery»
/// и так умеет. «Рядом» — в тулбаре «Discovery»: разрез того же справочника,
/// а не отдельный раздел.
///
/// Выбранная вкладка и пути стеков живут здесь, а не в экранах: так переход
/// можно открыть из кода — вернуть вкладку к корню или привести ссылку.
struct RootView: View {

    @State private var selection = AppTab.discovery
    @State private var discoveryPath: [Route] = []
    @State private var mealsPath: [Route] = []
    @State private var profilePath: [Route] = []

    var body: some View {
        TabView(selection: $selection) {
            Tab("Discovery", systemImage: Tokens.Symbol.chain, value: AppTab.discovery) {
                ChainsView(path: $discoveryPath)
            }
            Tab("Suggest Meal", systemImage: "wand.and.stars", value: AppTab.meals) {
                SavedOrdersView(path: $mealsPath)
            }
            Tab("Analytics", systemImage: "chart.bar", value: AppTab.analytics) {
                AnalyticsView()
            }
            Tab("Profile", systemImage: "person.crop.circle", value: AppTab.profile) {
                ProfileView(path: $profilePath)
            }
        }
        .minimizesTabBarOnScroll()
    }
}

private extension View {

    /// Панель вкладок прячется при прокрутке вниз — длинное меню сети
    /// получает место. API есть только с iOS 26; раньше панель остаётся.
    @ViewBuilder
    func minimizesTabBarOnScroll() -> some View {
        if #available(iOS 26, *) {
            tabBarMinimizeBehavior(.onScrollDown)
        } else {
            self
        }
    }
}

#Preview {
    RootView().environment(MenuRepository.preview).environment(NearbyStore())
}
