import SwiftUI

/// Рестораны, сохранённое, профиль — и поиск отдельной вкладкой.
///
/// Поиск живёт в табе с ролью `.search`: система кладёт его отдельно от
/// остальных и сама решает, как показать, — тот же жест, что в Картах и
/// App Store. «Рядом» из панели ушло в тулбар «Ресторанов»: это разрез того
/// же справочника, а не отдельный раздел, и место в панели он занимал зря.
struct RootView: View {
    var body: some View {
        TabView {
            Tab("Restaurants", systemImage: Tokens.Symbol.chain) {
                ChainsView()
            }
            Tab("Saved", systemImage: "bookmark") {
                SavedOrdersView()
            }
            Tab("Profile", systemImage: "person.crop.circle") {
                ProfileView()
            }
            Tab("Search", systemImage: "magnifyingglass", role: .search) {
                SearchView()
            }
        }
    }
}

#Preview {
    RootView().environment(MenuRepository.preview)
}
