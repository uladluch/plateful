import Foundation

// Проект собран с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor; сравнение —
// чистое значение над двумя позициями.

/// Сравнение двух блюд.
///
/// **Победитель не объявляется.** «Лучше» зависит от того, что человеку нужно
/// сегодня: кому-то меньше калорий, кому-то больше белка. Конкуренты ставят
/// оценку 0–100 и называют победителя — мы этот приём отвергли как
/// субъективный ещё на этапе границ MVP, и здесь он был бы тем же самым.
///
/// Показываем разницу — это факт. И отмечаем соответствие целям, если человек
/// их задал: это тоже факт, но уже относительно его собственной цели.
nonisolated struct Comparison: Sendable, Equatable {

    let left: MenuItem
    let right: MenuItem

    enum Nutrient: String, CaseIterable, Sendable {
        case calories, protein, carbs, fat

        var title: String {
            switch self {
            case .calories: "Calories"
            case .protein: "Protein"
            case .carbs: "Carbs"
            case .fat: "Fat"
            }
        }

        func value(of item: MenuItem) -> Double {
            switch self {
            case .calories: item.kcal
            case .protein: item.protein
            case .carbs: item.carbs
            case .fat: item.fat
            }
        }

        /// Калории — число, макросы — граммы.
        func format(_ value: Double) -> String {
            switch self {
            case .calories: value.formatted(.number.precision(.fractionLength(0)))
            default: MenuItem.grams(value)
            }
        }

        /// Разница со знаком: «+40», «−6 g». Знак нужен всегда, иначе
        /// непонятно, в какую сторону отличается правое блюдо.
        func formatDifference(_ value: Double) -> String {
            let number = value.formatted(
                .number.precision(.fractionLength(0)).sign(strategy: .always()))
            return self == .calories ? number : "\(number) g"
        }
    }

    struct Row: Sendable, Equatable, Identifiable {
        let nutrient: Nutrient
        let left: Double
        let right: Double

        var id: String { nutrient.rawValue }
        var difference: Double { right - left }
        var isEqual: Bool { difference == 0 }

        var leftText: String { nutrient.format(left) }
        var rightText: String { nutrient.format(right) }
        var differenceText: String? {
            isEqual ? nil : nutrient.formatDifference(difference)
        }
    }

    var rows: [Row] {
        Nutrient.allCases.map { nutrient in
            Row(nutrient: nutrient,
                left: nutrient.value(of: left),
                right: nutrient.value(of: right))
        }
    }

    /// Хотя бы одна цифра различается.
    var hasDifferences: Bool { rows.contains { !$0.isEqual } }

    /// Подходит ли каждое блюдо под цели человека.
    struct GoalFit: Sendable, Equatable {
        let left: Bool
        let right: Bool
    }

    /// Соответствие целям человека — факт относительно заявленной цели,
    /// а не наша оценка блюда. Без заданных целей вердикта нет вовсе.
    func meetsGoals(_ filter: MenuFilter) -> GoalFit? {
        guard filter.isNarrowing else { return nil }
        return GoalFit(left: filter.matches(left), right: filter.matches(right))
    }

    /// Устарела ли хоть одна цифра: сравнение свежего со старым — повод
    /// сказать об этом, а не молча поставить их рядом.
    var isStale: Bool { left.isStale || right.isStale }
}
