import MapKit
import SwiftData
import SwiftUI

/// Экран сети: «Best for you», «Full Menu», «Restaurants».
struct ChainMenuView: View {

    let chain: MenuChain

    @Environment(MenuRepository.self) private var menu
    @Query private var goals: [UserGoals]

    @State private var query = ""
    @State private var filter = MenuFilter.none
    @State private var tab = Tab.fullMenu

    /// Поиск заведений этой сети — своя копия хранилища: у экрана «Nearby»
    /// свой список сетей сразу, здесь нужна ровно одна.
    @State private var nearby = NearbyStore()
    /// Ответ без геопозиции — когда человек её не дал. Отдельно от `nearby`,
    /// потому что это другой запрос, не привязанный к разрешению системы.
    @State private var fallbackVenues: [Venue] = []
    @State private var fallbackLoaded = false

    enum Tab: String, CaseIterable, Identifiable {
        case bestForYou = "Best for you"
        case fullMenu = "Full Menu"
        case restaurants = "Restaurants"
        var id: String { rawValue }
    }

    var body: some View {
        Group {
            // Поиск и фильтр по целям имеют смысл только у полного меню:
            // на пустой пока «Best for you» и на списке заведений искать
            // блюдо нечем.
            if tab == .fullMenu {
                list
                    .searchable(text: $query, prompt: "Search \(chain.name)")
                    .toolbar {
                        MenuFilterMenu(filter: $filter, goals: goals.first)
                    }
            } else {
                list
            }
        }
    }

    private var list: some View {
        List {
            header
            segmentedControl

            switch tab {
            case .bestForYou:
                bestForYouPlaceholder
            case .fullMenu:
                fullMenuRows
            case .restaurants:
                restaurantsRows
            }
        }
        // Строки поиска ленивы: без очереди снимок начинают качать в тот
        // момент, когда строка уже показалась. Ленты разделов не ленивы и
        // просят своё сами.
        .prefetchesDishPhotos(searchResults, size: MenuItemRow.imageSize)
        // Без этого List рисует каждую Section как сгруппированную карточку
        // — тогда карточкой читается вся категория, а не позиция внутри неё.
        // .plain убирает этот фон и оставляет карточкой только ItemCard.
        .listStyle(.plain)
        // Название уже стоит в шапке контента, крупно и под маркой; в навбаре
        // оно было бы дублем. Пустой заголовок отдаёт эту строку шапке и
        // всё равно оставляет системную кнопку «Назад».
        .navigationTitle("")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var searchResults: [MenuItem] {
        guard !query.isEmpty else { return [] }
        return menu.collapsingVariants(
            filter.apply(to: menu.search(query, in: chain.name, limit: 200)))
    }

    /// Марка сети сверху, название под ней — первое, что видно на экране
    /// меню, ещё до сегмент-контрола и самих категорий.
    private var header: some View {
        VStack(spacing: Tokens.Spacing.s) {
            ChainMarkView(chain: chain.name, size: 72)
            Text(chain.name)
                .font(.title2)
                .fontWeight(.semibold)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, Tokens.Spacing.m)
        .listRowInsets(EdgeInsets())
        .listRowBackground(Color.clear)
        .listRowSeparator(.hidden)
    }

    private var segmentedControl: some View {
        Picker("Section", selection: $tab) {
            ForEach(Tab.allCases) { Text($0.rawValue).tag($0) }
        }
        .pickerStyle(.segmented)
        .listRowInsets(EdgeInsets(top: 0, leading: Tokens.Spacing.m,
                                  bottom: Tokens.Spacing.s, trailing: Tokens.Spacing.m))
        .listRowBackground(Color.clear)
        .listRowSeparator(.hidden)
    }

    // MARK: - Best for you

    /// Пока пусто: заполнится персональными подборками позже.
    private var bestForYouPlaceholder: some View {
        ContentUnavailableView("Coming soon", systemImage: "sparkles")
            .listRowInsets(EdgeInsets())
            .listRowBackground(Color.clear)
            .listRowSeparator(.hidden)
    }

    // MARK: - Full Menu

    @ViewBuilder
    private var fullMenuRows: some View {
        if query.isEmpty {
            // Витрина живёт над обычными категориями и не зависит от
            // фильтра по целям — это готовые подборки, а не то, что
            // человек сам сузил. Скрывается, как только он это сделал:
            // иначе на экране одновременно два разных «лучшее по цифре».
            if filter == .none {
                ForEach(menu.highlightShelves(for: chain.name)) { section in
                    Section {
                        itemShelf(section.items)
                    } header: {
                        sectionHeader(section.title)
                    }
                }
            }

            // Свёртка размеров — последней: фильтр по целям должен
            // видеть все размеры, иначе группа пропадёт из-за среднего.
            let sections = menu.collapsingVariants(
                filter.apply(to: menu.sections(for: chain.name)))
            if sections.isEmpty {
                noMatches
            } else {
                // Архив — не карточки: список снятых с меню позиций
                // читается плотнее строками, а разница между текущим и
                // прошлым важнее, чем свайп по нему пальцем.
                ForEach(sections.filter { !$0.isArchive }) { section in
                    Section {
                        itemShelf(section.items)
                    } header: {
                        sectionHeader(section.title)
                    }
                }

                if let archive = sections.first(where: \.isArchive) {
                    NavigationLink {
                        ArchiveMenuView(chain: chain, items: archive.items)
                    } label: {
                        LabeledContent("Archive") {
                            Text(archive.items.count.formatted())
                                .monospacedDigit()
                                .foregroundStyle(Tokens.Color.textSecondary)
                        }
                    }
                }
            }
        } else {
            if searchResults.isEmpty {
                ContentUnavailableView.search(text: query)
            } else {
                ForEach(searchResults) { item in
                    NavigationLink(value: item) {
                        MenuItemRow(item: item, showsChain: false,
                                    variants: menu.variants(of: item))
                    }
                }
            }
        }
    }

    /// Заголовок раздела — не мелкий системный header, а Headline 3, жирным,
    /// основным цветом текста: разделы здесь несут вес заголовков блюда, а
    /// не служебную подпись над списком.
    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.title3)
            .fontWeight(.bold)
            .foregroundStyle(Tokens.Color.textPrimary)
            .textCase(nil)
    }

    /// Позиции раздела как лента карточек, вбок: их пролистывают пальцем,
    /// как в App Store и Apple TV, а не вниз по строкам.
    private func itemShelf(_ items: [MenuItem]) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(alignment: .top, spacing: Tokens.Spacing.m) {
                ForEach(items) { item in
                    NavigationLink(value: item) {
                        ItemCard(item: item, variants: menu.variants(of: item))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, Tokens.Spacing.m)
            .padding(.vertical, Tokens.Spacing.xs)
        }
        .listRowInsets(EdgeInsets())
        .listRowSeparator(.hidden)
    }

    /// Пустой результат объясняется целями, а не выглядит как поломка.
    private var noMatches: some View {
        ContentUnavailableView {
            Label("Nothing fits", systemImage: "line.3.horizontal.decrease.circle")
        } description: {
            Text("No item at \(chain.name) matches your goals.")
        } actions: {
            Button("Clear filter") { filter = .none }
        }
    }

    // MARK: - Restaurants

    /// Пять ближайших заведений сети — если человек дал геопозицию.
    /// Без неё «ближайшее» не посчитать нечем, и лента становится
    /// алфавитной: не лучший ответ, но честный.
    @ViewBuilder
    private var restaurantsRows: some View {
        switch nearby.state {
        case .idle:
            restaurantsLoading
                .task { nearby.find(chains: [chain.name]) }

        case .locating, .searching:
            restaurantsLoading

        case .ready:
            if nearby.venues.isEmpty {
                restaurantsEmpty
            } else {
                venueShelf(Array(nearby.venues.prefix(5)), showsDistance: true)
            }

        case .denied, .failed:
            if fallbackLoaded {
                if fallbackVenues.isEmpty {
                    restaurantsEmpty
                } else {
                    venueShelf(fallbackVenues, showsDistance: false)
                }
            } else {
                restaurantsLoading
                    .task {
                        fallbackVenues = await Self.venuesWithoutLocation(for: chain.name)
                        fallbackLoaded = true
                    }
            }
        }
    }

    private var restaurantsLoading: some View {
        HStack(spacing: Tokens.Spacing.s) {
            ProgressView()
            Text("Finding \(chain.name) restaurants…")
                .font(.subheadline)
                .foregroundStyle(Tokens.Color.textSecondary)
        }
        .padding(.horizontal, Tokens.Spacing.m)
        .listRowInsets(EdgeInsets())
        .listRowSeparator(.hidden)
    }

    private var restaurantsEmpty: some View {
        ContentUnavailableView(
            "No locations found",
            systemImage: "mappin.slash",
            description: Text("Couldn't find a \(chain.name) restaurant."))
            .listRowInsets(EdgeInsets())
            .listRowBackground(Color.clear)
            .listRowSeparator(.hidden)
    }

    private func venueShelf(_ venues: [Venue], showsDistance: Bool) -> some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
            Text(showsDistance ? "Closest to you" : "Locations")
                .font(.subheadline)
                .foregroundStyle(Tokens.Color.textSecondary)
                .padding(.horizontal, Tokens.Spacing.m)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(alignment: .top, spacing: Tokens.Spacing.m) {
                    ForEach(venues) { venue in
                        NavigationLink {
                            VenueDetailView(venue: venue,
                                            mapItem: nearby.mapItem(for: venue),
                                            priceBand: chain.priceBand,
                                            menuChain: chain)
                        } label: {
                            VenueCard(venue: venue, showsDistance: showsDistance)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, Tokens.Spacing.m)
            }
        }
        .listRowInsets(EdgeInsets())
        .listRowSeparator(.hidden)
    }

    /// Без геопозиции спросить «рядом» нечем, но саму сеть карта может
    /// найти и без региона человека. Расстояние в таком ответе не значит
    /// ничего, поэтому сортируем по алфавиту адреса, а не по метрам.
    private static func venuesWithoutLocation(for chain: String) async -> [Venue] {
        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = chain
        // Центр контитентальных США — не «рядом с кем-то», а просто точка,
        // без которой `MKLocalSearch` не примет регион.
        request.region = MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: 39.8283, longitude: -98.5795),
            latitudinalMeters: 4_000_000, longitudinalMeters: 4_000_000)
        request.resultTypes = .pointOfInterest
        request.pointOfInterestFilter = MKPointOfInterestFilter(
            including: [.restaurant, .cafe, .bakery])

        let items: [MKMapItem]
        do {
            items = try await MKLocalSearch(request: request).start().mapItems
        } catch {
            return []
        }

        let index = NearbyCatalog([chain])
        return items.compactMap { item -> Venue? in
            guard let name = item.name, index.chain(of: name) != nil else { return nil }
            let coordinate = item.placemark.coordinate
            return Venue(
                chain: chain,
                extKey: item.identifier?.rawValue ?? "map:\(coordinate.latitude),\(coordinate.longitude)",
                latitude: coordinate.latitude, longitude: coordinate.longitude,
                address: item.placemark.title ?? "",
                phone: item.phoneNumber,
                distance: 0)
        }
        .sorted { $0.address < $1.address }
    }
}

#Preview {
    NavigationStack {
        ChainMenuView(chain: MenuChain(name: "McDonald's", itemCount: 3))
    }
    .environment(MenuRepository.preview)
}
