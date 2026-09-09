import SwiftUI

/// Иконка строки списка: цветная подложка, белый символ поверх.
///
/// Единственное место, где собирается эта пара — заменить круглую подложку
/// на квадратную со скруглением, поменять размер или белый глиф на другой
/// цвет значит один раз поправить этот файл, а не выискивать `Image` по
/// экранам. Цвет подложки — не параметр на вкус вызывающей стороны, а
/// одно из значений `Tokens.RowIconTint`, выбранное по психологии цвета
/// для смысла конкретной иконки.
struct RowIcon: View {

    let symbol: String
    let tint: Color
    var size: CGFloat = 28

    var body: some View {
        Image(systemName: symbol)
            .font(.subheadline)
            .foregroundStyle(Tokens.Color.rowIconGlyph)
            .frame(width: size, height: size)
            .background(tint, in: .rect(cornerRadius: size * 0.28))
            .accessibilityHidden(true)
    }
}

extension MenuItem.Flag {
    /// Подложка пометки — в этом файле, а не рядом с `symbol` и `title`:
    /// те не знают о SwiftUI и остаются в слое данных, а цвет — вещь чисто
    /// экранная.
    var rowIconTint: Color {
        switch self {
        case .kids: Tokens.RowIconTint.kids
        case .shareable: Tokens.RowIconTint.shareable
        case .regional: Tokens.RowIconTint.regional
        case .seasonal: Tokens.RowIconTint.seasonal
        }
    }
}

#Preview {
    List {
        Label {
            Text("Source")
        } icon: {
            RowIcon(symbol: Tokens.Symbol.source, tint: Tokens.RowIconTint.source)
        }
        Label {
            Text("Figures from")
        } icon: {
            RowIcon(symbol: Tokens.Symbol.stale, tint: Tokens.RowIconTint.freshness)
        }
        Label {
            Text("Serving")
        } icon: {
            RowIcon(symbol: Tokens.Symbol.serving, tint: Tokens.RowIconTint.serving)
        }
    }
}
