import SwiftUI

/// Корневой экран: сетки сетей и поиск по всему каталогу.
///
/// Первое, что видит человек, — уже полезно: ни онбординга, ни аккаунта,
/// ни пейволла. Это и есть позиционирование против всей категории. Поиск —
/// `.searchable` прямо здесь, а не отдельная вкладка: искать по каталогу
/// и листать его — один и тот же режим экрана, а не два разных места.
struct ChainsView: View {

    @Environment(MenuRepository.self) private var menu
    @State private var query = ""

    var body: some View {
        NavigationStack {
            content
                .navigationTitle("Discovery")
                .searchable(text: $query, prompt: "Search chains and dishes")
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
            if query.isEmpty {
                chainList
            } else {
                searchResults
            }
        }
    }

    /// Две колонки минимум, больше — на широком экране: тот же приём, что
    /// в системных плиточных списках (Музыка, Погода).
    private static let columns = [GridItem(.adaptive(minimum: 150), spacing: Tokens.Spacing.m)]

    private var chainList: some View {
        ScrollView {
            LazyVGrid(columns: Self.columns, spacing: Tokens.Spacing.m) {
                ForEach(menu.chains) { chain in
                    NavigationLink(value: chain) {
                        ChainCard(chain: chain)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(Tokens.Spacing.m)
        }
        .navigationDestination(for: MenuChain.self) { ChainMenuView(chain: $0) }
        .navigationDestination(for: MenuItem.self) { ItemDetailView(item: $0) }
        // Проверка обновлений сама идёт при запуске; жест нужен тем, кто
        // увидел устаревшее число и хочет проверить прямо сейчас.
        .refreshable { await menu.checkForUpdate() }
    }

    /// Запрос ищет сразу по всем сетям, а не по одной открытой.
    @ViewBuilder
    private var searchResults: some View {
        let results = menu.collapsingVariants(menu.search(query))
        if results.isEmpty {
            ContentUnavailableView.search(text: query)
        } else {
            List(results) { item in
                NavigationLink(value: item) {
                    MenuItemRow(item: item, showsChain: true,
                                variants: menu.variants(of: item))
                }
            }
            .navigationDestination(for: MenuItem.self) { ItemDetailView(item: $0) }
        }
    }
}

#Preview {
    ChainsView().environment(MenuRepository.preview)
}
