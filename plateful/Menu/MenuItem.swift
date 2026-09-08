import Foundation

/// Позиция меню в том виде, в котором её показывает интерфейс.
// Проект собирается с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor — это верно
// для SwiftUI, но не для слоя данных: каталог разбирается и строится вне
// главного потока. Отсюда `nonisolated` на типах ниже.
nonisolated struct MenuItem: Identifiable, Hashable, Sendable {

    /// Индекс в каталоге. Стабилен, пока каталог не перезагружен, — этого
    /// достаточно для списков SwiftUI. Для сохранённых заказов и истории
    /// брать `persistentID`: он переживает обновление пака.
    let id: Int

    let chain: String
    let key: String
    let name: String
    let category: String?
    let serving: String?

    let kcal: Double
    let protein: Double
    let carbs: Double
    let fat: Double

    /// Архетип блюда — имя изображения в каталоге ассетов.
    ///
    /// Не фотография конкретной позиции сети: снимок общий для всех
    /// чизбургеров, потому что чизбургер выглядит чизбургером везде.
    let image: String?

    /// Откуда цифра и на какую дату. Приложение обещает это показывать —
    /// конкурентов бьют именно за молчаливо устаревшие данные.
    let source: String
    let observed: String
    let isStale: Bool

    var persistentID: PersistentID { PersistentID(chain: chain, key: key) }

    /// Ссылка на позицию, переживающая обновление пака.
    struct PersistentID: Hashable, Codable, Sendable {
        let chain: String
        let key: String
    }
}

nonisolated extension MenuItem {

    init(id: Int, packItem: MenuPack.Item, defaults: MenuPack) {
        self.id = id
        self.chain = packItem.chain
        self.key = packItem.key
        self.name = packItem.name
        self.category = packItem.category
        self.serving = packItem.serving
        self.kcal = packItem.kcal
        self.protein = packItem.protein
        self.carbs = packItem.carbs
        self.fat = packItem.fat
        self.image = packItem.image
        self.source = packItem.source ?? defaults.source
        self.observed = packItem.observed ?? defaults.observed
        self.isStale = packItem.stale ?? defaults.stale
    }
}

/// Сеть и её позиции.
nonisolated struct MenuChain: Identifiable, Hashable, Sendable {
    var id: String { name }
    let name: String
    let itemCount: Int
}
