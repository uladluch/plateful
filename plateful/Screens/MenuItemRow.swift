import SwiftUI

/// Строка списка: название, калории и белок.
///
/// Системной строки «название + два числа справа» нет, поэтому строка своя —
/// но собрана из `LabeledContent` и системных стилей, чтобы отступы и
/// поведение при Dynamic Type остались как у списка.
struct MenuItemRow: View {

    let item: MenuItem
    let showsChain: Bool

    /// Варианты одного блюда. Непусто — строка представляет всю группу:
    /// название без варианта, числа диапазоном. Четыре карточки колы подряд
    /// не помогают выбрать, а мешают.
    var variants: [MenuItem] = []

    private var isGroup: Bool { variants.count > 1 }

    private var title: String { isGroup ? item.baseName : item.name }

    private var calories: String {
        isGroup ? variants.calorieRangeText : item.calorieText
    }

    private var protein: String {
        isGroup ? variants.proteinRangeText : item.proteinText
    }

    /// Подпись под названием. Собирается из того, что верно для этой строки:
    /// сеть — когда список смешанный, «archived» — когда блюда больше нет,
    /// число размеров — когда строка представляет группу.
    private var subtitle: String? {
        var parts: [String] = []
        if showsChain { parts.append(item.chain) }
        if item.isOffMenu { parts.append(showsChain ? "archived" : "Archived") }
        if isGroup {
            // «4 sizes» и «3 options» — разные обещания: первое про
            // количество, второе про состав.
            let kind = item.variant?.kind == .option ? "options" : "sizes"
            parts.append("\(variants.count) \(kind)")
        }
        return parts.isEmpty ? nil : parts.joined(separator: " · ")
    }

    var body: some View {
        LabeledContent {
            VStack(alignment: .trailing, spacing: Tokens.Spacing.xs) {
                Text(calories)
                    .font(.body)
                    .monospacedDigit()
                Text(protein)
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
                    Text(title)
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
