import SwiftUI

/// Поиск по всему каталогу — своя вкладка панели, роль `.search`.
///
/// Раньше это было `.searchable` поверх списка сетей; теперь система сама
/// решает, как показать вкладку с ролью поиска (тот же приём, что в Картах
/// и App Store), и запрос ищет сразу по всем сетям, а не по одной открытой.
struct SearchView: View {

    @Environment(MenuRepository.self) private var menu
    @State private var query = ""

    var body: some View {
        NavigationStack {
            content
                .navigationTitle("Search")
                .searchable(text: $query, prompt: "Search chains and dishes")
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
                ContentUnavailableView(
                    "Search for a chain or a dish",
                    systemImage: "magnifyingglass")
            } else {
                results
            }
        }
    }

    @ViewBuilder
    private var results: some View {
        let items = menu.collapsingVariants(menu.search(query))
        if items.isEmpty {
            ContentUnavailableView.search(text: query)
        } else {
            List(items) { item in
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
    SearchView().environment(MenuRepository.preview)
}
