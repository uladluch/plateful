import SwiftData
import SwiftUI

/// Карточка блюда: число, ради которого открывали приложение, и честная
/// подпись о том, откуда оно взялось.
struct ItemDetailView: View {

    let item: MenuItem

    @Environment(\.modelContext) private var context

    @State private var isPickingRival = false
    @State private var rival: MenuItem?

    var body: some View {
        List {
            Section {
                DishImage(item: item, size: 220, isHero: true)
                    .listRowInsets(EdgeInsets())
                    .listRowBackground(Color.clear)
            }

            Section {
                calories
                macro("Protein", value: item.proteinText, color: Tokens.Color.protein)
                macro("Carbs", value: item.carbsText, color: Tokens.Color.carbs)
                macro("Fat", value: item.fatText, color: Tokens.Color.fat)
            } header: {
                Text(item.chain)
            }

            if let serving = item.serving {
                Section {
                    LabeledContent {
                        Text(serving)
                    } label: {
                        Label("Serving", systemImage: Tokens.Symbol.serving)
                    }
                }
            }

            // Конкурентов бьют за молчаливо устаревшие данные. Мы говорим,
            // откуда цифра и на какой год, — это одно из трёх отличий.
            Section {
                LabeledContent {
                    Text(item.sourceDisplayName)
                        .multilineTextAlignment(.trailing)
                } label: {
                    Label("Source", systemImage: Tokens.Symbol.source)
                }
                LabeledContent {
                    Text(item.observedDisplay)
                        .monospacedDigit()
                } label: {
                    Label("Figures from", systemImage: Tokens.Symbol.stale)
                }
            } footer: {
                if let notice = item.staleNotice {
                    Text(notice)
                }
            }
        }
        .navigationTitle(item.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("Compare", systemImage: "arrow.left.arrow.right") {
                    isPickingRival = true
                }
            }
            ToolbarItem(placement: .primaryAction) {
                NavigationLink {
                    OrderView(startingWith: item)
                } label: {
                    Label("Build order", systemImage: "plus.forwardslash.minus")
                }
            }
        }
        .sheet(isPresented: $isPickingRival) {
            ItemPickerView(chain: nil, excluding: item.persistentID) { picked in
                rival = picked
                isPickingRival = false
            }
        }
        .navigationDestination(item: $rival) { other in
            ComparisonView(comparison: Comparison(left: item, right: other))
        }
        .task {
            // Сбой истории не должен мешать смотреть калории — это справочник,
            // а история лишь удобство.
            try? UserDataStore(context: context).recordView(of: item)
        }
    }

    private var calories: some View {
        HStack(alignment: .firstTextBaseline, spacing: Tokens.Spacing.s) {
            Text(item.calorieText)
                .font(.largeTitle)
                .fontWeight(.semibold)
                .monospacedDigit()
                .foregroundStyle(Tokens.Color.calories)
            Text("calories")
                .font(.subheadline)
                .foregroundStyle(Tokens.Color.textSecondary)
            Spacer()
            if item.isStale {
                Image(systemName: Tokens.Symbol.stale)
                    .foregroundStyle(Tokens.Color.staleWarning)
                    .accessibilityLabel("Figures may be out of date")
            }
        }
        .padding(.vertical, Tokens.Spacing.xs)
        .accessibilityElement(children: .combine)
    }

    private func macro(_ title: String, value: String, color: Color) -> some View {
        LabeledContent {
            Text(value).monospacedDigit()
        } label: {
            Label {
                Text(title)
            } icon: {
                Image(systemName: Tokens.Symbol.protein)
                    .foregroundStyle(color)
                    .imageScale(.small)
            }
        }
    }
}

#Preview("Устаревшие данные") {
    NavigationStack {
        ItemDetailView(item: MenuRepository.previewItem(name: "Big Mac"))
    }
}

#Preview("Сверено с сайтом сети") {
    NavigationStack {
        ItemDetailView(item: MenuRepository.previewItem(name: "Quarter Pounder w/ Cheese"))
    }
}
