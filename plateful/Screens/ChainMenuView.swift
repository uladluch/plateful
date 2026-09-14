import SwiftData
import SwiftUI

/// Экран сети: «Best for you», «Full Menu», «Restaurants».
///
/// Один `List` на все вкладки, а тулбар и загрузка ресторанов — на нём, а не
/// в ветках. Раньше ради тулбара список стоял в двух ветках `if`, и смена
/// вкладки пересоздавала его вместе с прокруткой; загрузка висела на строке
/// «Finding…» и обрывалась, если уйти с вкладки, пока шёл запрос.
struct ChainMenuView: View {

    let chain: MenuChain

    @Environment(MenuRepository.self) private var menu
    /// Общее на приложение хранилище, а не своя копия: своя слала карте
    /// отдельный залп на каждое открытие сети, а карта ограничивает частоту.
    @Environment(NearbyStore.self) private var nearby
    @Query private var goals: [UserGoals]

    @State private var filter = MenuFilter.none
    @State private var tab = Tab.fullMenu
    /// Заведения сети без геопозиции — когда человек её не дал. `nil` — ещё
    /// не спрашивали.
    @State private var venuesWithoutLocation: [Venue]?

    enum Tab: String, CaseIterable, Identifiable {
        case bestForYou = "Best for you"
        case fullMenu = "Full Menu"
        case restaurants = "Restaurants"
        var id: String { rawValue }
    }

    var body: some View {
        List {
            ChainHeader(chain: chain)

            switch tab {
            case .bestForYou:
                BestForYouRows(chain: chain)
            case .fullMenu:
                FullMenuRows(chain: chain, filter: $filter)
            case .restaurants:
                RestaurantRows(chain: chain, venuesWithoutLocation: venuesWithoutLocation)
            }
        }
        // Без этого List рисует каждую Section как сгруппированную карточку
        // — тогда карточкой читается вся категория, а не позиция внутри неё.
        // .plain убирает этот фон и оставляет карточкой только ItemCard.
        .listStyle(.plain)
        // Переключатель вкладок прикреплён к верху: в длинном меню к нему
        // иначе приходилось листать обратно.
        .topBar {
            Picker("Section", selection: $tab) {
                ForEach(Tab.allCases) { Text($0.rawValue).tag($0) }
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, Tokens.Spacing.m)
            .padding(.vertical, Tokens.Spacing.s)
        }
        // Название уже стоит в шапке контента, крупно и под маркой; в навбаре
        // оно было бы дублем. Пустой заголовок отдаёт эту строку шапке и
        // всё равно оставляет системную кнопку «Назад».
        .navigationTitle("")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            // Фильтр по целям имеет смысл только у полного меню: на подборках
            // и на списке заведений фильтровать нечего.
            if tab == .fullMenu {
                ToolbarItem(placement: .primaryAction) {
                    MenuFilterMenu(filter: $filter, goals: goals.first)
                }
            }
        }
        .task(id: RestaurantsLoad(isOpen: tab == .restaurants,
                                  withoutLocation: needsSearchWithoutLocation)) {
            await loadRestaurants()
        }
    }

    private struct RestaurantsLoad: Hashable {
        let isOpen: Bool
        let withoutLocation: Bool
    }

    private var needsSearchWithoutLocation: Bool {
        switch nearby.state {
        case .denied, .failed: true
        default: false
        }
    }

    /// Поиск «рядом» — тем же залпом по всему каталогу, что у главного
    /// экрана: хранилище узнаёт его и не шлёт второй. Без геопозиции — один
    /// запрос по имени сети.
    private func loadRestaurants() async {
        guard tab == .restaurants else { return }
        if nearby.state == .idle {
            nearby.find(chains: menu.chains.map(\.name))
        }
        if needsSearchWithoutLocation, venuesWithoutLocation == nil {
            venuesWithoutLocation = await nearby.venuesWithoutLocation(for: chain.name)
        }
    }
}

/// Марка сети сверху, название под ней — первое, что видно на экране
/// меню, ещё до категорий.
private struct ChainHeader: View {

    let chain: MenuChain

    var body: some View {
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
}

// MARK: - Best for you

/// High Protein, Less Sugar, Less Calories — готовые подборки по одной
/// цифре, без фильтра и без целей: раньше жили сверху полного меню,
/// теперь у них своя вкладка, а не место над категориями.
///
/// Отдельным видом: подборки сортируют всё меню сети, и считать их стоит,
/// только когда открыта эта вкладка или сменился каталог.
private struct BestForYouRows: View {

    let chain: MenuChain

    @Environment(MenuRepository.self) private var menu

    var body: some View {
        let shelves = menu.highlightShelves(for: chain.name)
        if shelves.isEmpty {
            ContentUnavailableView("Coming soon", systemImage: "sparkles")
                .listRowInsets(EdgeInsets())
                .listRowBackground(Color.clear)
                .listRowSeparator(.hidden)
        } else {
            ForEach(shelves) { section in
                Section {
                    ItemShelf(items: section.items)
                } header: {
                    SectionTitle(section.title)
                }
            }
        }
    }
}

// MARK: - Full Menu

private struct FullMenuRows: View {

    let chain: MenuChain
    @Binding var filter: MenuFilter

    @Environment(MenuRepository.self) private var menu

    var body: some View {
        // Свёртка размеров — последней: фильтр по целям должен видеть все
        // размеры, иначе группа пропадёт из-за среднего.
        let sections = menu.collapsingVariants(
            filter.apply(to: menu.sections(for: chain.name)))

        if sections.isEmpty {
            // Пустой результат объясняется целями, а не выглядит как поломка.
            ContentUnavailableView {
                Label("Nothing fits", systemImage: "line.3.horizontal.decrease.circle")
            } description: {
                Text("No item at \(chain.name) matches your goals.")
            } actions: {
                Button("Clear filter") { filter = .none }
            }
            .listRowBackground(Color.clear)
            .listRowSeparator(.hidden)
        } else {
            // Архив — не карточки: список снятых с меню позиций читается
            // плотнее строками, а разница между текущим и прошлым важнее,
            // чем свайп по нему пальцем.
            ForEach(sections.filter { !$0.isArchive }) { section in
                Section {
                    ItemShelf(items: section.items)
                } header: {
                    SectionTitle(section.title)
                }
            }

            if let archive = sections.first(where: \.isArchive) {
                NavigationLink(value: Route.archive(chain, archive.items)) {
                    LabeledContent("Archive") {
                        Text(archive.items.count.formatted())
                            .monospacedDigit()
                            .foregroundStyle(Tokens.Color.textSecondary)
                    }
                }
            }
        }
    }
}

/// Позиции раздела как лента карточек, вбок: их пролистывают пальцем,
/// как в App Store и Apple TV, а не вниз по строкам.
///
/// Ряд ленивый: у крупных сетей в разделе под сотню позиций, и обычный
/// `HStack` создавал все карточки и запускал все загрузки снимков разом,
/// едва раздел показывался.
private struct ItemShelf: View {

    let items: [MenuItem]

    @Environment(MenuRepository.self) private var menu

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            LazyHStack(alignment: .top, spacing: Tokens.Spacing.m) {
                ForEach(items) { item in
                    NavigationLink(value: Route.item(item)) {
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
}

// MARK: - Restaurants

/// Пять ближайших заведений сети — если человек дал геопозицию.
/// Без неё «ближайшее» не посчитать нечем, и лента становится
/// алфавитной: не лучший ответ, но честный.
private struct RestaurantRows: View {

    let chain: MenuChain
    let venuesWithoutLocation: [Venue]?

    @Environment(NearbyStore.self) private var nearby

    var body: some View {
        switch nearby.state {
        case .idle, .locating:
            RestaurantsLoading(chain: chain)

        case .searching, .ready:
            let mine = nearby.venues.filter { $0.chain == chain.name }
            if !mine.isEmpty {
                VenueSection(venues: Array(mine.prefix(5)), showsDistance: true)
            } else if nearby.isSearching, !nearby.answered.contains(chain.name) {
                // Залп идёт по всему каталогу пачками: пустота до ответа
                // именно этой сети ещё не значит «рядом нет».
                RestaurantsLoading(chain: chain)
            } else {
                RestaurantsEmpty(chain: chain)
            }

        case .denied, .failed:
            if let venuesWithoutLocation {
                if venuesWithoutLocation.isEmpty {
                    RestaurantsEmpty(chain: chain)
                } else {
                    VenueSection(venues: venuesWithoutLocation, showsDistance: false)
                }
            } else {
                RestaurantsLoading(chain: chain)
            }
        }
    }
}

private struct RestaurantsLoading: View {

    let chain: MenuChain

    var body: some View {
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
}

private struct RestaurantsEmpty: View {

    let chain: MenuChain

    var body: some View {
        ContentUnavailableView(
            "No locations found",
            systemImage: "mappin.slash",
            description: Text("Couldn't find a \(chain.name) restaurant."))
            .listRowInsets(EdgeInsets())
            .listRowBackground(Color.clear)
            .listRowSeparator(.hidden)
    }
}

/// Список, а не лента: заведения читаются друг под другом, строка на
/// всю ширину — так же, как «Chains around you» на вкладке «Nearby».
/// Карточкой остаётся сама строка, а не контейнер вокруг неё.
private struct VenueSection: View {

    let venues: [Venue]
    let showsDistance: Bool

    var body: some View {
        Section {
            ForEach(venues) { venue in
                NavigationLink(value: Route.venue(venue)) {
                    VenueCard(venue: venue, showsDistance: showsDistance, layout: .row)
                }
                .listRowInsets(EdgeInsets(top: Tokens.Spacing.xs, leading: Tokens.Spacing.m,
                                          bottom: Tokens.Spacing.xs, trailing: Tokens.Spacing.m))
                .listRowSeparator(.hidden)
            }
        } header: {
            SectionTitle(showsDistance ? "Closest to you" : "Locations")
        }
    }
}

#Preview {
    NavigationStack {
        ChainMenuView(chain: MenuChain(name: "McDonald's", itemCount: 3))
            .routeDestinations()
    }
    .environment(MenuRepository.preview)
    .environment(NearbyStore())
}
