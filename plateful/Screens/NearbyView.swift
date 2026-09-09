import MapKit
import SwiftData
import SwiftUI

/// Что можно съесть рядом.
///
/// Порядок экрана отвечает на вопрос, с которым его открывают: сперва какие
/// сети вокруг, потом — что в них подходит под цели. Карта сверху, потому
/// что расстояние понимают глазами, а не в метрах.
struct NearbyView: View {

    @Environment(MenuRepository.self) private var menu
    @State private var nearby = NearbyStore()
    @State private var filter = MenuFilter.none
    /// Выбранная булавка. Она же открывает карточку заведения.
    @State private var selected: Venue?

    /// Цели человека — те же, что на экране сети: фильтр один на приложение.
    @Query private var goals: [UserGoals]

    var body: some View {
        NavigationStack {
            content
                .navigationTitle("Nearby")
                .toolbar {
                    if case .ready = nearby.state {
                        ToolbarItem(placement: .primaryAction) {
                            MenuFilterMenu(filter: $filter, goals: goals.first)
                        }
                    }
                }
                .sheet(item: $selected) { venue in
                    VenueDetailSheet(venue: venue,
                                     mapItem: nearby.mapItem(for: venue),
                                     priceBand: chain(named: venue.chain).priceBand,
                                     menuChain: menuChain(for: venue))
                }
        }
        .task { find() }
    }

    private func find() {
        guard case .ready = menu.state else { return }
        nearby.find(chains: menu.catalog?.chains.map(\.name) ?? [])
    }

    @ViewBuilder
    private var content: some View {
        switch nearby.state {
        case .idle, .locating:
            ProgressView("Finding your location")

        case .searching:
            ProgressView("Looking for places nearby")

        case .denied:
            ContentUnavailableView {
                Label("Location is off", systemImage: "location.slash")
            } description: {
                Text("Plateful uses your location only to list chains around you, and only while you are on this screen.")
            } actions: {
                // Разрешение переспрашивать нельзя: система показывает
                // диалог один раз. Отправляем туда, где его меняют.
                if let settings = URL(string: UIApplication.openSettingsURLString) {
                    Link("Open Settings", destination: settings)
                }
            }

        case .failed(let message):
            ContentUnavailableView("Couldn't look around",
                                   systemImage: Tokens.Symbol.failure,
                                   description: Text(message))

        case .ready(let chains):
            if chains.isEmpty {
                ContentUnavailableView(
                    "No known chains nearby",
                    systemImage: "mappin.slash",
                    description: Text("None of the chains in this catalogue has a restaurant around you."))
            } else {
                list(chains)
            }
        }
    }

    /// Сеть каталога по имени. Имя пришло из каталога же — оно там есть.
    private func chain(named name: String) -> MenuChain {
        menu.catalog?.chains.first { $0.name == name }
            ?? MenuChain(name: name, itemCount: 0)
    }

    /// Сеть, чьё меню можно открыть из карточки заведения.
    private func menuChain(for venue: Venue) -> MenuChain? {
        menu.catalog?.chains.first { $0.name == venue.chain }
    }

    private func list(_ chains: [NearbyChain]) -> some View {
        List {
            Section {
                map
                    .frame(height: 220)
                    .listRowInsets(EdgeInsets())
            }

            Section {
                ForEach(nearby.venues) { venue in
                    NavigationLink {
                        VenueDetailView(venue: venue,
                                        mapItem: nearby.mapItem(for: venue),
                                        priceBand: chain(named: venue.chain).priceBand,
                                        menuChain: menuChain(for: venue))
                    } label: {
                        venueRow(venue)
                    }
                }
            } header: {
                SectionTitle("Restaurants around you")
            }

            Section {
                ForEach(chains) { found in
                    NavigationLink {
                        ChainMenuView(chain: chain(named: found.chain))
                    } label: {
                        row(found)
                    }
                }
            } header: {
                SectionTitle("Chains around you")
            }

            if filter.isNarrowing {
                matching(chains)
            }
        }
    }

    /// Системная карта: она уже умеет масштаб, тёмную тему и жесты.
    ///
    /// Булавка на каждое заведение, а не на сеть: четыре «Burger King»
    /// вокруг — это четыре разных ответа на вопрос «куда идти».
    private var map: some View {
        Map(selection: $selected) {
            UserAnnotation()
            ForEach(nearby.venues) { venue in
                Marker(venue.chain, systemImage: Tokens.Symbol.chain,
                       coordinate: CLLocationCoordinate2D(
                        latitude: venue.latitude, longitude: venue.longitude))
                .tag(venue)
            }
        }
        .mapControls { MapUserLocationButton() }
    }

    /// Строка заведения. Снимок слева — единственное, чем два McDonald's
    /// в четырёх кварталах друг от друга различаются с одного взгляда:
    /// имя у них одно, а расстояние читается цифрой, а не узнаётся.
    private func venueRow(_ venue: Venue) -> some View {
        LabeledContent {
            Text(Self.distance(venue.distance))
                .monospacedDigit()
                .foregroundStyle(Tokens.Color.textSecondary)
        } label: {
            HStack(spacing: Tokens.Spacing.s) {
                VenueImage(venue: venue, chain: venue.chain)
                VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                    Text(venue.chain)
                    if !venue.address.isEmpty {
                        Text(venue.address)
                            .font(.caption)
                            .foregroundStyle(Tokens.Color.textSecondary)
                    }
                }
            }
        }
    }

    private func row(_ found: NearbyChain) -> some View {
        LabeledContent {
            Text(Self.distance(found.nearest.distance))
                .monospacedDigit()
                .foregroundStyle(Tokens.Color.textSecondary)
        } label: {
            HStack(spacing: Tokens.Spacing.s) {
                ChainMarkView(chain: found.chain, size: 28)
                VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                    HStack(spacing: Tokens.Spacing.xs) {
                        Text(found.chain)
                        if let band = chain(named: found.chain).priceBand {
                            Text(band)
                                .foregroundStyle(Tokens.Color.textSecondary)
                        }
                    }
                    Text(subtitle(for: found))
                        .font(.caption)
                        .foregroundStyle(Tokens.Color.textSecondary)
                }
            }
        }
    }

    private func subtitle(for found: NearbyChain) -> String {
        let address = found.nearest.address
        guard found.venues > 1 else { return address }
        return address.isEmpty
            ? "\(found.venues) nearby"
            : "\(address) · \(found.venues) nearby"
    }

    /// Блюда под цель — из того, что рядом, а не из всего каталога.
    @ViewBuilder
    private func matching(_ chains: [NearbyChain]) -> some View {
        let items = filter.apply(to: chains.flatMap {
            menu.catalog?.items(in: $0.chain) ?? []
        })

        Section {
            if items.isEmpty {
                Text("Nothing on these menus fits.")
                    .foregroundStyle(Tokens.Color.textSecondary)
            } else {
                ForEach(items.prefix(30)) { item in
                    NavigationLink {
                        ItemDetailView(item: item)
                    } label: {
                        MenuItemRow(item: item, showsChain: true)
                    }
                }
            }
        } header: {
            SectionTitle("Fits your goals nearby")
        }
    }

    /// Расстояние через `Measurement`, чтобы мили и километры выбирала
    /// система: приложение для США, но телефон бывает настроен иначе.
    static func distance(_ meters: Double) -> String {
        Measurement(value: meters, unit: UnitLength.meters)
            .formatted(.measurement(width: .abbreviated,
                                    usage: .road,
                                    numberFormatStyle: .number.precision(.fractionLength(0...1))))
    }
}

#Preview {
    NearbyView().environment(MenuRepository.preview)
}
