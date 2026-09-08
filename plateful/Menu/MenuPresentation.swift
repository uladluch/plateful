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

    /// Позиции сети, разбитые по категориям.
    ///
    /// Порядок категорий — как в паке: он идёт от источника, а не от
    /// алфавита, и завтраки там раньше десертов.
    ///
    /// Блюда, которых больше нет в меню, собираются в отдельный раздел
    /// в самом конце. Держать их вперемешку с текущими — вводить в
    /// заблуждение: человек стоит у кассы и не может это заказать.
    func sections(for chain: String) -> [MenuSection] {
        var order: [String] = []
        var grouped: [String: [MenuItem]] = [:]
        var archived: [MenuItem] = []

        for item in items(in: chain) {
            if item.isOffMenu {
                archived.append(item)
                continue
            }
            let title = item.category ?? MenuSection.uncategorized
            if grouped[title] == nil { order.append(title) }
            grouped[title, default: []].append(item)
        }

        var sections = order.map { MenuSection(title: $0, items: grouped[$0] ?? []) }
        if !archived.isEmpty {
            sections.append(MenuSection(title: MenuSection.archived, items: archived))
        }
        return sections
    }
}

nonisolated extension MenuCatalog {

    /// Те же разделы, но по одной строке на группу размеров.
    ///
    /// Отдельным шагом, а не внутри `sections(for:)`: свёртка обязана идти
    /// после фильтра по целям, иначе группа исчезает из-за размера, который
    /// в цель не влез, — а маленький влезал.
    func collapsingSizeVariants(_ sections: [MenuSection]) -> [MenuSection] {
        sections.map { MenuSection(title: $0.title,
                                   items: collapsingSizeVariants($0.items)) }
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

nonisolated extension MenuItem {

    /// Калории — целым числом: доли грамма у кассы никому не нужны.
    var calorieText: String {
        kcal.formatted(.number.precision(.fractionLength(0)))
    }

    var proteinText: String { Self.grams(protein) }
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
