import SwiftUI

/// Как выглядит это заведение — чтобы отличить его от следующего.
///
/// Пока кадра нет, на его месте стоит значок сети: строка не должна
/// прыгать, а у части точек кадра не будет вовсе — ни вида с улицы, ни
/// разборчивого спутника за городом.
struct VenueImage: View {

    @Environment(\.displayScale) private var displayScale

    let venue: Venue
    var chain: String
    var side: CGFloat = 56

    @State private var image: UIImage?

    /// Просим кадр в пикселях экрана: на 3x квадрат в 56 точек — это 168.
    private var pixels: CGFloat { side * displayScale }

    var body: some View {
        Group {
            if let image {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
            } else {
                ChainMarkView(chain: chain, size: side)
            }
        }
        .frame(width: side, height: side)
        .clipShape(RoundedRectangle(cornerRadius: Tokens.Radius.image,
                                    style: .continuous))
        .accessibilityHidden(true)
        .task(id: venue.id) {
            // Уже в памяти — ставим сразу, без мигания заглушкой.
            if let ready = VenueSnapshot.shared.cached(venue, side: pixels) {
                image = ready
                return
            }
            image = await VenueSnapshot.shared.image(for: venue, side: pixels)
        }
    }
}
