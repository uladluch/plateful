import SwiftUI

/// Корневой экран: сетки сетей и поиск по всему каталогу.
///
/// Первое, что видит человек, — уже полезно: ни онбординга, ни аккаунта,
/// ни пейволла. Это и есть позиционирование против всей категории. Поиск —
/// `.searchable` прямо здесь, а не отдельная вкладка: искать по каталогу
/// и листать его — один и тот же режим экрана, а не два разных места.
struct ChainsView: View {

    @Binding var path: [Route]

    @Environment(MenuRepository.self) private var menu
    @State private var query = ""

    var body: some View {
        NavigationStack(path: $path) {
            content
                .navigationTitle("Discovery")
                .navigationBarTitleDisplayMode(.inline)
                .searchable(text: $query, prompt: "Search chains and dishes")
                // На стабильном корне стека, а не внутри веток ниже:
                // объявление внутри if/switch однажды теряется при повторном
                // рендере, и вторая попытка открыть сеть перестаёт находить
                // назначение — тот самый баг с «NavigationLink cannot be
                // activated» после возврата назад.
                .routeDestinations()
                .toolbar {
                    ToolbarItem(placement: .primaryAction) {
                        Button("Nearby", systemImage: "location") {
                            path.append(.nearby)
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
                ChainGrid()
            } else {
                SearchResults(query: query)
            }
        }
    }
}

/// Все сети плитками, над ними — витрина «рядом».
private struct ChainGrid: View {

    @Environment(MenuRepository.self) private var menu
    /// Общее на приложение: ответ, полученный главным экраном, видит и
    /// вкладка «рядом» — без второго залпа запросов к карте.
    @Environment(NearbyStore.self) private var nearby

    /// Две колонки минимум, больше — на широком экране: тот же приём, что
    /// в системных плиточных списках (Музыка, Погода).
    private static let columns = [GridItem(.adaptive(minimum: 150), spacing: Tokens.Spacing.m)]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Spacing.m) {
                NearbyShelf()

                LazyVGrid(columns: Self.columns, spacing: Tokens.Spacing.m) {
                    ForEach(menu.chains) { chain in
                        NavigationLink(value: Route.chain(chain)) {
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

    /// Спрашивать заново нельзя — только подхватить решение, которое уже
    /// стоит в системе (например, человек разрешил на вкладке «Nearby»).
    private func autoLoadNearbyIfAuthorized() {
        guard nearby.state == .idle, !menu.chains.isEmpty else { return }
        guard nearby.authorization == .authorizedWhenInUse
                || nearby.authorization == .authorizedAlways else { return }
        nearby.find(chains: menu.chains.map(\.name))
    }
}

/// «Рядом» — витрина в одну строку: сети, а не заведения с адресом и
/// часами, полный разбор остаётся за вкладкой «Nearby». Отказ и ошибка
/// молчат — это необязательная секция, а не тело экрана, приставать
/// на главном экране с ними незачем.
///
/// Отдельным видом, чтобы от ответов карты перерисовывалась только эта
/// полоса: карта присылает их пачками, и раньше каждая пачка пересобирала
/// всю сетку сетей.
private struct NearbyShelf: View {

    @Environment(MenuRepository.self) private var menu
    @Environment(NearbyStore.self) private var nearby

    var body: some View {
        switch nearby.state {
        case .idle:
            if nearby.authorization == .notDetermined {
                NearbyPromptCard {
                    nearby.find(chains: menu.chains.map(\.name))
                }
            }
        case .locating, .searching:
            HStack(spacing: Tokens.Spacing.s) {
                ProgressView()
                Text("Finding restaurants near you…")
                    .font(.subheadline)
                    .foregroundStyle(Tokens.Color.textSecondary)
            }
            .padding(.horizontal, Tokens.Spacing.m)
        case .ready(let chains):
            if !chains.isEmpty {
                shelf(chains)
            }
        case .denied, .failed:
            EmptyView()
        }
    }

    private func shelf(_ chains: [NearbyChain]) -> some View {
        VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
            SectionTitle("Restaurants Near Me")
                .padding(.horizontal, Tokens.Spacing.m)

            ScrollView(.horizontal, showsIndicators: false) {
                LazyHStack(alignment: .top, spacing: Tokens.Spacing.m) {
                    ForEach(chains) { found in
                        if let chain = menu.chain(named: found.chain) {
                            NavigationLink(value: Route.chain(chain)) {
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
}

/// Приглашение включить «рядом». Диалог геопозиции — по нажатию, не раньше.
private struct NearbyPromptCard: View {

    let action: () -> Void

    var body: some View {
        Button(action: action) {
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
            .padding(Tokens.Spacing.card)
            .background(Tokens.Color.cardBackground, in: .rect(cornerRadius: Tokens.Radius.card))
        }
        .buttonStyle(.plain)
        .padding(.horizontal, Tokens.Spacing.m)
    }
}

/// Запрос ищет сразу по всем сетям, а не по одной открытой.
private struct SearchResults: View {

    let query: String

    @Environment(MenuRepository.self) private var menu
    /// Ответ вместе с запросом, на который он дан: пока идёт пауза, на экране
    /// остаётся прошлый ответ, а не «ничего не нашлось».
    @State private var answer: (query: String, items: [MenuItem])?

    var body: some View {
        Group {
            if let answer, answer.query == query, answer.items.isEmpty {
                ContentUnavailableView.search(text: query)
            } else {
                List(answer?.items ?? []) { item in
                    NavigationLink(value: Route.item(item)) {
                        MenuItemRow(item: item, showsChain: true,
                                    variants: menu.variants(of: item))
                    }
                }
            }
        }
        .task(id: query) {
            // Поиск — проход по всему каталогу, двадцать пять тысяч позиций.
            // Раньше он шёл прямо в `body` на каждую букву; пауза отдаёт его
            // только последнему нажатию из быстрой серии.
            try? await Task.sleep(for: .milliseconds(150))
            guard !Task.isCancelled else { return }
            answer = (query, menu.collapsingVariants(menu.search(query)))
        }
    }
}

#Preview {
    ChainsView(path: .constant([]))
        .environment(MenuRepository.preview)
        .environment(NearbyStore())
}
