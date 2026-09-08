import SwiftUI

/// Корневой экран: список сетей.
///
/// Первое, что видит человек, — уже полезно: ни онбординга, ни аккаунта,
/// ни пейволла. Это и есть позиционирование против всей категории. Поиск
/// живёт отдельной вкладкой панели; здесь — то, что видно без запроса.
struct ChainsView: View {

    @Environment(MenuRepository.self) private var menu

    var body: some View {
        NavigationStack {
            content
                .navigationTitle("Restaurants")
                .toolbar {
                    ToolbarItem(placement: .primaryAction) {
                        NavigationLink {
                            NearbyView()
                        } label: {
                            Label("Nearby", systemImage: "location")
                        }
                    }
                }
        }
    }

    @ViewBuilder
    private var content: some View {
        switch menu.state {
        case .loading:
            ProgressView("Loading menus")

        case .failed(let message):
            ContentUnavailableView(
                "Menus unavailable",
                systemImage: Tokens.Symbol.failure,
                description: Text(message))

        case .ready:
            chainList
        }
    }

    private var chainList: some View {
        List {
            ForEach(menu.chains) { chain in
                NavigationLink(value: chain) {
                    ChainRow(chain: chain)
                }
            }
        }
        .navigationDestination(for: MenuChain.self) { ChainMenuView(chain: $0) }
        .navigationDestination(for: MenuItem.self) { ItemDetailView(item: $0) }
        // Проверка обновлений сама идёт при запуске; жест нужен тем, кто
        // увидел устаревшее число и хочет проверить прямо сейчас.
        .refreshable { await menu.checkForUpdate() }
    }
}

#Preview {
    ChainsView().environment(MenuRepository.preview)
}
