import SwiftUI

/// Снимок блюда по его архетипу.
///
/// Пока набор изображений не заведён, вью не рисует ничего — пустых серых
/// прямоугольников в списке быть не должно. Как только ассеты появятся,
/// они подхватятся сами: имя ассета совпадает с архетипом из пака.
struct DishImage: View {

    let item: MenuItem
    var size: CGFloat = 44

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
        .frame(width: size, height: size)
        .clipShape(.rect(cornerRadius: Tokens.Radius.image))
        .accessibilityHidden(true)
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
