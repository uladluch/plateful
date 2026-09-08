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
                    description: Text("There are places around you, but none of them is a chain in this catalogue."))
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

    private func list(_ chains: [NearbyChain]) -> some View {
        List {
            Section {
                map(chains)
                    .frame(height: 200)
                    .listRowInsets(EdgeInsets())
            }

            Section("Chains around you") {
                ForEach(chains) { found in
                    NavigationLink {
                        ChainMenuView(chain: chain(named: found.chain))
                    } label: {
                        row(found)
                    }
                }
            }

            if filter.isNarrowing {
                matching(chains)
            }
        }
    }

    /// Системная карта: она уже умеет масштаб, тёмную тему и жесты.
    private func map(_ chains: [NearbyChain]) -> some View {
        Map {
            UserAnnotation()
            ForEach(chains) { found in
                Marker(found.chain, systemImage: Tokens.Symbol.chain,
                       coordinate: CLLocationCoordinate2D(
                        latitude: found.nearest.latitude,
                        longitude: found.nearest.longitude))
            }
        }
        .mapControls { MapUserLocationButton() }
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
                    Text(found.chain)
                    if let address = found.nearest.address {
                        Text(found.venues > 1
                             ? "\(address) · \(found.venues) nearby"
                             : address)
                            .font(.caption)
                            .foregroundStyle(Tokens.Color.textSecondary)
                    }
                }
            }
        }
    }

    /// Блюда под цель — из того, что рядом, а не из всего каталога.
    @ViewBuilder
    private func matching(_ chains: [NearbyChain]) -> some View {
        let items = filter.apply(to: chains.flatMap {
            menu.catalog?.items(in: $0.chain) ?? []
        })

        Section("Fits your goals nearby") {
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
