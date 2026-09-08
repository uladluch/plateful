import SwiftData
import SwiftUI

/// Карточка блюда: число, ради которого открывали приложение, и честная
/// подпись о том, откуда оно взялось.
struct ItemDetailView: View {

    let item: MenuItem

    @Environment(\.modelContext) private var context
    @Environment(MenuRepository.self) private var menu

    @State private var isPickingRival = false
    @State private var rival: MenuItem?

    /// Выбранный размер. Ключ, а не индекс: индекс живёт до перезагрузки
    /// каталога, а обновление пака может прийти прямо с открытой карточкой.
    @State private var sizeKey: String

    init(item: MenuItem) {
        self.item = item
        // Открываемся на том размере, который человек выбрал в списке.
        _sizeKey = State(initialValue: item.key)
    }

    /// Размеры одного блюда, слева направо. Пусто — блюдо одного размера.
    private var variants: [MenuItem] { menu.sizeVariants(of: item) }

    /// Позиция, о которой сейчас говорит вся карточка.
    private var shown: MenuItem {
        variants.first { $0.key == sizeKey } ?? item
    }

    /// Снимок берём у того размера, у которого он есть: у «Waffle Potato
    /// Fries» сеть сняла только Large, и подмена фотографии на заглушку при
    /// переключении сегмента читалась бы как поломка.
    private var illustrated: MenuItem {
        shown.photo != nil ? shown : (variants.first { $0.photo != nil } ?? shown)
    }

    var body: some View {
        List {
            Section {
                DishImage(item: illustrated, size: 220, isHero: true)
                    .listRowInsets(EdgeInsets())
                    .listRowBackground(Color.clear)
            } footer: {
                if let photo = illustrated.photo {
                    PhotoCaption(photo: photo)
                }
            }

            if item.isOffMenu {
                Section {
                    Label {
                        Text("No longer on the menu")
                    } icon: {
                        Image(systemName: Tokens.Symbol.stale)
                    }
                    .foregroundStyle(Tokens.Color.staleWarning)
                } footer: {
                    Text("This dish was on \(item.chain)'s menu when the data was collected, but is not listed today.")
                }
            }

            Section {
                // Размер — первым: он меняет все числа под собой, и читать
                // карточку сверху вниз надо уже с выбранным сегментом.
                if variants.count > 1 { sizePicker }
                calories
                macro("Protein", value: shown.proteinText, color: Tokens.Color.protein)
                macro("Carbs", value: shown.carbsText, color: Tokens.Color.carbs)
                macro("Fat", value: shown.fatText, color: Tokens.Color.fat)
            } header: {
                Text(item.chain)
            }

            if let serving = shown.serving {
                Section {
                    LabeledContent {
                        Text(serving)
                    } label: {
                        Label("Serving", systemImage: Tokens.Symbol.serving)
                    }
                }
            }

            // Конкурентов бьют за молчаливо устаревшие данные. Мы говорим,
            // откуда цифра и на какой год, — это одно из трёх отличий.
            Section {
                LabeledContent {
                    Text(shown.sourceDisplayName)
                        .multilineTextAlignment(.trailing)
                } label: {
                    Label("Source", systemImage: Tokens.Symbol.source)
                }
                LabeledContent {
                    Text(shown.observedDisplay)
                        .monospacedDigit()
                } label: {
                    Label("Figures from", systemImage: Tokens.Symbol.stale)
                }
            } footer: {
                if let notice = shown.staleNotice {
                    Text(notice)
                }
            }
        }
        // Заголовок без размера: он не должен прыгать при переключении
        // сегмента — размер и так виден в переключателе. Но только там, где
        // переключатель есть: у одинокой «Apple Slices, 1 Package» размер —
        // часть названия, и отрезать его нечестно.
        .navigationTitle(variants.count > 1 ? item.baseName : item.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("Compare", systemImage: "arrow.left.arrow.right") {
                    isPickingRival = true
                }
            }
            ToolbarItem(placement: .primaryAction) {
                NavigationLink {
                    OrderView(startingWith: shown)
                } label: {
                    Label("Build order", systemImage: "plus.forwardslash.minus")
                }
            }
        }
        .sheet(isPresented: $isPickingRival) {
            ItemPickerView(chain: nil, excluding: shown.persistentID) { picked in
                rival = picked
                isPickingRival = false
            }
        }
        .navigationDestination(item: $rival) { other in
            ComparisonView(comparison: Comparison(left: shown, right: other))
        }
        .task(id: shown.persistentID) {
            // Сбой истории не должен мешать смотреть калории — это справочник,
            // а история лишь удобство.
            try? UserDataStore(context: context).recordView(of: shown)
        }
    }

    /// Кто владеет снимком и откуда он взят.
    ///
    /// Подпись — условие, на котором сеть разрешила использование, а не
    /// замена разрешению. Поэтому она обязательна там, где снимок принадлежит
    /// сети, и не показывается у свободных лицензий, где владельца нет.
    private struct PhotoCaption: View {
        let photo: MenuPack.Photo

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
                Text(photo.license)
                if let page = photo.page {
                    Link(page.host() ?? page.absoluteString, destination: page)
                }
            }
            .font(.caption2)
        }
    }

    /// Сегментов столько же, сколько размеров: у кассы выбирают из того,
    /// что на табло, а не из выпадающего списка.
    ///
    /// Потолок — шесть: на узком iPhone это по 57 pt на сегмент, ещё выше
    /// минимальной цели нажатия в 44 pt. Дальше переключатель становится
    /// системным списком — у Steak 'n Shake газировка идёт девятью объёмами
    /// от 12 до 44 oz, и девять полосок не нажать даже с сокращениями.
    private static let maxSegments = 6

    @ViewBuilder
    private var sizePicker: some View {
        let picker = Picker("Size", selection: $sizeKey) {
            ForEach(variants) { variant in
                // На сегменте — «L», в озвучке — «Large»: сокращение
                // экономит ширину, а не смысл.
                Text(variant.size?.shortLabel ?? variant.name)
                    .accessibilityLabel(variant.size?.label ?? variant.name)
                    .tag(variant.key)
            }
        }
        if variants.count <= Self.maxSegments {
            picker
                .pickerStyle(.segmented)
                .listRowInsets(EdgeInsets(top: Tokens.Spacing.s, leading: Tokens.Spacing.m,
                                          bottom: Tokens.Spacing.s, trailing: Tokens.Spacing.m))
        } else {
            picker.pickerStyle(.navigationLink)
        }
    }

    private var calories: some View {
        HStack(alignment: .firstTextBaseline, spacing: Tokens.Spacing.s) {
            Text(shown.calorieText)
                .font(.largeTitle)
                .fontWeight(.semibold)
                .monospacedDigit()
                .foregroundStyle(Tokens.Color.calories)
            Text("calories")
                .font(.subheadline)
                .foregroundStyle(Tokens.Color.textSecondary)
            Spacer()
            if shown.isStale {
                Image(systemName: Tokens.Symbol.stale)
                    .foregroundStyle(Tokens.Color.staleWarning)
                    .accessibilityLabel("Figures may be out of date")
            }
        }
        .padding(.vertical, Tokens.Spacing.xs)
        .accessibilityElement(children: .combine)
    }

    private func macro(_ title: String, value: String, color: Color) -> some View {
        LabeledContent {
            Text(value).monospacedDigit()
        } label: {
            Label {
                Text(title)
            } icon: {
                Image(systemName: Tokens.Symbol.protein)
                    .foregroundStyle(color)
                    .imageScale(.small)
            }
        }
    }
}

#Preview("Устаревшие данные") {
    NavigationStack {
        ItemDetailView(item: MenuRepository.previewItem(name: "Big Mac"))
    }
    .environment(MenuRepository.preview)
}

#Preview("Сверено с сайтом сети") {
    NavigationStack {
        ItemDetailView(item: MenuRepository.previewItem(name: "Quarter Pounder w/ Cheese"))
    }
    .environment(MenuRepository.preview)
}
