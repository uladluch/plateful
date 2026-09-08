import SwiftUI

/// Снимок блюда, а где его нет — нейтральная заглушка.
///
/// Показываем только настоящие снимки: официальную съёмку сети или
/// свободно лицензированный кадр именно этого блюда. Общих картинок
/// «примерно такой бургер» больше нет — они обесценивали и те снимки,
/// которые настоящие.
struct DishImage: View {

    let item: MenuItem
    var size: CGFloat = 44
    /// Во всю ширину и без скруглений — для шапки карточки блюда.
    var isHero: Bool = false

    var body: some View {
        Group {
            if let photo = item.photo {
                AsyncImage(url: photo.url) { image in
                    if photo.fitsInside {
                        image.resizable()
                            .scaledToFit()
                            .padding(size * 0.06)
                            .background(Tokens.Color.photoBackground)
                    } else {
                        // Кадр без полей и так покрывает весь размер, но
                        // прозрачные углы или недогрузившийся угол снимка не
                        // должны показать системный серый под ним.
                        image.resizable().scaledToFill()
                            .background(Tokens.Color.photoBackground)
                    }
                } placeholder: {
                    // Пока снимок качается — та же заглушка, что и без него:
                    // строка списка не должна прыгать.
                    DishPlaceholderView(archetype: item.image)
                }
            } else {
                DishPlaceholderView(archetype: item.image)
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
}
