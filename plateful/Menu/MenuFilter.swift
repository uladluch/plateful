import Foundation

// Проект собран с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor; фильтр —
// чистое значение над массивом позиций.

/// Как упорядочить меню.
nonisolated enum MenuSort: String, CaseIterable, Identifiable, Sendable {
    /// Порядок из пака: категории идут так, как их публикует сеть.
    case menuOrder
    case fewestCalories
    case mostProtein

    var id: String { rawValue }

    var title: String {
        switch self {
        case .menuOrder: "Menu order"
        case .fewestCalories: "Fewest calories"
        case .mostProtein: "Most protein"
        }
    }
}

/// Отбор позиций по целям человека.
///
/// Цели необязательные: пустой фильтр ничего не отсекает. Так справочник
/// остаётся справочником для того, кто целей не ставил.
nonisolated struct MenuFilter: Equatable, Sendable {

    var maxCalories: Int?
    var minProtein: Int?
    var sort: MenuSort = .menuOrder

    static let none = MenuFilter()

    /// Меняет ли фильтр состав выдачи. Сортировка сюда не входит: она
    /// переставляет, но ничего не прячет.
    var isNarrowing: Bool { maxCalories != nil || minProtein != nil }

    var isActive: Bool { isNarrowing || sort != .menuOrder }

    func apply(to items: [MenuItem]) -> [MenuItem] {
        let kept = isNarrowing ? items.filter(matches) : items

        return switch sort {
        case .menuOrder:
            kept
        case .fewestCalories:
            kept.sorted { ($0.kcal, $0.name) < ($1.kcal, $1.name) }
        case .mostProtein:
            kept.sorted { ($1.protein, $1.name) < ($0.protein, $0.name) }
        }
    }

    func matches(_ item: MenuItem) -> Bool {
        if let maxCalories, item.kcal > Double(maxCalories) { return false }
        if let minProtein, item.protein < Double(minProtein) { return false }
        return true
    }

    /// Разделы меню с применённым фильтром; пустые разделы исчезают.
    func apply(to sections: [MenuSection]) -> [MenuSection] {
        guard isActive else { return sections }

        // При сортировке деление на категории теряет смысл: человек просил
        // «самое белковое в сети», а не «самое белковое в каждой категории».
        if sort != .menuOrder {
            let all = apply(to: sections.flatMap(\.items))
            return all.isEmpty ? [] : [MenuSection(title: sort.title, items: all)]
        }

        return sections.compactMap { section in
            let items = apply(to: section.items)
            return items.isEmpty ? nil : MenuSection(title: section.title, items: items)
        }
    }
}
