import SwiftUI

/// Сборка заказа с пересчётом на лету.
///
/// Главное функциональное отличие: ни один из девяти конкурентов не даёт
/// изменить блюдо — а заказывают именно так, «с двойной курицей и без риса».
struct OrderView: View {

    @Environment(MenuRepository.self) private var menu
    @State private var order: Order
    @State private var isPickingItem = false

    init(startingWith item: MenuItem) {
        _order = State(initialValue: Order(startingWith: item))
    }

    var body: some View {
        List {
            Section {
                TotalsRow(totals: order.totals)
            } header: {
                Text("Total")
            } footer: {
                Text(footnote)
            }

            Section {
                ForEach(order.lines) { line in
                    OrderLineRow(
                        line: line,
                        quantity: Binding(
                            get: { line.quantity },
                            set: { order.setQuantity($0, for: line.id) }))
                }
                .onDelete { order.remove(atOffsets: $0) }

                Button("Add item", systemImage: "plus") {
                    isPickingItem = true
                }
            } header: {
                Text("Items")
            }
        }
        .navigationTitle(order.chain)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { EditButton() }
        .sheet(isPresented: $isPickingItem) {
            ItemPickerView(chain: order.chain) { order.add($0) }
        }
    }

    /// Говорим прямо, что итог — сумма опубликованных цифр, а не наша оценка.
    private var footnote: String {
        order.isStale
            ? "Adds up the figures each chain published. Some are from earlier years, so treat the total as a guide."
            : "Adds up the figures each chain published."
    }
}

/// Итог заказа: калории крупно, макросы рядом.
private struct TotalsRow: View {

    let totals: Nutrition

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
            HStack(alignment: .firstTextBaseline, spacing: Tokens.Spacing.s) {
                Text(totals.kcal.formatted(.number.precision(.fractionLength(0))))
                    .font(.largeTitle)
                    .fontWeight(.semibold)
                    .monospacedDigit()
                    .contentTransition(.numericText())
                Text("calories")
                    .font(.subheadline)
                    .foregroundStyle(Tokens.Color.textSecondary)
            }
            HStack(spacing: Tokens.Spacing.m) {
                macro("Protein", MenuItem.grams(totals.protein), Tokens.Color.protein)
                macro("Carbs", MenuItem.grams(totals.carbs), Tokens.Color.carbs)
                macro("Fat", MenuItem.grams(totals.fat), Tokens.Color.fat)
            }
        }
        .padding(.vertical, Tokens.Spacing.xs)
        .animation(.default, value: totals)
        .accessibilityElement(children: .combine)
    }

    private func macro(_ title: String, _ value: String, _ color: Color) -> some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
            Text(title)
                .font(.caption)
                .foregroundStyle(Tokens.Color.textSecondary)
            Text(value)
                .font(.subheadline)
                .monospacedDigit()
                .foregroundStyle(color)
                .contentTransition(.numericText())
        }
    }
}

/// Строка заказа со степпером количества.
private struct OrderLineRow: View {

    let line: OrderLine
    @Binding var quantity: Int

    var body: some View {
        Stepper(value: $quantity, in: Order.quantityRange) {
            LabeledContent {
                Text((line.item.nutrition * quantity).kcal
                    .formatted(.number.precision(.fractionLength(0))))
                    .monospacedDigit()
                    .contentTransition(.numericText())
            } label: {
                VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                    Text(line.item.name)
                    Text("\(quantity) × \(line.item.calorieText)")
                        .font(.caption)
                        .foregroundStyle(Tokens.Color.textSecondary)
                        .monospacedDigit()
                }
            }
        }
    }
}

#Preview {
    NavigationStack {
        OrderView(startingWith: MenuRepository.previewItem(name: "Big Mac"))
    }
    .environment(MenuRepository.preview)
}
