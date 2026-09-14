import SwiftData
import SwiftUI

/// Сохранённые заказы — «моё обычное» по сетям.
struct SavedOrdersView: View {

    @Binding var path: [Route]

    @Environment(MenuRepository.self) private var menu
    @Environment(\.modelContext) private var context

    @Query(sort: \SavedOrder.createdAt, order: .reverse)
    private var orders: [SavedOrder]

    var body: some View {
        NavigationStack(path: $path) {
            Group {
                if orders.isEmpty {
                    ContentUnavailableView(
                        "No saved orders",
                        systemImage: "bookmark",
                        description: Text("Build an order from any dish and save it for one-tap lookup."))
                } else {
                    List {
                        ForEach(orders) { order in
                            NavigationLink(value: Route.savedOrder(order.persistentModelID)) {
                                SavedOrderRow(order: order, catalog: menu.catalog)
                            }
                        }
                        .onDelete(perform: delete)
                    }
                }
            }
            .navigationTitle("Suggest Meal")
            .navigationBarTitleDisplayMode(.inline)
            // На стабильном Group, а не на List внутри if/else: назначение,
            // объявленное в условной ветке, однажды теряется при повторном
            // рендере, и вторая попытка открыть заказ перестаёт работать.
            .routeDestinations()
        }
    }

    private func delete(at offsets: IndexSet) {
        let store = UserDataStore(context: context)
        for index in offsets {
            UserDataStore.attempt("Удаление заказа") { try store.delete(orders[index]) }
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
///
/// Заказ приходит ссылкой и читается запросом, а не моделью из пути: пока
/// экран открыт, заказ могут удалить свайпом или правкой из iCloud, и
/// удалённая модель в пути показала бы мусор.
struct SavedOrderDetailView: View {

    @Environment(MenuRepository.self) private var menu
    @Query private var matches: [SavedOrder]

    init(id: PersistentIdentifier) {
        _matches = Query(filter: #Predicate<SavedOrder> { $0.persistentModelID == id })
    }

    var body: some View {
        Group {
            if let saved = matches.first {
                if let catalog = menu.catalog {
                    OrderBreakdown(resolved: ResolvedOrder(saved: saved, catalog: catalog))
                } else {
                    ProgressView()
                }
            } else {
                ContentUnavailableView("Order deleted", systemImage: "bookmark.slash")
            }
        }
        .navigationTitle(matches.first?.title ?? "")
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct OrderBreakdown: View {

    let resolved: ResolvedOrder

    var body: some View {
        let archived = resolved.order.lines.filter(\.item.isOffMenu)

        List {
            Section {
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
            } header: {
                SectionTitle("Total")
            }

            Section {
                ForEach(resolved.order.lines) { line in
                    NavigationLink(value: Route.item(line.item)) {
                        LabeledContent {
                            Text("\(line.quantity)×").monospacedDigit()
                        } label: {
                            Text(line.item.name)
                        }
                    }
                }
            } header: {
                SectionTitle("Items")
            }

            // Блюдо ещё в каталоге, но сеть его больше не продаёт.
            if !archived.isEmpty {
                Section {
                    ForEach(archived) { line in
                        Label(line.item.name, systemImage: Tokens.Symbol.stale)
                            .foregroundStyle(Tokens.Color.staleWarning)
                    }
                } header: {
                    SectionTitle("No longer on the menu")
                } footer: {
                    Text("Still counted in the total, but you may not be able to order them.")
                }
            }

            // Исчезнувшие позиции называем прямо: молчаливый недосчёт
            // калорий — ровно та претензия, за которую бьют конкурентов.
            if resolved.hasMissing {
                Section {
                    // По месту в списке, а не по имени: два одинаковых
                    // исчезнувших блюда в заказе иначе делили бы одну строку.
                    ForEach(Array(resolved.missing.enumerated()), id: \.offset) { _, name in
                        Label(name, systemImage: Tokens.Symbol.failure)
                            .foregroundStyle(Tokens.Color.staleWarning)
                    }
                } header: {
                    SectionTitle("No longer on the menu")
                } footer: {
                    Text("These are not counted in the total.")
                }
            }
        }
    }
}
