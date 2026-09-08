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

    /// Снимок именно этого блюда. Где его нет, показывается картинка
    /// по архетипу — она есть всегда.
    let photo: MenuPack.Photo?

    /// Размер порции, если блюдо выпускается в нескольких.
    ///
    /// «Coca Cola, Small» и «Coca Cola, Large» — одно блюдо в двух порциях,
    /// и четыре карточки колы подряд в меню — это шум. Группу считает
    /// конвейер, приложение только показывает её переключателем.
    let size: Size?

    /// Блюда больше нет в меню сети.
    ///
    /// Не прячем: человек мог сохранить его в заказ или прийти по истории,
    /// и «позиция исчезла» выглядело бы как поломка. Вместо этого говорим
    /// прямо — конкурентов ругают именно за молчание об этом.
    let isOffMenu: Bool

    /// Откуда цифра и на какую дату. Приложение обещает это показывать —
    /// конкурентов бьют именно за молчаливо устаревшие данные.
    let source: String
    let observed: String
    let isStale: Bool

    var persistentID: PersistentID { PersistentID(chain: chain, key: key) }

    /// Размерный вариант блюда.
    struct Size: Hashable, Sendable {
        /// Ключ группы. Уникален внутри сети, но не между сетями:
        /// `coca-cola` есть у половины каталога.
        let group: String
        /// Подпись на сегменте: «Small», «12 fl oz».
        let label: String
        /// Порядок слева направо. Считается конвейером по словарю размеров.
        let order: Int
    }

    /// Ссылка на группу размеров, с сетью — иначе колы разных сетей склеятся.
    struct SizeGroupID: Hashable, Sendable {
        let chain: String
        let group: String
    }

    var sizeGroupID: SizeGroupID? {
        size.map { SizeGroupID(chain: chain, group: $0.group) }
    }

    /// Название без размера: «Coca Cola, Large» → «Coca Cola».
    ///
    /// Режем по последней запятой, а не по подписи размера: конвейер собрал
    /// имя ровно так, и обратная операция должна быть той же, иначе
    /// «Iced Coffee, Vanilla, Medium» потеряет ваниль.
    var baseName: String {
        guard size != nil,
              let comma = name.range(of: ",", options: .backwards) else { return name }
        return String(name[..<comma.lowerBound])
    }

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
        self.photo = packItem.photo
        // Три поля приходят вместе или не приходят вовсе.
        if let group = packItem.group, let label = packItem.size {
            self.size = MenuItem.Size(group: group, label: label,
                                      order: packItem.sizeOrder ?? 0)
        } else {
            self.size = nil
        }
        self.isOffMenu = packItem.offMenu ?? false
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
