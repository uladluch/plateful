import MapKit
import SwiftData
import SwiftUI

/// Что можно съесть рядом.
///
/// Порядок экрана отвечает на вопрос, с которым его открывают: сперва какие
/// сети вокруг, потом — что в них подходит под цели. Карта сверху, потому
/// что расстояние понимают глазами, а не в метрах.
///
/// Своего `NavigationStack` у экрана нет: его открывают пушем из стека
/// «Discovery», и второй стек внутри первого ломал переходы — карточка блюда,
/// открытая отсюда, не находила назначения.
struct NearbyView: View {

    @Environment(MenuRepository.self) private var menu
    /// Общее на приложение: ответ, полученный главным экраном, видит и
    /// вкладка «рядом» — без второго залпа запросов к карте.
    @Environment(NearbyStore.self) private var nearby
    @State private var filter = MenuFilter.none
    /// Выбранная булавка. Она же открывает карточку заведения.
    @State private var selected: Venue?

    /// Цели человека — те же, что на экране сети: фильтр один на приложение.
    @Query private var goals: [UserGoals]

    var body: some View {
        content
            .navigationTitle("Nearby")
            .toolbar {
                if case .ready = nearby.state {
                    ToolbarItem(placement: .primaryAction) {
                        MenuFilterMenu(filter: $filter, goals: goals.first)
                    }
                }
            }
            .sheet(item: $selected) { VenueDetailSheet(venue: $0) }
            .task { find() }
    }

    private func find() {
        guard case .ready = menu.state else { return }
        nearby.find(chains: menu.chains.map(\.name))
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
                // Карта над списком, а не строкой в нём: внутри `List` её
                // перетаскивание спорило с прокруткой.
                VStack(spacing: 0) {
                    NearbyMap(selection: $selected)
                        .containerRelativeFrame(.vertical) { height, _ in height * 0.3 }
                    NearbyList(chains: chains, filter: filter)
                }
            }
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

/// Системная карта: она уже умеет масштаб, тёмную тему и жесты.
///
/// Булавка на каждое заведение, а не на сеть: четыре «Burger King»
/// вокруг — это четыре разных ответа на вопрос «куда идти».
private struct NearbyMap: View {

    @Binding var selection: Venue?
    @Environment(NearbyStore.self) private var nearby

    var body: some View {
        Map(selection: $selection) {
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
}

private struct NearbyList: View {

    let chains: [NearbyChain]
    let filter: MenuFilter

    @Environment(MenuRepository.self) private var menu
    @Environment(NearbyStore.self) private var nearby

    var body: some View {
        List {
            Section {
                ForEach(nearby.venues) { venue in
                    NavigationLink(value: Route.venue(venue)) {
                        NearbyVenueRow(venue: venue)
                    }
                }
            } header: {
                SectionTitle("Restaurants around you")
            }

            Section {
                ForEach(chains) { found in
                    // Имя пришло из каталога же — сеть там есть.
                    if let chain = menu.chain(named: found.chain) {
                        NavigationLink(value: Route.chain(chain)) {
                            NearbyChainRow(found: found, priceBand: chain.priceBand)
                        }
                    }
                }
            } header: {
                SectionTitle("Chains around you")
            }

            if filter.isNarrowing {
                FitsGoalsSection(chains: chains, filter: filter)
            }
        }
    }
}

/// Строка заведения. Снимок слева — единственное, чем два McDonald's
/// в четырёх кварталах друг от друга различаются с одного взгляда:
/// имя у них одно, а расстояние читается цифрой, а не узнаётся.
private struct NearbyVenueRow: View {

    let venue: Venue

    var body: some View {
        LabeledContent {
            Text(NearbyView.distance(venue.distance))
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
}

private struct NearbyChainRow: View {

    let found: NearbyChain
    let priceBand: String?

    var body: some View {
        LabeledContent {
            Text(NearbyView.distance(found.nearest.distance))
                .monospacedDigit()
                .foregroundStyle(Tokens.Color.textSecondary)
        } label: {
            HStack(spacing: Tokens.Spacing.s) {
                ChainMarkView(chain: found.chain, size: 28)
                VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                    HStack(spacing: Tokens.Spacing.xs) {
                        Text(found.chain)
                        if let priceBand {
                            Text(priceBand)
                                .foregroundStyle(Tokens.Color.textSecondary)
                        }
                    }
                    Text(subtitle)
                        .font(.caption)
                        .foregroundStyle(Tokens.Color.textSecondary)
                }
            }
        }
    }

    private var subtitle: String {
        let address = found.nearest.address
        guard found.venues > 1 else { return address }
        return address.isEmpty
            ? "\(found.venues) nearby"
            : "\(address) · \(found.venues) nearby"
    }
}

/// Блюда под цель — из того, что рядом, а не из всего каталога.
///
/// Отдельным видом: подборка — проход по меню всех сетей вокруг, и считать
/// его стоит, только когда поменялись сами сети или фильтр, а не на выбор
/// булавки.
private struct FitsGoalsSection: View {

    let chains: [NearbyChain]
    let filter: MenuFilter

    @Environment(MenuRepository.self) private var menu

    var body: some View {
        let items = filter.apply(to: chains.flatMap { menu.items(in: $0.chain) })

        Section {
            if items.isEmpty {
                Text("Nothing on these menus fits.")
                    .foregroundStyle(Tokens.Color.textSecondary)
            } else {
                ForEach(items.prefix(30)) { item in
                    NavigationLink(value: Route.item(item)) {
                        MenuItemRow(item: item, showsChain: true)
                    }
                }
            }
        } header: {
            SectionTitle("Fits your goals nearby")
        }
    }
}

#Preview {
    NavigationStack {
        NearbyView().routeDestinations()
    }
    .environment(MenuRepository.preview)
    .environment(NearbyStore())
}
