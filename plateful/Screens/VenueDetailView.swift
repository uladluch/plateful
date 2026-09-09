import MapKit
import SwiftUI

/// Что известно про конкретное заведение: адрес, часы, чем оно оснащено.
///
/// Своя карточка, а не карточка Apple, потому что данные наши: часы работы
/// сеть публикует у себя, и MapKit их не отдаёт вовсе — среди свойств
/// `MKMapItem` их нет. Зато у Apple есть то, чего нет у нас — снимки,
/// оценки и ценник, — и туда ведёт отдельная кнопка.
struct VenueDetailView: View {

    let venue: Venue
    /// `$$` — полоса по сети, а не чек этого ресторана. Разницу проговаривает
    /// подпись под разделом, иначе цифру прочтут как обещание.
    var priceBand: String?
    /// Сеть каталога — чтобы отсюда открывалось её меню. `nil`, если сети
    /// в паке нет: так бывает на запасном пути, когда точки нашла карта.
    var menuChain: MenuChain?

    @State private var mapItem: MKMapItem?
    @State private var showsMapCard = false
    @State private var lookingUp = false

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
                    LabeledContent("Address", value: venue.address)
                    if let phone = venue.phone {
                        LabeledContent("Phone", value: phone)
                    }
                    LabeledContent("Distance",
                                   value: NearbyView.distance(venue.distance))
                    if let priceBand {
                        LabeledContent("Prices", value: priceBand)
                    }
                } footer: {
                    if priceBand != nil {
                        Text("Prices are typical for the chain, not for this restaurant.")
                    }
                }

                hours(venue.hours, title: "Hours")
                hours(venue.driveThruHours, title: "Drive-thru")

                if !venue.amenities.isEmpty {
                    Section("At this location") {
                        ForEach(venue.amenities, id: \.self) { name in
                            Label(Self.amenityTitle(name),
                                  systemImage: Self.amenitySymbol(name))
                        }
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

                Section {
                    Button {
                        openInMaps()
                    } label: {
                        Label("Directions", systemImage: Tokens.Symbol.directions)
                    }
                    // Снимки, оценки и ценник «$$» рисует Apple — у нас их
                    // нет и хранить их условия Apple Maps не разрешают.
                    Button {
                        lookUpPlaceCard()
                    } label: {
                        LabeledContent {
                            if lookingUp { ProgressView() }
                        } label: {
                            Label("Photos and prices in Maps",
                                  systemImage: "map")
                        }
                    }
                    .disabled(lookingUp)
                }
        }
        .navigationTitle(venue.chain)
        .navigationBarTitleDisplayMode(.inline)
        .mapItemDetailSheet(isPresented: $showsMapCard, item: mapItem)
    }

    @ViewBuilder
    private func hours(_ week: WeekHours?, title: LocalizedStringKey) -> some View {
        if let week, !week.days.isEmpty {
            Section(title) {
                ForEach(Self.weekFromToday(), id: \.self) { index in
                    LabeledContent(Self.dayName(index)) {
                        Text(Self.dayHours(week.day(index)))
                            .monospacedDigit()
                            .foregroundStyle(Tokens.Color.textSecondary)
                    }
                }
            }
        }
    }

    /// Маршрут строит системная карта — она знает про пробки и транспорт.
    private func openInMaps() {
        let placemark = MKPlacemark(coordinate: CLLocationCoordinate2D(
            latitude: venue.latitude, longitude: venue.longitude))
        let item = MKMapItem(placemark: placemark)
        item.name = venue.chain
        item.openInMaps(launchOptions: [
            MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDefault])
    }

    /// Карточка места Apple по нашей координате.
    ///
    /// `MKMapItem` для неё нужен настоящий — собранный из координаты не
    /// несёт ни снимков, ни ценника. Поэтому спрашиваем карту про имя сети
    /// в маленьком окне вокруг точки: это один запрос и только по нажатию.
    private func lookUpPlaceCard() {
        if mapItem != nil {
            showsMapCard = true
            return
        }
        lookingUp = true
        Task {
            let request = MKLocalSearch.Request()
            request.naturalLanguageQuery = venue.chain
            request.region = MKCoordinateRegion(
                center: CLLocationCoordinate2D(latitude: venue.latitude,
                                               longitude: venue.longitude),
                latitudinalMeters: 200, longitudinalMeters: 200)
            mapItem = try? await MKLocalSearch(request: request).start().mapItems.first
            lookingUp = false
            showsMapCard = mapItem != nil
        }
    }

    // MARK: - Представление

    /// Неделя начиная с сегодняшнего дня: человек спрашивает «а сейчас?»,
    /// и понедельник первым строкой отвечает не ему.
    static func weekFromToday(now: Date = .now, calendar: Calendar = .current) -> [Int] {
        let today = (calendar.component(.weekday, from: now) - 1) % 7
        return (0..<7).map { (today + $0) % 7 }
    }

    static func dayName(_ index: Int, calendar: Calendar = .current) -> String {
        calendar.standaloneWeekdaySymbols[index % 7]
    }

    static func dayHours(_ day: WeekHours.Day?) -> String {
        guard let day else { return "Closed" }
        if day.allDay { return "Open 24 hours" }
        return "\(clock(day.opens)) – \(clock(day.closes))"
    }

    /// Минуты от полуночи → время в том виде, в каком его пишет система:
    /// 10:00 PM в США, 22:00 там, где принят двадцатичетырёхчасовой.
    static func clock(_ minutes: Int) -> String {
        var parts = DateComponents()
        parts.hour = (minutes / 60) % 24
        parts.minute = minutes % 60
        guard let date = Calendar.current.date(from: parts) else { return "" }
        return date.formatted(date: .omitted, time: .shortened)
    }

    static func amenityTitle(_ name: String) -> String {
        switch name {
        case "drive_thru": "Drive-thru"
        case "delivery": "Delivery"
        case "breakfast": "Breakfast"
        case "wifi": "Wi-Fi"
        case "mobile_ordering": "Mobile ordering"
        case "parking": "Parking"
        case "playground": "Playground"
        default: name.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }

    static func amenitySymbol(_ name: String) -> String {
        switch name {
        case "drive_thru": "car"
        case "delivery": "bicycle"
        case "breakfast": "sunrise"
        case "wifi": "wifi"
        case "mobile_ordering": "iphone"
        case "parking": "parkingsign"
        case "playground": "figure.play"
        default: "checkmark.circle"
        }
    }
}


/// Та же карточка, открытая с карты.
///
/// С булавки она приходит шитом, из списка — пушем в тот же стек, поэтому
/// навигационную обвязку добавляет обёртка, а не сама карточка: иначе
/// пуш вкладывал бы один `NavigationStack` в другой.
struct VenueDetailSheet: View {

    let venue: Venue
    var priceBand: String?
    var menuChain: MenuChain?

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VenueDetailView(venue: venue, priceBand: priceBand, menuChain: menuChain)
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Done") { dismiss() }
                    }
                }
        }
    }
}
