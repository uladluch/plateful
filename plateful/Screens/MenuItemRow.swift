import SwiftUI

/// Строка списка: название, калории и белок.
///
/// Системной строки «название + два числа справа» нет, поэтому строка своя —
/// но собрана из `LabeledContent` и системных стилей, чтобы отступы и
/// поведение при Dynamic Type остались как у списка.
struct MenuItemRow: View {

    let item: MenuItem
    let showsChain: Bool

    var body: some View {
        LabeledContent {
            VStack(alignment: .trailing, spacing: Tokens.Spacing.xs) {
                Text(item.calorieText)
                    .font(.body)
                    .monospacedDigit()
                Text(item.proteinText)
                    .font(.caption)
                    .foregroundStyle(Tokens.Color.textSecondary)
                    .monospacedDigit()
            }
        } label: {
            HStack(spacing: Tokens.Spacing.s) {
                if showsChain {
                    ChainMarkView(chain: item.chain, size: 26)
                }
                VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                    Text(item.name)
                    if showsChain {
                        Text(item.chain)
                            .font(.caption)
                            .foregroundStyle(Tokens.Color.textSecondary)
                    }
                }
            }
        }
    }
}
