import SwiftUI

/// Корневой экран: список сетей и поиск по всему каталогу.
///
/// Первое, что видит человек, — уже полезно: ни онбординга, ни аккаунта,
/// ни пейволла. Это и есть позиционирование против всей категории.
struct ChainsView: View {

    @Environment(MenuRepository.self) private var menu
    @State private var query = ""

    var body: some View {
        NavigationStack {
            content
                .navigationTitle("Chains")
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
                chainList
            } else {
                searchResults
            }
        }
    }

    private var chainList: some View {
        List(menu.chains) { chain in
            NavigationLink(value: chain) {
                LabeledContent {
                    Text(chain.itemCount.formatted())
                        .monospacedDigit()
                } label: {
                    Label(chain.name, systemImage: Tokens.Symbol.chain)
                }
            }
        }
        .navigationDestination(for: MenuChain.self) { ChainMenuView(chain: $0) }
        .navigationDestination(for: MenuItem.self) { ItemDetailView(item: $0) }
    }

    @ViewBuilder
    private var searchResults: some View {
        let results = menu.search(query)
        if results.isEmpty {
            ContentUnavailableView.search(text: query)
        } else {
            List(results) { item in
                NavigationLink(value: item) {
                    MenuItemRow(item: item, showsChain: true)
                }
            }
            .navigationDestination(for: MenuItem.self) { ItemDetailView(item: $0) }
        }
    }
}

#Preview {
    ChainsView().environment(MenuRepository.preview)
}
