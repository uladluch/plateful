import SwiftUI

/// Выбор позиции для добавления в заказ.
///
/// Ингредиенты идут первыми: там, где сеть публикует их отдельно — Chipotle,
/// Subway, — именно из них и собирают заказ. Где не публикует, раздел просто
/// не появится, и выбор пойдёт по обычному меню.
struct ItemPickerView: View {

    /// Сеть, внутри которой выбираем. `nil` — искать по всему каталогу:
    /// сравнивать блюда разных сетей осмысленно, добавлять их в один заказ — нет.
    let chain: String?
    /// Позиция, которую нельзя выбрать: сравнивать блюдо с самим собой незачем.
    var excluding: MenuItem.PersistentID?
    let onPick: (MenuItem) -> Void

    @Environment(MenuRepository.self) private var menu
    @Environment(\.dismiss) private var dismiss
    @State private var query = ""

    /// Категория MenuStat, в которой лежат ингредиенты и добавки.
    private static let ingredientsCategory = "Toppings & Ingredients"

    var body: some View {
        NavigationStack {
            List {
                if query.isEmpty {
                    if let chain {
                        ForEach(orderedSections(for: chain)) { section in
                            Section(section.title) {
                                ForEach(section.items) { item in row(item) }
                            }
                        }
                    } else {
                        ContentUnavailableView(
                            "Find a dish",
                            systemImage: "magnifyingglass",
                            description: Text("Search any chain to compare against."))
                    }
                } else {
                    let results = selectable(menu.search(query, in: chain))
                    if results.isEmpty {
                        ContentUnavailableView.search(text: query)
                    } else {
                        ForEach(results) { item in row(item) }
                    }
                }
            }
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
            .searchable(text: $query, prompt: chain.map { "Search \($0)" } ?? "Search all chains")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    private var title: String { chain == nil ? "Compare with" : "Add to order" }

    /// Ингредиенты наверх, остальные разделы — в порядке пака.
    private func orderedSections(for chain: String) -> [MenuSection] {
        let sections = menu.sections(for: chain).map { section in
            MenuSection(title: section.title, items: selectable(section.items))
        }
        let ingredients = sections.filter { $0.title == Self.ingredientsCategory }
        return (ingredients + sections.filter { $0.title != Self.ingredientsCategory })
            .filter { !$0.items.isEmpty }
    }

    private func selectable(_ items: [MenuItem]) -> [MenuItem] {
        guard let excluding else { return items }
        return items.filter { $0.persistentID != excluding }
    }

    private func row(_ item: MenuItem) -> some View {
        Button {
            onPick(item)
        } label: {
            MenuItemRow(item: item, showsChain: false)
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    ItemPickerView(chain: "McDonald's") { _ in }
        .environment(MenuRepository.preview)
}
