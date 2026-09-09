import SwiftUI

/// Заведение сети как карточка: снимок или заглушка сверху, адрес и,
/// если известно, расстояние — тот же язык карточек, что у сети и у блюда.
struct VenueCard: View {

    let venue: Venue
    /// Без геопозиции человека расстояние ничего не значит — строка просто
    /// не показывается, а не врёт нулём.
    var showsDistance: Bool = true

    static let width: CGFloat = 160

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
            VenueImage(venue: venue, chain: venue.chain, side: Self.width)

            if !venue.address.isEmpty {
                Text(venue.address)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundStyle(Tokens.Color.textPrimary)
                    .lineLimit(2)
            }

            if showsDistance {
                Text(NearbyView.distance(venue.distance))
                    .font(.caption)
                    .foregroundStyle(Tokens.Color.textSecondary)
                    .monospacedDigit()
            }
        }
        .frame(width: Self.width, alignment: .leading)
        .padding(Tokens.Spacing.s)
        .background(Tokens.Color.cardBackground, in: .rect(cornerRadius: Tokens.Radius.card))
    }
}

#Preview {
    ScrollView(.horizontal) {
        HStack(spacing: Tokens.Spacing.m) {
            VenueCard(venue: Venue(chain: "McDonald's", extKey: "1", latitude: 0, longitude: 0,
                                   address: "123 Main St", phone: nil, distance: 420))
            VenueCard(venue: Venue(chain: "McDonald's", extKey: "2", latitude: 0, longitude: 0,
                                   address: "456 Market St", phone: nil, distance: 0),
                      showsDistance: false)
        }
        .padding()
    }
}
