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
