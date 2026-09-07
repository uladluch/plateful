import Foundation

// Проект собран с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor; арифметика
// макросов — чистые значения, главный поток им не нужен.

/// Калории и три макроса. Складываются и умножаются, чтобы пересчёт заказа
/// был одной строкой, а не четырьмя параллельными суммами.
nonisolated struct Nutrition: Hashable, Sendable {

    var kcal: Double
    var protein: Double
    var carbs: Double
    var fat: Double

    static let zero = Nutrition(kcal: 0, protein: 0, carbs: 0, fat: 0)

    static func + (lhs: Nutrition, rhs: Nutrition) -> Nutrition {
        Nutrition(
            kcal: lhs.kcal + rhs.kcal,
            protein: lhs.protein + rhs.protein,
            carbs: lhs.carbs + rhs.carbs,
            fat: lhs.fat + rhs.fat)
    }

    static func * (nutrition: Nutrition, factor: Int) -> Nutrition {
        Nutrition(
            kcal: nutrition.kcal * Double(factor),
            protein: nutrition.protein * Double(factor),
            carbs: nutrition.carbs * Double(factor),
            fat: nutrition.fat * Double(factor))
    }
}

nonisolated extension MenuItem {
    var nutrition: Nutrition {
        Nutrition(kcal: kcal, protein: protein, carbs: carbs, fat: fat)
    }
}
