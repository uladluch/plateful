import Foundation

// Проект собран с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor; форматирование
// и группировка — чистые функции над данными, им главный поток не нужен.

/// Раздел меню сети: категория и её позиции.
nonisolated struct MenuSection: Identifiable, Hashable, Sendable {
    var id: String { title }
    let title: String
    let items: [MenuItem]
}

nonisolated extension MenuCatalog {

    /// Позиции сети, разбитые по разделам меню.
    ///
    /// Порядок разделов — из пака, один на все 96 сетей: сначала то, ради
    /// чего пришли, в конце напитки и добавки. У источника порядка нет
    /// вовсе, и раньше разделы шли по алфавиту первого блюда — меню
    /// McDonald's открывалось напитками, а соусы стояли выше картошки.
    ///
    /// Блюда, которых больше нет в меню, собираются в отдельный раздел
    /// в самом конце. Держать их вперемешку с текущими — вводить в
    /// заблуждение: человек стоит у кассы и не может это заказать.
    func sections(for chain: String) -> [MenuSection] {
        var grouped: [String: [MenuItem]] = [:]
        var archived: [MenuItem] = []

        for item in items(in: chain) {
            if item.isOffMenu {
                archived.append(item)
                continue
            }
            grouped[item.section, default: []].append(item)
        }

        var sections = grouped.keys
            .sorted { (order(of: $0), $0) < (order(of: $1), $1) }
            .map { MenuSection(title: $0, items: grouped[$0] ?? []) }
        if !archived.isEmpty {
            sections.append(MenuSection(title: MenuSection.archived, items: archived))
        }
        return sections
    }
}

nonisolated extension MenuCatalog {

    /// Те же разделы, но по одной строке на группу вариантов.
    ///
    /// Отдельным шагом, а не внутри `sections(for:)`: свёртка обязана идти
    /// после фильтра по целям, иначе группа исчезает из-за размера, который
    /// в цель не влез, — а маленький влезал.
    func collapsingVariants(_ sections: [MenuSection]) -> [MenuSection] {
        sections.map { MenuSection(title: $0.title,
                                   items: collapsingVariants($0.items)) }
    }

    /// Три подборки поверх обычных категорий: то же меню, другой разрез.
    ///
    /// Не фильтр — витрина. Показывают лучшее по одной цифре сразу, ещё до
    /// того, как человек станет листать категории или ставить свои цели.
    /// Раздел со снятыми с меню позициями сюда не попадает: подборка о
    /// том, что можно заказать сейчас.
    func highlightShelves(for chain: String, limit: Int = 12) -> [MenuSection] {
        let items = collapsingVariants(items(in: chain).filter { !$0.isOffMenu })
        guard !items.isEmpty else { return [] }

        func shelf(_ title: String, _ sorted: [MenuItem]) -> MenuSection? {
            sorted.isEmpty ? nil : MenuSection(title: title, items: Array(sorted.prefix(limit)))
        }

        let highProtein = items.sorted {
            $0.protein != $1.protein ? $0.protein > $1.protein : $0.name < $1.name
        }

        // «Меньше сахара» — это порог, не просто сортировка: меньше 6 г на
        // 100 г продукта, тот же порог, что называют «низкий сахар» на
        // этикетке. Сравнивать абсолютные граммы порции было бы нечестно —
        // банка 500 мл и стакан 200 мл не равны просто потому что у одной
        // цифра меньше. Без веса порции позиция не попадает в подборку: он
        // есть не у каждой строки («1 Slice», «Small» веса не несут), и
        // лучше не показать число, чем придумать его.
        let lessSugar = items
            .compactMap { item -> (item: MenuItem, per100: Double)? in
                guard let per100 = item.sugarPer100g, per100 < 6 else { return nil }
                return (item, per100)
            }
            .sorted {
                $0.per100 != $1.per100 ? $0.per100 < $1.per100 : $0.item.name < $1.item.name
            }
            .map(\.item)

        // Газировка почти всегда дешевле по калориям, чем еда, и заняла бы
        // подборку целиком — а «меньше калорий» здесь про то, что съесть,
        // а не про то, что выпить. Она не исчезает, а уходит в конец ряда.
        let lessCalories = items.sorted {
            let left = ($0.isSoda ? 1 : 0, $0.kcal, $0.name)
            let right = ($1.isSoda ? 1 : 0, $1.kcal, $1.name)
            return left < right
        }

        return [
            shelf("High Protein", highProtein),
            shelf("Less Sugar", lessSugar),
            shelf("Less Calories", lessCalories),
        ].compactMap { $0 }
    }
}

nonisolated extension MenuSection {
    /// Для позиций, у которых источник не указал категорию.
    static let uncategorized = "Other"

    /// Раздел со снятыми с меню блюдами. Заголовок — место («Archive»),
    /// а объяснение живёт в подписи под разделом: в шапке списка длинная
    /// фраза читается хуже короткого имени.
    static let archived = "Archive"

    var isArchive: Bool { title == Self.archived }
}

nonisolated extension Array where Element == MenuItem {

    /// «140–380» или «140», если во всех размерах число одно.
    ///
    /// Диапазон, а не число представителя: в списке он честнее — человек
    /// видит, во что обойдётся выбор размера, ещё до открытия карточки.
    var calorieRangeText: String {
        range(of: \.kcal) { $0.formatted(.number.precision(.fractionLength(0))) }
    }

    /// «20–25 g» — единица одна на весь диапазон, а не по разу на конец.
    var proteinRangeText: String {
        range(of: \.protein, unit: MenuItem.grams) {
            $0.formatted(.number.precision(.fractionLength(0)))
        }
    }

    /// - Parameter unit: как оформить верхнюю границу; на неё вешается
    ///   единица измерения. Нижняя остаётся голым числом.
    private func range(of value: (MenuItem) -> Double,
                       unit: (Double) -> String = { _ in "" },
                       number: (Double) -> String) -> String {
        let values = map(value)
        guard let low = values.min(), let high = values.max() else { return "" }
        let highText = unit(high).isEmpty ? number(high) : unit(high)
        // Сравниваем округлённое, а не исходное: 139.6 и 140.4 дают одно
        // число, и «140–140» выглядело бы поломкой.
        guard number(low) != number(high) else { return highText }
        return "\(number(low))–\(highText)"
    }
}

nonisolated extension MenuItem.Variant {

    /// Сокращения размеров. Ключи в нижнем регистре: источник пишет и
    /// «Large», и «large».
    private static let abbreviations = [
        "extra small": "XS", "small": "S", "medium": "M",
        "large": "L", "extra large": "XL", "regular": "Reg",
    ]

    /// Подпись на сегменте.
    ///
    /// «S · M · L» — то, чем размеры подписаны на табло у кассы, и то, что
    /// влезает в сегмент шириной с палец. Полное слово остаётся у VoiceOver:
    /// «эс» вслух — не размер.
    ///
    /// Сокращаются только порции. Исполнение блюда («Egg», «Mayo») сократить
    /// нечем: там не шкала, а список, и первая буква ничего не значит.
    ///
    /// У объёмов буквы нет, поэтому остаётся число: единица повторяется в
    /// каждом сегменте, места не стоит, а под переключателем её всё равно
    /// показывает строка «Serving».
    ///
    /// Фирменные размеры не трогаем: «Grande» — имя, а не мера, и «G»
    /// рядом с «Venti» ничего не значит.
    var shortLabel: String {
        guard kind == .size else { return label }
        if let short = Self.abbreviations[label.lowercased()] { return short }

        let parts = label.split(separator: " ")
        if parts.count > 1, parts.last?.lowercased() == "oz",
           let number = parts.first, Double(number) != nil {
            return String(number)
        }
        return label
    }
}

nonisolated extension MenuItem {

    /// Калории — целым числом: доли грамма у кассы никому не нужны.
    var calorieText: String {
        kcal.formatted(.number.precision(.fractionLength(0)))
    }

    var proteinText: String { Self.grams(protein) }

    var sugarText: String? { sugar.map(Self.grams) }
    var satFatText: String? { satFat.map(Self.grams) }
    var fiberText: String? { fiber.map(Self.grams) }

    /// Трансжиры — с десятой долей: их и меряют долями грамма, и «0.5 г»
    /// в округлении до целого превратилось бы в успокоительный ноль.
    var transFatText: String? {
        transFat.map {
            Measurement(value: $0, unit: UnitMass.grams)
                .formatted(.measurement(
                    width: .abbreviated,
                    usage: .asProvided,
                    numberFormatStyle: .number.precision(.fractionLength(0...1))))
        }
    }

    /// Натрий и холестерин — в миллиграммах: так они стоят на этикетке,
    /// и так их сравнивают с дневной нормой.
    var sodiumText: String? { sodium.map(Self.milligrams) }
    var cholesterolText: String? { cholesterol.map(Self.milligrams) }

    var carbsText: String { Self.grams(carbs) }
    var fatText: String { Self.grams(fat) }

    /// Через `Measurement`, чтобы единицы приходили из системы, а не из
    /// захардкоженного «g».
    static func grams(_ value: Double) -> String {
        Measurement(value: value, unit: UnitMass.grams)
            .formatted(.measurement(
                width: .abbreviated,
                usage: .asProvided,
                numberFormatStyle: .number.precision(.fractionLength(0))))
    }

    static func milligrams(_ value: Double) -> String {
        Measurement(value: value, unit: UnitMass.milligrams)
            .formatted(.measurement(
                width: .abbreviated,
                usage: .asProvided,
                numberFormatStyle: .number.precision(.fractionLength(0))))
    }

    /// Вес порции в граммах — только если строка серванса его несёт явно.
    ///
    /// «12 fl oz», «4 oz», «85 g» разбираются; «1 Slice», «Small», «Regular»
    /// — нет, вес у них не написан, и его неоткуда взять, кроме как
    /// придумать. Жидкость и объём переводятся через плотность воды: для
    /// газировки и большинства напитков это точно, для сиропа — приближённо,
    /// но здесь речь о ранжировании в подборке, а не об этикетке.
    private static let servingUnits: [String: Double] = [
        "g": 1, "gram": 1, "grams": 1,
        "ml": 1, "milliliter": 1, "milliliters": 1,
        "fl oz": 29.5735, "floz": 29.5735,
        "oz": 28.3495, "ounce": 28.3495, "ounces": 28.3495,
        "lb": 453.592, "lbs": 453.592, "pound": 453.592, "pounds": 453.592,
    ]

    var servingGrams: Double? {
        guard let serving else { return nil }
        let parts = serving.split(separator: " ")
        guard let first = parts.first, let value = Double(first) else { return nil }
        let unit = parts.dropFirst().joined(separator: " ").lowercased()
        guard let multiplier = Self.servingUnits[unit] else { return nil }
        return value * multiplier
    }

    /// Сахар на 100 г продукта, а не абсолютная цифра порции: банка 500 мл
    /// и стакан 200 мл иначе сравнивались бы нечестно. `nil`, если сахар не
    /// указан или вес порции не считается по её строке.
    var sugarPer100g: Double? {
        guard let sugar, let servingGrams, servingGrams > 0 else { return nil }
        return sugar / servingGrams * 100
    }

    /// Газированный безалкогольный напиток — по названию, эвристика.
    ///
    /// В паке нет отдельного признака: раздел «Beverages» шире и включает
    /// кофе, сок, воду. Список — бренды и общие слова, которых достаточно
    /// в меню восьми ключевых сетей; сверяется по словам целиком, а не
    /// подстрокой, иначе «chocolate» поймает «cola».
    private static let sodaWords: Set<String> = [
        "coke", "cola", "pepsi", "sprite", "fanta", "soda", "surge",
        "squirt", "crush", "fresca", "barqs", "cheerwine", "sunkist",
    ]
    private static let sodaPhrases: [String] = [
        "mountain dew", "dr pepper", "root beer", "sierra mist",
        "mist twst", "7 up", "big red",
    ]

    var isSoda: Bool {
        let normalized = String(decoding: TextIndex.normalized(name), as: UTF8.self)
        if normalized.split(separator: " ").contains(where: { Self.sodaWords.contains(String($0)) }) {
            return true
        }
        let padded = " " + normalized + " "
        return Self.sodaPhrases.contains { padded.contains(" \($0) ") }
    }

    /// Пометки в порядке объявления: набор неупорядочен, а список на экране
    /// не должен прыгать между открытиями карточки.
    var orderedFlags: [MenuItem.Flag] {
        MenuItem.Flag.allCases.filter(flags.contains)
    }

    /// Человеческое имя источника.
    ///
    /// Приложение обещает показывать, откуда цифра, — значит `menustat-2018`
    /// в интерфейсе появляться не должно.
    var sourceDisplayName: String {
        source.hasPrefix("menustat")
            ? "MenuStat, NYC Dept. of Health"
            : source
    }

    /// Год наблюдения — этого достаточно, чтобы понять, насколько цифра свежая.
    var observedDisplay: String {
        String(observed.prefix(4))
    }

    /// Строка происхождения под карточкой.
    var provenanceText: String {
        "\(sourceDisplayName) · \(observedDisplay)"
    }

    /// Предупреждение показывается только там, где оно правдиво: у позиций,
    /// сверенных с сайтом сети, его быть не должно.
    var staleNotice: String? {
        isStale
            ? "Published \(observedDisplay). Chains change portions and recipes, so treat this as a guide."
            : nil
    }
}

nonisolated extension MenuItem.Flag {

    var title: String {
        switch self {
        case .kids: "Kids meal"
        case .shareable: "Made to share"
        case .regional: "Not at every location"
        case .seasonal: "Was a seasonal item"
        }
    }

    var symbol: String {
        switch self {
        case .kids: Tokens.Symbol.kidsMeal
        case .shareable: Tokens.Symbol.shareable
        case .regional: Tokens.Symbol.regional
        case .seasonal: Tokens.Symbol.seasonal
        }
    }

    /// Что пометка значит на самом деле. Показывается там, где формулировка
    /// сама по себе может обмануть.
    var notice: String? {
        switch self {
        case .seasonal:
            "This was a limited-time item when the figures were collected, so the chain may no longer serve it."
        case .regional:
            "The chain lists this dish at some locations only."
        case .kids, .shareable:
            nil
        }
    }
}
