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
            hero

            if item.isOffMenu {
                Section {
                    Label {
                        Text("No longer on the menu")
                            .foregroundStyle(Tokens.Color.staleWarning)
                    } icon: {
                        RowIcon(symbol: Tokens.Symbol.stale, tint: Tokens.RowIconTint.freshness)
                    }
                } footer: {
                    Text("This dish was on \(item.chain)'s menu when the data was collected, but is not listed today.")
                }
            }

            label

            portion

            legal
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

    /// Снимок, название, калории и макросы — одним блоком под шапкой, не
    /// в карточке: это не ещё один раздел этикетки, а то, ради чего сюда
    /// зашли в первую секунду, и оно не должно выглядеть строкой среди
    /// прочих. Имя — Headline 2, крупнее заголовков разделов ниже: это всё
    /// ещё заголовок всей карточки, просто не в навбаре и не в header'е
    /// секции.
    private var hero: some View {
        VStack(spacing: Tokens.Spacing.m) {
            DishImage(item: illustrated, size: 220, isHero: true)

            VStack(spacing: Tokens.Spacing.s) {
                Text(variants.count > 1 ? item.baseName : item.name)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundStyle(Tokens.Color.textPrimary)
                    .multilineTextAlignment(.center)

                if variants.count > 1 { sizePicker }

                calories
                macroRings
            }
            .padding(.horizontal, Tokens.Spacing.m)
        }
        .listRowInsets(EdgeInsets())
        .listRowBackground(Color.clear)
        .listRowSeparator(.hidden)
    }

    /// Откуда цифра, на какой год и чей снимок — в самом низу карточки,
    /// одной секцией, а не подписью под снимком и отдельным разделом
    /// наверху: числа читают все, происхождение и лицензию — почти никто,
    /// и обоим место рядом, а не между фотографией и калориями.
    @ViewBuilder
    private var legal: some View {
        Section {
            LabeledContent {
                Text(shown.sourceDisplayName)
                    .multilineTextAlignment(.trailing)
            } label: {
                Label {
                    Text("Source")
                } icon: {
                    RowIcon(symbol: Tokens.Symbol.source, tint: Tokens.RowIconTint.source)
                }
            }
            LabeledContent {
                Text(shown.observedDisplay)
                    .monospacedDigit()
            } label: {
                Label {
                    Text("Figures from")
                } icon: {
                    RowIcon(symbol: Tokens.Symbol.stale, tint: Tokens.RowIconTint.freshness)
                }
            }
            if let photo = illustrated.photo {
                PhotoCaption(photo: photo)
            }
        } header: {
            SectionTitle("Legal")
        } footer: {
            if let notice = shown.staleNotice {
                Text(notice)
            }
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
                .padding(.vertical, Tokens.Spacing.xs)
        } else {
            picker.pickerStyle(.navigationLink)
        }
    }

    /// По центру, как имя над ней: раньше цифра стояла у левого края
    /// строки, а предупреждение об устаревании — у правого. В блоке под
    /// снимком это была бы асимметрия без причины, поэтому предупреждение
    /// встало рядом с подписью «calories», а не отдельно у края.
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
            if shown.isStale {
                Image(systemName: Tokens.Symbol.stale)
                    .foregroundStyle(Tokens.Color.staleWarning)
                    .accessibilityLabel("Figures may be out of date")
            }
        }
        .padding(.vertical, Tokens.Spacing.xs)
        .accessibilityElement(children: .combine)
    }

    /// Белки, углеводы, жиры — три кольца в ряд, а не строки друг под
    /// другом: заполнение кольца — доля этого макроса в калориях блюда
    /// (белок и углеводы по 4 ккал/г, жир — по 9), так три числа сразу
    /// читаются и по отдельности, и по вкладу в общую цифру наверху.
    private var macroRings: some View {
        HStack(spacing: Tokens.Spacing.l) {
            macroRing(title: "Protein", value: shown.proteinText,
                      share: macroShare(shown.protein, kcalPerGram: 4), color: Tokens.Color.protein)
            macroRing(title: "Carbs", value: shown.carbsText,
                      share: macroShare(shown.carbs, kcalPerGram: 4), color: Tokens.Color.carbs)
            macroRing(title: "Fat", value: shown.fatText,
                      share: macroShare(shown.fat, kcalPerGram: 9), color: Tokens.Color.fat)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, Tokens.Spacing.s)
    }

    /// Доля калорий одного макроса от суммы всех трёх — не от заявленных
    /// калорий блюда: округление на этикетке иначе иногда дало бы кольцо
    /// за пределами круга.
    private var macroKcalTotal: Double {
        shown.protein * 4 + shown.carbs * 4 + shown.fat * 9
    }

    private func macroShare(_ grams: Double, kcalPerGram: Double) -> Double {
        guard macroKcalTotal > 0 else { return 0 }
        return (grams * kcalPerGram) / macroKcalTotal
    }

    /// Системное кольцо-индикатор — то же, чем виджеты показывают заряд
    /// или прогресс кольца активности, здесь применено к одному макросу.
    private func macroRing(title: String, value: String, share: Double, color: Color) -> some View {
        VStack(spacing: Tokens.Spacing.s) {
            Gauge(value: share) {
                EmptyView()
            } currentValueLabel: {
                Text(value)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .monospacedDigit()
            }
            .gaugeStyle(.accessoryCircularCapacity)
            .tint(color)

            // Название — тем же весом, что и заголовок секции: не служебная
            // подпись под кольцом, а часть того, что человек хочет прочитать
            // первым делом.
            Text(title)
                .font(.footnote)
                .foregroundStyle(Tokens.Color.textPrimary)
        }
        .frame(maxWidth: .infinity)
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
                        Label {
                            Text("Serving")
                        } icon: {
                            RowIcon(symbol: Tokens.Symbol.serving, tint: Tokens.RowIconTint.serving)
                        }
                    }
                }
                ForEach(flags, id: \.self) { flag in
                    Label {
                        Text(flag.title)
                    } icon: {
                        RowIcon(symbol: flag.symbol, tint: flag.rowIconTint)
                    }
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
