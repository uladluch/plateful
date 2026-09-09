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

    /// Выбранный вариант. Ключ, а не индекс: индекс живёт до перезагрузки
    /// каталога, а обновление пака может прийти прямо с открытой карточкой.
    @State private var variantKey: String

    init(item: MenuItem) {
        self.item = item
        // Открываемся на том варианте, который человек выбрал в списке.
        _variantKey = State(initialValue: item.key)
    }

    /// Варианты одного блюда, слева направо. Пусто — вариант один.
    private var variants: [MenuItem] { menu.variants(of: item) }

    /// Позиция, о которой сейчас говорит вся карточка.
    private var shown: MenuItem {
        variants.first { $0.key == variantKey } ?? item
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
                // Вариант — первым: он меняет все числа под собой, и читать
                // карточку сверху вниз надо уже с выбранным сегментом.
                if variants.count > 1 { sizePicker }
                calories
                macro("Protein", value: shown.proteinText, color: Tokens.Color.protein)
                macro("Carbs", value: shown.carbsText, color: Tokens.Color.carbs)
                macro("Fat", value: shown.fatText, color: Tokens.Color.fat)
            } header: {
                // Заголовок страницы переехал сюда: имя без размера, тот же
                // повод, что был у navigationTitle — «L» и так виден в
                // переключателе, а у одинокого блюда без вариантов размер
                // остаётся частью имени, отрезать его нечестно.
                SectionTitle(variants.count > 1 ? item.baseName : item.name)
            }

            label

            portion

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
        // Заголовка в навбаре больше нет — имя блюда переехало в шапку
        // раздела с калориями. Пустая строка оставляет системную кнопку
        // «Назад», не дублируя название.
        .navigationTitle("")
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

    /// Сегментов столько же, сколько вариантов: у кассы выбирают из того,
    /// что на табло, а не из выпадающего списка.
    ///
    /// Потолок — шесть: на узком iPhone это по 57 pt на сегмент, ещё выше
    /// минимальной цели нажатия в 44 pt. Дальше переключатель становится
    /// системным списком — у Steak 'n Shake газировка идёт девятью объёмами
    /// от 12 до 44 oz, и девять полосок не нажать даже с сокращениями.
    private static let maxSegments = 6

    @ViewBuilder
    private var sizePicker: some View {
        let picker = Picker(item.variant?.kind == .option ? "Option" : "Size",
                            selection: $variantKey) {
            ForEach(variants) { variant in
                // На сегменте — «L», в озвучке — «Large»: сокращение
                // экономит ширину, а не смысл.
                Text(variant.variant?.shortLabel ?? variant.name)
                    .accessibilityLabel(variant.variant?.label ?? variant.name)
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

    /// Остальная этикетка.
    ///
    /// Отдельным разделом, а не вперемешку с макросами: белки, углеводы и
    /// жиры — то, ради чего открывают карточку, а сахар и натрий ищут
    /// прицельно, когда есть повод. Строки, которых сеть не публикует,
    /// не показываем вовсе — прочерк там читался бы как ноль.
    @ViewBuilder
    private var label: some View {
        // Порядок — как на самой этикетке: жиры, холестерин, натрий,
        // клетчатка, сахар. Он привычен и потому не требует чтения подряд:
        // взгляд идёт туда, где строка стоит на упаковке.
        let rows: [(String, String)] = [
            ("Saturated fat", shown.satFatText), ("Trans fat", shown.transFatText),
            ("Cholesterol", shown.cholesterolText), ("Sodium", shown.sodiumText),
            ("Fiber", shown.fiberText), ("Sugars", shown.sugarText),
        ].compactMap { title, value in value.map { (title, $0) } }

        if !rows.isEmpty {
            Section {
                ForEach(rows, id: \.0) { title, value in
                    LabeledContent(title) {
                        Text(value).monospacedDigit()
                    }
                }
            } header: {
                SectionTitle("Label")
            }
        }
    }

    /// Порция и пометки: детская, на компанию, не везде, сезонная.
    ///
    /// Одной секцией с размером порции, а не отдельной: всё это ответы на
    /// «что мне принесут и застану ли я это», и разносить их по карточке
    /// значит заставить читать её дважды.
    @ViewBuilder
    private var portion: some View {
        let flags = shown.orderedFlags

        if shown.serving != nil || !flags.isEmpty {
            Section {
                if let serving = shown.serving {
                    LabeledContent {
                        Text(serving)
                    } label: {
                        Label("Serving", systemImage: Tokens.Symbol.serving)
                    }
                }
                ForEach(flags, id: \.self) { flag in
                    Label(flag.title, systemImage: flag.symbol)
                }
            } footer: {
                // Пояснение — только там, где сама формулировка может
                // обмануть: «сезонное» в снимке 2018 года это не «успей
                // до конца месяца», а «скорее всего уже не подают».
                if let notice = flags.compactMap(\.notice).first {
                    Text(notice)
                }
            }
        }
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
