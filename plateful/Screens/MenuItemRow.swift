import SwiftUI

/// Строка списка: название, калории и белок.
///
/// Системной строки «название + два числа справа» нет, поэтому строка своя —
/// но собрана из `LabeledContent` и системных стилей, чтобы отступы и
/// поведение при Dynamic Type остались как у списка.
struct MenuItemRow: View {

    let item: MenuItem
    let showsChain: Bool

    private var subtitle: String? {
        switch (item.isOffMenu, showsChain) {
        case (true, true): "\(item.chain) · archived"
        case (true, false): "Archived"
        case (false, true): item.chain
        case (false, false): nil
        }
    }

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
                DishImage(item: item, size: 56)
                if showsChain {
                    ChainMarkView(chain: item.chain, size: 22)
                }
                VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                    Text(item.name)
                        .foregroundStyle(item.isOffMenu
                                         ? Tokens.Color.textSecondary
                                         : Tokens.Color.textPrimary)
                    // Пометка нужна именно в списке: иначе человек узнаёт,
                    // что блюдо снято, уже открыв карточку.
                    if let subtitle {
                        Text(subtitle)
                            .font(.caption)
                            .foregroundStyle(item.isOffMenu
                                             ? Tokens.Color.staleWarning
                                             : Tokens.Color.textSecondary)
                    }
                }
            }
        }
    }
}
