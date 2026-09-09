import SwiftData
import SwiftUI

/// Два блюда рядом, с разницей по каждой строке.
struct ComparisonView: View {

    let comparison: Comparison

    @Query private var goals: [UserGoals]

    var body: some View {
        List {
            Section {
                Grid(horizontalSpacing: Tokens.Spacing.m, verticalSpacing: Tokens.Spacing.s) {
                    GridRow {
                        heading(comparison.left)
                        heading(comparison.right)
                    }
                }
                .padding(.vertical, Tokens.Spacing.xs)
            }

            Section {
                ForEach(comparison.rows) { row in
                    NutrientRow(row: row)
                }
            } header: {
                SectionTitle("Difference is right minus left")
            }

            if let fit = comparison.meetsGoals(goals.first?.filter ?? .none) {
                Section {
                    goalFit(comparison.left, meets: fit.left)
                    goalFit(comparison.right, meets: fit.right)
                } header: {
                    SectionTitle("Your goals")
                } footer: {
                    Text("Whether each dish fits the goals you set. Which one is better is your call, not ours.")
                }
            }

            if comparison.isStale {
                Section {
                    Label(
                        "One of these figures is older than the other. Compare with that in mind.",
                        systemImage: Tokens.Symbol.stale)
                        .foregroundStyle(Tokens.Color.staleWarning)
                }
            }
        }
        .navigationTitle("Compare")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func heading(_ item: MenuItem) -> some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
            Text(item.name)
                .font(.headline)
            Text(item.chain)
                .font(.caption)
                .foregroundStyle(Tokens.Color.textSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func goalFit(_ item: MenuItem, meets: Bool) -> some View {
        LabeledContent {
            Text(meets ? "Fits" : "Does not fit")
                .foregroundStyle(meets ? Tokens.Color.textPrimary : Tokens.Color.textSecondary)
        } label: {
            Label {
                Text(item.name)
            } icon: {
                Image(systemName: meets ? "checkmark.circle" : "circle")
                    .foregroundStyle(meets ? Tokens.Color.protein : Tokens.Color.textSecondary)
            }
        }
    }
}

/// Строка одного нутриента: значение слева, значение справа, разница снизу.
private struct NutrientRow: View {

    let row: Comparison.Row

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
            Grid(horizontalSpacing: Tokens.Spacing.m) {
                GridRow {
                    Text(row.leftText)
                        .monospacedDigit()
                        .frame(maxWidth: .infinity, alignment: .leading)
                    Text(row.rightText)
                        .monospacedDigit()
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            HStack(spacing: Tokens.Spacing.s) {
                Text(row.nutrient.title)
                    .font(.caption)
                    .foregroundStyle(Tokens.Color.textSecondary)
                if let difference = row.differenceText {
                    Text(difference)
                        .font(.caption)
                        .monospacedDigit()
                        .foregroundStyle(Tokens.Color.textSecondary)
                }
            }
        }
        .padding(.vertical, Tokens.Spacing.xs)
        .accessibilityElement(children: .combine)
    }
}

#Preview {
    NavigationStack {
        ComparisonView(comparison: Comparison(
            left: MenuRepository.previewItem(name: "Big Mac"),
            right: MenuRepository.previewItem(name: "Chicken Sandwich")))
    }
}
