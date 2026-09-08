import SwiftData
import SwiftUI

/// Корневой экран: список сетей и поиск по всему каталогу.
///
/// Первое, что видит человек, — уже полезно: ни онбординга, ни аккаунта,
/// ни пейволла. Это и есть позиционирование против всей категории.
struct ChainsView: View {

    @Environment(MenuRepository.self) private var menu
    @State private var query = ""

    /// Последние просмотры. Бесплатны и лежат локально; через iCloud
    /// подхватятся на другом устройстве, когда включим entitlement.
    @Query(sort: \ViewedItem.viewedAt, order: .reverse)
    private var recent: [ViewedItem]

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
        List {
            if !recentItems.isEmpty {
                Section("Recent") {
                    ForEach(recentItems) { item in
                        NavigationLink(value: item) {
                            MenuItemRow(item: item, showsChain: true)
                        }
                    }
                }
            }

            Section(recentItems.isEmpty ? "" : "Chains") {
                ForEach(menu.chains) { chain in
                    NavigationLink(value: chain) {
                        LabeledContent {
                            Text(chain.itemCount.formatted())
                                .monospacedDigit()
                        } label: {
                            Label {
                                Text(chain.name)
                            } icon: {
                                ChainMarkView(chain: chain.name)
                            }
                        }
                    }
                }
            }
        }
        .navigationDestination(for: MenuChain.self) { ChainMenuView(chain: $0) }
        .navigationDestination(for: MenuItem.self) { ItemDetailView(item: $0) }
        // Проверка обновлений сама идёт при запуске; жест нужен тем, кто
        // увидел устаревшее число и хочет проверить прямо сейчас.
        .refreshable { await menu.checkForUpdate() }
    }

    /// Просмотренные позиции, которые ещё есть в текущем каталоге.
    ///
    /// Исчезнувшие из меню в истории не показываем: история — это ярлык
    /// «открыть снова», и вести он должен на живую карточку.
    private var recentItems: [MenuItem] {
        recent.prefix(10).compactMap { menu.item($0.reference) }
    }

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
