import SwiftData
import SwiftUI

/// Меню одной сети, разбитое по категориям.
struct ChainMenuView: View {

    let chain: MenuChain

    @Environment(MenuRepository.self) private var menu
    @Query private var goals: [UserGoals]

    @State private var query = ""
    @State private var filter = MenuFilter.none

    var body: some View {
        List {
            if query.isEmpty {
                let sections = filter.apply(to: menu.sections(for: chain.name))
                if sections.isEmpty {
                    noMatches
                } else {
                    ForEach(sections) { section in
                        Section(section.title) {
                            ForEach(section.items) { item in
                                NavigationLink(value: item) {
                                    MenuItemRow(item: item, showsChain: false)
                                }
                            }
                        }
                    }
                }
            } else {
                let results = filter.apply(to: menu.search(query, in: chain.name, limit: 200))
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
        .toolbar {
            MenuFilterMenu(filter: $filter, goals: goals.first)
        }
    }

    /// Пустой результат объясняется целями, а не выглядит как поломка.
    private var noMatches: some View {
        ContentUnavailableView {
            Label("Nothing fits", systemImage: "line.3.horizontal.decrease.circle")
        } description: {
            Text("No item at \(chain.name) matches your goals.")
        } actions: {
            Button("Clear filter") { filter = .none }
        }
    }
}

#Preview {
    NavigationStack {
        ChainMenuView(chain: MenuChain(name: "McDonald's", itemCount: 3))
    }
    .environment(MenuRepository.preview)
}
