import SwiftUI

/// Справочник, что рядом и сохранённое.
///
/// Поиск остаётся первым и главным — он бесплатный и работает без аккаунта.
struct RootView: View {
    var body: some View {
        TabView {
            Tab("Menus", systemImage: "magnifyingglass") {
                ChainsView()
            }
            Tab("Nearby", systemImage: "location") {
                NearbyView()
            }
            Tab("Saved", systemImage: "bookmark") {
                SavedOrdersView()
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
