import SwiftUI

/// Снимок блюда по его архетипу.
///
/// Пока набор изображений не заведён, вью не рисует ничего — пустых серых
/// прямоугольников в списке быть не должно. Как только ассеты появятся,
/// они подхватятся сами: имя ассета совпадает с архетипом из пака.
struct DishImage: View {

    let item: MenuItem
    var size: CGFloat = 44
    /// Во всю ширину и без скруглений — для шапки карточки блюда.
    var isHero: Bool = false

    /// Префикс имён в каталоге ассетов: `dish-cheeseburger`, `dish-fries`…
    static let assetPrefix = "dish-"

    private var assetName: String? {
        guard let image = item.image else { return nil }
        let name = Self.assetPrefix + image
        return UIImage(named: name) == nil ? nil : name
    }

    var body: some View {
        Group {
            if let photo = item.photo {
                // Пока снимок блюда качается — показываем картинку по
                // архетипу, а не пустоту: строка списка не должна прыгать.
                AsyncImage(url: photo.url) { image in
                    image.resizable().scaledToFill()
                } placeholder: {
                    archetypeImage
                }
            } else {
                archetypeImage
            }
        }
        .modifier(Shape(size: size, isHero: isHero))
        .accessibilityHidden(true)
    }

    /// Шапка тянется по ширине списка, строка остаётся квадратной.
    private struct Shape: ViewModifier {
        let size: CGFloat
        let isHero: Bool

        func body(content: Content) -> some View {
            if isHero {
                content
                    .frame(maxWidth: .infinity)
                    .frame(height: size)
                    .clipped()
            } else {
                content
                    .frame(width: size, height: size)
                    .clipShape(.rect(cornerRadius: Tokens.Radius.image))
            }
        }
    }

    @ViewBuilder
    private var archetypeImage: some View {
        if let assetName {
            Image(assetName).resizable().scaledToFill()
        } else {
            Color(.secondarySystemFill)
        }
    }
}
