import SwiftData
import SwiftUI

/// Меню одной сети, разбитое по категориям.
struct ChainMenuView: View {

    let chain: MenuChain

    @Environment(MenuRepository.self) private var menu
    @Query private var goals: [UserGoals]

    @State private var query = ""
    @State private var filter = MenuFilter.none

    var body: some View {
        List {
            header

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
                let results = menu.collapsingVariants(
                    filter.apply(to: menu.search(query, in: chain.name, limit: 200)))
                if results.isEmpty {
                    ContentUnavailableView.search(text: query)
                } else {
                    ForEach(results) { item in
                        NavigationLink(value: item) {
                            MenuItemRow(item: item, showsChain: false,
                                        variants: menu.variants(of: item))
                        }
                    }
                }
            }
        }
        // Без этого List рисует каждую Section как сгруппированную карточку
        // — тогда карточкой читается вся категория, а не позиция внутри неё.
        // .plain убирает этот фон и оставляет карточкой только ItemCard.
        .listStyle(.plain)
        // Название уже стоит в шапке контента, крупно и под маркой; в навбаре
        // оно было бы дублем. Пустой заголовок отдаёт эту строку шапке и
        // всё равно оставляет системную кнопку «Назад».
        .navigationTitle("")
        .navigationBarTitleDisplayMode(.inline)
        .searchable(text: $query, prompt: "Search \(chain.name)")
        .toolbar {
            MenuFilterMenu(filter: $filter, goals: goals.first)
        }
    }

    /// Марка сети сверху, название под ней — первое, что видно на экране
    /// меню, ещё до самих категорий.
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
}

#Preview {
    NavigationStack {
        ChainMenuView(chain: MenuChain(name: "McDonald's", itemCount: 3))
    }
    .environment(MenuRepository.preview)
}
