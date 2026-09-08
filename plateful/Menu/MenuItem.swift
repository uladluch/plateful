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

    /// Раздел меню, в котором показывается позиция. Считает конвейер:
    /// правило одно на 96 сетей, и ошибку в нём чинит публикация пака.
    let section: String

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

    /// Вариант блюда, если оно выпускается в нескольких.
    ///
    /// «Coca Cola, Small» и «Coca Cola, Large» — одно блюдо в двух порциях;
    /// «Big Breakfast» и «Big Breakfast w/ Hotcakes» — в двух исполнениях.
    /// В обоих случаях четыре карточки подряд — это шум. Группу считает
    /// конвейер, приложение только показывает её переключателем.
    let variant: Variant?

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

    /// Вариант блюда: порция или исполнение.
    struct Variant: Hashable, Sendable {
        /// Ключ группы. Уникален внутри сети, но не между сетями:
        /// `coca-cola` есть у половины каталога.
        let group: String
        /// Подпись на сегменте: «Small», «12 fl oz», «Egg».
        let label: String
        /// Порядок слева направо. Считается конвейером.
        let order: Int
        let kind: Kind

        /// Порция меняет количество, исполнение — состав. Приложению это
        /// нужно для двух вещей: подписи под названием («4 sizes» против
        /// «3 options») и сокращений — «Large» становится «L», «Egg» нет.
        enum Kind: String, Sendable {
            case size
            case option

            init(pack value: String) { self = Kind(rawValue: value) ?? .size }
        }
    }

    /// Ссылка на группу вариантов, с сетью — иначе колы разных сетей склеятся.
    struct VariantGroupID: Hashable, Sendable {
        let chain: String
        let group: String
    }

    var variantGroupID: VariantGroupID? {
        variant.map { VariantGroupID(chain: chain, group: $0.group) }
    }

    /// Название без варианта: «Coca Cola, Large» → «Coca Cola»,
    /// «10 Chicken McNuggets» → «Chicken McNuggets».
    ///
    /// Отрезаем ровно то, что конвейер приписал: он собирал имя из базы и
    /// подписи, и обратная операция должна быть той же, иначе
    /// «Iced Coffee, Vanilla, Medium» потеряет ваниль.
    var baseName: String {
        guard let variant else { return name }
        if let comma = name.range(of: ", \(variant.label)", options: [.backwards, .anchored]) {
            return String(name[..<comma.lowerBound])
        }
        if let separator = name.range(of: " w/ ", options: .backwards),
           variant.kind == .option {
            return String(name[..<separator.lowerBound])
        }
        if name.hasPrefix(variant.label) {
            return String(name.dropFirst(variant.label.count)).trimmingCharacters(
                in: .whitespaces)
        }
        return name
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
        self.section = packItem.section ?? packItem.category ?? MenuSection.uncategorized
        self.serving = packItem.serving
        self.kcal = packItem.kcal
        self.protein = packItem.protein
        self.carbs = packItem.carbs
        self.fat = packItem.fat
        self.image = packItem.image
        self.photo = packItem.photo
        self.variant = packItem.variant.map {
            MenuItem.Variant(group: $0.group, label: $0.label, order: $0.order,
                             kind: MenuItem.Variant.Kind(pack: $0.kind))
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
