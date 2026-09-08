import SwiftUI

/// Карточка блюда для горизонтальной ленты раздела: снимок сверху,
/// название и числа снизу.
///
/// Системной карточки нет, только строки списка — здесь она собрана вручную
/// на `Tokens.Color.cardBackground`, той же, что и у карточки сети, чтобы
/// оба уровня каталога выглядели одной системой.
struct ItemCard: View {

    let item: MenuItem

    /// Варианты одного блюда. Непусто — карточка представляет всю группу:
    /// название без варианта, числа диапазоном.
    var variants: [MenuItem] = []

    private var isGroup: Bool { variants.count > 1 }
    private var title: String { isGroup ? item.baseName : item.name }
    private var calories: String { isGroup ? variants.calorieRangeText : item.calorieText }
    private var protein: String { isGroup ? variants.proteinRangeText : item.proteinText }

    static let width: CGFloat = 140

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
            DishImage(item: item, size: Self.width)

            Text(title)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundStyle(Tokens.Color.textPrimary)
                .lineLimit(2)
                .frame(height: 36, alignment: .top)

            HStack(spacing: Tokens.Spacing.xs) {
                Text(calories)
                    .monospacedDigit()
                Text("cal")
                    .foregroundStyle(Tokens.Color.textSecondary)
                Text("·")
                    .foregroundStyle(Tokens.Color.textSecondary)
                Text(protein)
                    .monospacedDigit()
                    .foregroundStyle(Tokens.Color.textSecondary)
            }
            .font(.caption)
        }
        .frame(width: Self.width, alignment: .leading)
        .padding(Tokens.Spacing.s)
        .background(Tokens.Color.cardBackground, in: .rect(cornerRadius: Tokens.Radius.card))
    }
}

#Preview {
    ScrollView(.horizontal) {
        HStack(spacing: Tokens.Spacing.m) {
            ItemCard(item: MenuRepository.previewItem(name: "Big Mac"))
        }
        .padding()
    }
}
