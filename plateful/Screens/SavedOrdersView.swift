import SwiftData
import SwiftUI

/// Сохранённые заказы — «моё обычное» по сетям.
struct SavedOrdersView: View {

    @Environment(MenuRepository.self) private var menu
    @Environment(\.modelContext) private var context

    @Query(sort: \SavedOrder.createdAt, order: .reverse)
    private var orders: [SavedOrder]

    var body: some View {
        NavigationStack {
            Group {
                if orders.isEmpty {
                    ContentUnavailableView(
                        "No saved orders",
                        systemImage: "bookmark",
                        description: Text("Build an order from any dish and save it for one-tap lookup."))
                } else {
                    List {
                        ForEach(orders) { order in
                            NavigationLink(value: order) {
                                SavedOrderRow(order: order, catalog: menu.catalog)
                            }
                        }
                        .onDelete(perform: delete)
                    }
                    .navigationDestination(for: SavedOrder.self) {
                        SavedOrderDetailView(saved: $0)
                    }
                }
            }
            .navigationTitle("Saved")
        }
    }

    private func delete(at offsets: IndexSet) {
        let store = UserDataStore(context: context)
        for index in offsets {
            try? store.delete(orders[index])
        }
    }
}

/// Строка списка: название, сеть и текущий итог по калориям.
private struct SavedOrderRow: View {

    let order: SavedOrder
    let catalog: MenuCatalog?

    var body: some View {
        LabeledContent {
            if let catalog {
                Text(ResolvedOrder(saved: order, catalog: catalog)
                    .order.totals.kcal.formatted(.number.precision(.fractionLength(0))))
                    .monospacedDigit()
            }
        } label: {
            VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                Text(order.title)
                Text("\(order.chain) · \(order.orderedLines.count) items")
                    .font(.caption)
                    .foregroundStyle(Tokens.Color.textSecondary)
            }
        }
    }
}

/// Разбор сохранённого заказа по текущему каталогу.
private struct SavedOrderDetailView: View {

    let saved: SavedOrder
    @Environment(MenuRepository.self) private var menu

    var body: some View {
        Group {
            if let catalog = menu.catalog {
                let resolved = ResolvedOrder(saved: saved, catalog: catalog)
                List {
                    Section("Total") {
                        LabeledContent("Calories") {
                            Text(resolved.order.totals.kcal
                                .formatted(.number.precision(.fractionLength(0))))
                                .monospacedDigit()
                        }
                        LabeledContent("Protein") {
                            Text(MenuItem.grams(resolved.order.totals.protein)).monospacedDigit()
                        }
                        LabeledContent("Carbs") {
                            Text(MenuItem.grams(resolved.order.totals.carbs)).monospacedDigit()
                        }
                        LabeledContent("Fat") {
                            Text(MenuItem.grams(resolved.order.totals.fat)).monospacedDigit()
                        }
                    }

                    Section("Items") {
                        ForEach(resolved.order.lines) { line in
                            NavigationLink(value: line.item) {
                                LabeledContent {
                                    Text("\(line.quantity)×").monospacedDigit()
                                } label: {
                                    Text(line.item.name)
                                }
                            }
                        }
                    }

                    // Исчезнувшие позиции называем прямо: молчаливый недосчёт
                    // калорий — ровно та претензия, за которую бьют конкурентов.
                    if resolved.hasMissing {
                        Section {
                            ForEach(resolved.missing, id: \.self) { name in
                                Label(name, systemImage: Tokens.Symbol.failure)
                                    .foregroundStyle(Tokens.Color.staleWarning)
                            }
                        } header: {
                            Text("No longer on the menu")
                        } footer: {
                            Text("These are not counted in the total.")
                        }
                    }
                }
                .navigationDestination(for: MenuItem.self) { ItemDetailView(item: $0) }
            } else {
                ProgressView()
            }
        }
        .navigationTitle(saved.title)
        .navigationBarTitleDisplayMode(.inline)
    }
}
