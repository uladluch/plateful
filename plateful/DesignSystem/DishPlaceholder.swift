import SwiftUI

/// Заглушка там, где своего снимка ещё нет.
///
/// Раньше здесь стояли общие снимки по типу блюда, снятые кем-то на телефон.
/// Они выглядели хуже, чем ничего: соседство любительского кадра с
/// официальной студийной съёмкой било по доверию ко всему списку.
///
/// Честная заглушка лучше плохой фотографии. Символ подбирается по архетипу,
/// поэтому у напитка стакан, а у десерта торт — этого хватает, чтобы строка
/// не выглядела сломанной.
nonisolated enum DishPlaceholder {

    /// Только те символы, которые в SF Symbols действительно есть и
    /// действительно похожи. Изображать сэндвич стопкой квадратов — то же
    /// враньё, что и чужая фотография не того блюда.
    static func symbol(for archetype: String?) -> String {
        switch archetype {
        case "coffee", "iced-coffee", "tea": "cup.and.saucer.fill"
        case "soda", "drink", "juice", "milk", "slush", "smoothie", "milkshake":
            "takeoutbag.and.cup.and.straw.fill"
        case "water": "waterbottle.fill"
        case "beer", "wine", "cocktail": "wineglass.fill"
        case "cake", "dessert", "cookie", "donut", "ice-cream", "yogurt":
            "birthday.cake.fill"
        case "salad", "side-vegetables", "fruit", "ingredients": "leaf.fill"
        case "seafood": "fish.fill"
        case "chips": "popcorn.fill"
        case "fries", "hash-browns", "baked-potato": "frying.pan.fill"
        default: "fork.knife"
        }
    }
}

/// Нейтральная плитка с символом.
struct DishPlaceholderView: View {

    let archetype: String?

    var body: some View {
        Image(systemName: DishPlaceholder.symbol(for: archetype))
            .font(.title3)
            .foregroundStyle(Tokens.Color.textSecondary)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(.secondarySystemFill))
            .accessibilityHidden(true)
    }
}
