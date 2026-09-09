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

        /// Фон карточки на групповом фоне — на шаг светлее самого фона,
        /// как у системных сгруппированных ячеек.
        static let cardBackground = SwiftUI.Color(.secondarySystemGroupedBackground)

        /// Цвета макросов. Разные оттенки нужны, чтобы белки/углеводы/жиры
        /// различались взглядом за те самые тридцать секунд у кассы.
        static let protein = SwiftUI.Color(.systemBlue)
        static let carbs = SwiftUI.Color(.systemOrange)
        static let fat = SwiftUI.Color(.systemPink)
        static let calories = SwiftUI.Color.primary

        /// Пометка «данные могут быть устаревшими» — предупреждение, не ошибка.
        static let staleWarning = SwiftUI.Color(.systemOrange)

        /// Подложка под настоящий снимок блюда.
        ///
        /// Осознанное исключение из правила «только системные цвета»: съёмка
        /// снята на белом циклораме, и в тёмной теме серый системный фон
        /// показывает края кадра как обрезанные — буквальный белый читает
        /// снимок карточкой товара в любой теме, как в Instacart и Ozon.
        /// Заглушки без снимка сюда не относятся — у них обычный `secondarySystemFill`.
        static let photoBackground = SwiftUI.Color.white

        /// Глиф иконки строки — второе осознанное исключение из «только
        /// системные цвета»: подложка в `RowIcon` цветная (см. `RowIconTint`
        /// ниже), а символ на ней всегда белый — единственный цвет, который
        /// читается на любом из этих оттенков, так же, как делает Apple в
        /// Settings.
        static let rowIconGlyph = SwiftUI.Color.white
    }

    /// Правило дизайн-системы: у иконки в начале строки списка всегда есть
    /// цветная подложка (`RowIcon`), сама иконка на ней — белая. Голый
    /// цветной SF Symbol на системном фоне строки читается слабее и не даёт
    /// строке якорь для глаза; подложка есть у Settings, Reminders,
    /// Health — и должна быть здесь везде одинаково.
    ///
    /// Цвет подложки — по психологии цвета того, что означает иконка, не по
    /// вкусу и не по остатку из палитры: синий читается как доверие и
    /// информация, оранжевый — как внимание и время, зелёный — как еда и
    /// свежесть, розовый — как «для детей», индиго — как сообщество и
    /// компания, красный — как метка на карте и ограничение, фиолетовый —
    /// как редкое и сезонное предложение.
    enum RowIconTint {
        /// Источник данных — синий: то, чему стоит доверять.
        static let source = SwiftUI.Color(.systemBlue)
        /// Дата записи — тот же оранжевый, что у предупреждения об
        /// устаревании: свежесть данных и есть про время.
        static let freshness = SwiftUI.Color(.systemOrange)
        /// Размер порции — зелёный: еда, а не служебная цифра.
        static let serving = SwiftUI.Color(.systemGreen)
        /// Детское меню — розовый.
        static let kids = SwiftUI.Color(.systemPink)
        /// «На компанию» — индиго: про людей вместе, не про одного.
        static let shareable = SwiftUI.Color(.systemIndigo)
        /// «Не везде» — красный, тот же смысл, что у булавки на карте.
        static let regional = SwiftUI.Color(.systemRed)
        /// Сезонное предложение — фиолетовый: редкое, ограниченное по времени.
        static let seasonal = SwiftUI.Color(.systemPurple)
    }

    enum Spacing {
        static let xs: CGFloat = 4
        static let s: CGFloat = 8
        static let m: CGFloat = 16
        static let l: CGFloat = 24
    }

    enum Radius {
        static let image: CGFloat = 8
        static let card: CGFloat = 16
    }

    /// Имена символов — строки, и главный актор им ни к чему: их спрашивает
    /// в том числе представление каталога, а оно `nonisolated`.
    nonisolated enum Symbol {
        static let chain = "storefront"
        static let calories = "flame"
        static let protein = "circle.fill"
        static let carbs = "circle.fill"
        static let fat = "circle.fill"
        static let stale = "clock.badge.exclamationmark"
        static let source = "building.columns"
        static let serving = "fork.knife"
        static let failure = "exclamationmark.triangle"

        /// Маршрут до заведения.
        static let directions = "arrow.triangle.turn.up.right.circle"

        /// Пометки позиции.
        static let kidsMeal = "figure.and.child.holdinghands"
        static let shareable = "person.2"
        static let regional = "mappin.and.ellipse"
        static let seasonal = "calendar"
    }
}
