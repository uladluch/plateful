import SwiftUI

/// Заведение сети как карточка: снимок или заглушка, адрес и, если известно,
/// расстояние — тот же язык карточек, что у сети и у блюда.
///
/// Два расположения одной карточки, а не два разных вида: список
/// заведений — вертикальный, а не лента вбок, и там нужна строка на всю
/// ширину, а не квадрат из горизонтальной ленты.
struct VenueCard: View {

    enum Layout {
        /// Снимок сверху, во всю ширину карточки — для горизонтальной ленты.
        case tile
        /// Снимок слева, текст справа, во всю ширину экрана — для
        /// вертикального списка.
        case row
    }

    let venue: Venue
    /// Без геопозиции человека расстояние ничего не значит — строка просто
    /// не показывается, а не врёт нулём.
    var showsDistance: Bool = true
    var layout: Layout = .tile

    static let tileWidth: CGFloat = 160

    var body: some View {
        switch layout {
        case .tile: tile
        case .row: row
        }
    }

    private var tile: some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
            VenueImage(venue: venue, chain: venue.chain, side: Self.tileWidth)
            addressText
            distanceText
        }
        .frame(width: Self.tileWidth, alignment: .leading)
        .padding(Tokens.Spacing.s)
        .background(Tokens.Color.cardBackground, in: .rect(cornerRadius: Tokens.Radius.card))
    }

    private var row: some View {
        HStack(spacing: Tokens.Spacing.s) {
            VenueImage(venue: venue, chain: venue.chain, side: 56)
            VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                addressText
                distanceText
            }
            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(Tokens.Spacing.s)
        .background(Tokens.Color.cardBackground, in: .rect(cornerRadius: Tokens.Radius.card))
    }

    @ViewBuilder
    private var addressText: some View {
        if !venue.address.isEmpty {
            Text(venue.address)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundStyle(Tokens.Color.textPrimary)
                .lineLimit(2)
        }
    }

    @ViewBuilder
    private var distanceText: some View {
        if showsDistance {
            Text(NearbyView.distance(venue.distance))
                .font(.caption)
                .foregroundStyle(Tokens.Color.textSecondary)
                .monospacedDigit()
        }
    }
}

#Preview {
    List {
        VenueCard(venue: Venue(chain: "McDonald's", extKey: "1", latitude: 0, longitude: 0,
                               address: "123 Main St", phone: nil, distance: 420),
                  layout: .row)
        VenueCard(venue: Venue(chain: "McDonald's", extKey: "2", latitude: 0, longitude: 0,
                               address: "456 Market St", phone: nil, distance: 0),
                  showsDistance: false, layout: .row)
    }
    .listRowInsets(EdgeInsets())
    .listRowSeparator(.hidden)
}
