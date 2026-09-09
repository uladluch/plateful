import MapKit
import SwiftUI

/// Что известно про конкретное заведение: где оно и как выглядит.
///
/// Данных здесь ровно столько, сколько отдаёт карта: адрес, телефон,
/// расстояние. Часы, снимки, оценки и ценник живут в карточке места Apple —
/// она в одном нажатии и рисуется системой, а не нами.
struct VenueDetailView: View {

    let venue: Venue
    /// Объект карты — для её карточки места и маршрута.
    var mapItem: MKMapItem?
    /// `$$` — полоса по сети, а не чек этого ресторана. Разницу проговаривает
    /// подпись под разделом, иначе цифру прочтут как обещание.
    var priceBand: String?
    /// Сеть каталога — чтобы отсюда открывалось её меню.
    var menuChain: MenuChain?

    @State private var showsMapCard = false

    var body: some View {
        List {
            Section {
                // Как это выглядит: вид с улицы или спутник. Ради того,
                // чтобы этот ресторан отличался от следующего.
                VenueImage(venue: venue, chain: venue.chain, side: 220)
                    .frame(maxWidth: .infinity)
                    .listRowInsets(EdgeInsets())
            }

            Section {
                if !venue.address.isEmpty {
                    LabeledContent("Address", value: venue.address)
                }
                if let phone = venue.phone {
                    LabeledContent("Phone", value: phone)
                }
                // Ноль — это «неизвестно», а не «вплотную»: карточки без
                // геопозиции человека получают заведение без расстояния.
                if venue.distance > 0 {
                    LabeledContent("Distance",
                                   value: NearbyView.distance(venue.distance))
                }
                if let priceBand {
                    LabeledContent("Prices", value: priceBand)
                }
            } footer: {
                if priceBand != nil {
                    Text("Prices are typical for the chain, not for this restaurant.")
                }
            }

            if let menuChain {
                Section {
                    NavigationLink {
                        ChainMenuView(chain: menuChain)
                    } label: {
                        Label("See the menu", systemImage: Tokens.Symbol.chain)
                    }
                }
            }

            if let mapItem {
                Section {
                    Button {
                        showsMapCard = true
                    } label: {
                        Label("Hours, photos and more in Maps", systemImage: "map")
                    }
                    Button {
                        mapItem.openInMaps(launchOptions: [
                            MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDefault])
                    } label: {
                        Label("Directions", systemImage: Tokens.Symbol.directions)
                    }
                }
            }
        }
        .navigationTitle(venue.chain)
        .navigationBarTitleDisplayMode(.inline)
        .mapItemDetailSheet(isPresented: $showsMapCard, item: mapItem)
    }
}

/// Та же карточка, открытая с карты.
///
/// С булавки она приходит шитом, из списка — пушем в тот же стек, поэтому
/// навигационную обвязку добавляет обёртка, а не сама карточка: иначе
/// пуш вкладывал бы один `NavigationStack` в другой.
struct VenueDetailSheet: View {

    let venue: Venue
    var mapItem: MKMapItem?
    var priceBand: String?
    var menuChain: MenuChain?

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VenueDetailView(venue: venue, mapItem: mapItem,
                            priceBand: priceBand, menuChain: menuChain)
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Done") { dismiss() }
                    }
                }
        }
    }
}
