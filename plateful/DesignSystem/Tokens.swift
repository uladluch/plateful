import SwiftUI

/// Единственное место, где называются цвета и отступы.
///
/// Все значения — системные: так приложение бесплатно получает тёмную тему,
/// контрастные режимы и Dynamic Type, а смена дизайн-системы остаётся
/// правкой одного файла.
enum Tokens {

    enum Color {
        static let textPrimary = SwiftUI.Color.primary
        static let textSecondary = SwiftUI.Color.secondary
        static let accent = SwiftUI.Color.accentColor

        /// Цвета макросов. Разные оттенки нужны, чтобы белки/углеводы/жиры
        /// различались взглядом за те самые тридцать секунд у кассы.
        static let protein = SwiftUI.Color(.systemBlue)
        static let carbs = SwiftUI.Color(.systemOrange)
        static let fat = SwiftUI.Color(.systemPink)
        static let calories = SwiftUI.Color.primary

        /// Пометка «данные могут быть устаревшими» — предупреждение, не ошибка.
        static let staleWarning = SwiftUI.Color(.systemOrange)
    }

    enum Spacing {
        static let xs: CGFloat = 4
        static let s: CGFloat = 8
        static let m: CGFloat = 16
        static let l: CGFloat = 24
    }

    enum Radius {
        static let image: CGFloat = 8
    }

    enum Symbol {
        static let chain = "storefront"
        static let calories = "flame"
        static let protein = "circle.fill"
        static let carbs = "circle.fill"
        static let fat = "circle.fill"
        static let stale = "clock.badge.exclamationmark"
        static let source = "building.columns"
        static let serving = "fork.knife"
        static let failure = "exclamationmark.triangle"

        /// Пометки позиции.
        static let kidsMeal = "figure.and.child.holdinghands"
        static let shareable = "person.2"
        static let regional = "mappin.and.ellipse"
        static let seasonal = "calendar"
    }
}
