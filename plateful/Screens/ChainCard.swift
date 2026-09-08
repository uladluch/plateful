import SwiftUI

/// Карточка сети: марка сверху, название, число позиций.
///
/// Системной карточки-плитки нет — есть только `List`/`Form` со строками.
/// Здесь она собрана вручную из `VStack` на `Tokens.Color.cardBackground` в
/// сетке `LazyVGrid`, но сохраняет системные шрифты, отступы и скругление,
/// принятое для карточек на сгруппированном фоне.
struct ChainCard: View {

    let chain: MenuChain

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
            ChainMarkView(chain: chain.name, size: 44)

            VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                Text(chain.name)
                    .font(.headline)
                    .lineLimit(2)
                    .foregroundStyle(Tokens.Color.textPrimary)

                Text("\(chain.itemCount.formatted()) \(chain.itemCount == 1 ? "item" : "items")")
                    .font(.subheadline)
                    .foregroundStyle(Tokens.Color.textSecondary)
                    .monospacedDigit()
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(Tokens.Spacing.m)
        .background(Tokens.Color.cardBackground, in: .rect(cornerRadius: Tokens.Radius.card))
    }
}

#Preview {
    ScrollView {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 150), spacing: Tokens.Spacing.m)],
                  spacing: Tokens.Spacing.m) {
            ChainCard(chain: MenuChain(name: "Chick-Fil-A", itemCount: 101))
            ChainCard(chain: MenuChain(name: "McDonald's", itemCount: 223))
            ChainCard(chain: MenuChain(name: "Starbucks", itemCount: 566))
        }
        .padding()
    }
}
