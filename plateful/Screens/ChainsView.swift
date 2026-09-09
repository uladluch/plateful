import CoreLocation
import SwiftUI

/// Корневой экран: сетки сетей и поиск по всему каталогу.
///
/// Первое, что видит человек, — уже полезно: ни онбординга, ни аккаунта,
/// ни пейволла. Это и есть позиционирование против всей категории. Поиск —
/// `.searchable` прямо здесь, а не отдельная вкладка: искать по каталогу
/// и листать его — один и тот же режим экрана, а не два разных места.
struct ChainsView: View {

    @Environment(MenuRepository.self) private var menu
    @State private var query = ""

    /// Своя копия, не общая с вкладкой «Nearby»: витрина здесь — тизер,
    /// полный список с картой и часами остаётся её работой.
    @State private var nearby = NearbyStore()

    var body: some View {
        NavigationStack {
            content
                .navigationTitle("Discovery")
                .navigationBarTitleDisplayMode(.inline)
                .searchable(text: $query, prompt: "Search chains and dishes")
                // На стабильном корне стека, а не внутри chainList/searchResults:
                // объявление внутри if/switch однажды теряется при повторном
                // рендере, и вторая попытка открыть сеть перестаёт находить
                // назначение — тот самый баг с «NavigationLink cannot be
                // activated» после возврата назад.
                .navigationDestination(for: MenuChain.self) { ChainMenuView(chain: $0) }
                .navigationDestination(for: MenuItem.self) { ItemDetailView(item: $0) }
                .toolbar {
                    ToolbarItem(placement: .primaryAction) {
                        NavigationLink {
                            NearbyView()
                        } label: {
                            Label("Nearby", systemImage: "location")
                        }
                    }
                }
        }
    }

    @ViewBuilder
    private var content: some View {
        switch menu.state {
        case .loading:
            ProgressView("Loading menus")

        case .failed(let message):
            ContentUnavailableView(
                "Menus unavailable",
                systemImage: Tokens.Symbol.failure,
                description: Text(message))

        case .ready:
            if query.isEmpty {
                chainList
            } else {
                searchResults
            }
        }
    }

    /// Две колонки минимум, больше — на широком экране: тот же приём, что
    /// в системных плиточных списках (Музыка, Погода).
    private static let columns = [GridItem(.adaptive(minimum: 150), spacing: Tokens.Spacing.m)]

    private var chainList: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Spacing.m) {
                nearbySection

                LazyVGrid(columns: Self.columns, spacing: Tokens.Spacing.m) {
                    ForEach(menu.chains) { chain in
                        NavigationLink(value: chain) {
                            ChainCard(chain: chain)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, Tokens.Spacing.m)
            }
            .padding(.vertical, Tokens.Spacing.m)
        }
        // Проверка обновлений сама идёт при запуске; жест нужен тем, кто
        // увидел устаревшее число и хочет проверить прямо сейчас.
        .refreshable { await menu.checkForUpdate() }
        // Разрешение не переспрашиваем: если человек уже разрешил геопозицию
        // на вкладке «Nearby», витрина подхватывает её молча. Если ещё нет —
        // только карточка-приглашение, диалог показывается по её тапу, а не
        // здесь, при открытии главного экрана.
        .task { autoLoadNearbyIfAuthorized() }
    }

    /// «Рядом» — витрина в одну строку: сети, а не заведения с адресом и
    /// часами, полный разбор остаётся за вкладкой «Nearby». Отказ и ошибка
    /// молчат — это необязательная секция, а не тело экрана, приставать
    /// на главном экране с ними незачем.
    @ViewBuilder
    private var nearbySection: some View {
        switch nearby.state {
        case .idle:
            if CLLocationManager().authorizationStatus == .notDetermined {
                nearbyPrompt
            }
        case .locating, .searching:
            nearbyLoading
        case .ready(let chains):
            if !chains.isEmpty {
                nearbyShelf(chains)
            }
        case .denied, .failed:
            EmptyView()
        }
    }

    private var nearbyPrompt: some View {
        Button {
            nearby.find(chains: menu.chains.map(\.name))
        } label: {
            HStack(spacing: Tokens.Spacing.s) {
                Image(systemName: "location.circle.fill")
                    .foregroundStyle(Tokens.Color.accent)
                VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                    Text("Restaurants Near Me")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundStyle(Tokens.Color.textPrimary)
                    Text("See which chains are around you right now.")
                        .font(.caption)
                        .foregroundStyle(Tokens.Color.textSecondary)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundStyle(Tokens.Color.textSecondary)
            }
            .padding(Tokens.Spacing.m)
            .background(Tokens.Color.cardBackground, in: .rect(cornerRadius: Tokens.Radius.card))
        }
        .buttonStyle(.plain)
        .padding(.horizontal, Tokens.Spacing.m)
    }

    private var nearbyLoading: some View {
        HStack(spacing: Tokens.Spacing.s) {
            ProgressView()
            Text("Finding restaurants near you…")
                .font(.subheadline)
                .foregroundStyle(Tokens.Color.textSecondary)
        }
        .padding(.horizontal, Tokens.Spacing.m)
    }

    private func nearbyShelf(_ chains: [NearbyChain]) -> some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
            SectionTitle("Restaurants Near Me")
                .padding(.horizontal, Tokens.Spacing.m)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(alignment: .top, spacing: Tokens.Spacing.m) {
                    ForEach(chains) { found in
                        if let chain = menu.chain(named: found.chain) {
                            NavigationLink(value: chain) {
                                ChainCard(chain: chain)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .padding(.horizontal, Tokens.Spacing.m)
            }
        }
    }

    /// Спрашивать заново нельзя — только подхватить решение, которое уже
    /// стоит в системе (например, человек разрешил на вкладке «Nearby»).
    private func autoLoadNearbyIfAuthorized() {
        guard nearby.state == .idle, !menu.chains.isEmpty else { return }
        let status = CLLocationManager().authorizationStatus
        guard status == .authorizedWhenInUse || status == .authorizedAlways else { return }
        nearby.find(chains: menu.chains.map(\.name))
    }

    /// Запрос ищет сразу по всем сетям, а не по одной открытой.
    @ViewBuilder
    private var searchResults: some View {
        let results = menu.collapsingVariants(menu.search(query))
        if results.isEmpty {
            ContentUnavailableView.search(text: query)
        } else {
            List(results) { item in
                NavigationLink(value: item) {
                    MenuItemRow(item: item, showsChain: true,
                                variants: menu.variants(of: item))
                }
            }
        }
    }
}

#Preview {
    ChainsView().environment(MenuRepository.preview)
}
