import SwiftUI

/// Выбор позиции для добавления в заказ.
///
/// Ингредиенты идут первыми: там, где сеть публикует их отдельно — Chipotle,
/// Subway, — именно из них и собирают заказ. Где не публикует, раздел просто
/// не появится, и выбор пойдёт по обычному меню.
struct ItemPickerView: View {

    let chain: String
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
                    ForEach(orderedSections) { section in
                        Section(section.title) {
                            ForEach(section.items) { item in row(item) }
                        }
                    }
                } else {
                    let results = menu.search(query, in: chain)
                    if results.isEmpty {
                        ContentUnavailableView.search(text: query)
                    } else {
                        ForEach(results) { item in row(item) }
                    }
                }
            }
            .navigationTitle("Add to order")
            .navigationBarTitleDisplayMode(.inline)
            .searchable(text: $query, prompt: "Search \(chain)")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    /// Ингредиенты наверх, остальные разделы — в порядке пака.
    private var orderedSections: [MenuSection] {
        let sections = menu.sections(for: chain)
        let ingredients = sections.filter { $0.title == Self.ingredientsCategory }
        return ingredients + sections.filter { $0.title != Self.ingredientsCategory }
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
