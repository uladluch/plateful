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
    func sections(for chain: String) -> [MenuSection] {
        var order: [String] = []
        var grouped: [String: [MenuItem]] = [:]

        for item in items(in: chain) {
            let title = item.category ?? MenuSection.uncategorized
            if grouped[title] == nil { order.append(title) }
            grouped[title, default: []].append(item)
        }
        return order.map { MenuSection(title: $0, items: grouped[$0] ?? []) }
    }
}

nonisolated extension MenuSection {
    /// Для позиций, у которых источник не указал категорию.
    static let uncategorized = "Other"
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
