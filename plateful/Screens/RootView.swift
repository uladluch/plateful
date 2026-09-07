import SwiftUI

/// Две вкладки: справочник и сохранённое.
///
/// Поиск остаётся первым и главным — он бесплатный и работает без аккаунта.
struct RootView: View {
    var body: some View {
        TabView {
            Tab("Menus", systemImage: "magnifyingglass") {
                ChainsView()
            }
            Tab("Saved", systemImage: "bookmark") {
                SavedOrdersView()
            }
        }
    }
}

#Preview {
    RootView().environment(MenuRepository.preview)
}
