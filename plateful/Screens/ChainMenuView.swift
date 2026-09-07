import SwiftUI

/// Меню одной сети, разбитое по категориям.
struct ChainMenuView: View {

    let chain: MenuChain

    @Environment(MenuRepository.self) private var menu
    @State private var query = ""

    var body: some View {
        List {
            if query.isEmpty {
                ForEach(menu.sections(for: chain.name)) { section in
                    Section(section.title) {
                        ForEach(section.items) { item in
                            NavigationLink(value: item) {
                                MenuItemRow(item: item, showsChain: false)
                            }
                        }
                    }
                }
            } else {
                let results = menu.search(query, in: chain.name)
                if results.isEmpty {
                    ContentUnavailableView.search(text: query)
                } else {
                    ForEach(results) { item in
                        NavigationLink(value: item) {
                            MenuItemRow(item: item, showsChain: false)
                        }
                    }
                }
            }
        }
        .navigationTitle(chain.name)
        .navigationBarTitleDisplayMode(.inline)
        .searchable(text: $query, prompt: "Search \(chain.name)")
    }
}

#Preview {
    NavigationStack {
        ChainMenuView(chain: MenuChain(name: "McDonald's", itemCount: 3))
    }
    .environment(MenuRepository.preview)
}
