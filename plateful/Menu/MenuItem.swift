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

    /// Остальная этикетка: сахар, жиры, холестерин, натрий, клетчатка.
    ///
    /// Необязательные, и это не формальность: «нет числа» значит, что сеть
    /// его не публикует, а не что там ноль. Показывать ноль вместо пробела
    /// у сахара — прямой вред тому, кто его считает.
    let sugar: Double?
    let satFat: Double?

    /// Трансжиры. Почти везде ноль — и именно поэтому их стоит показывать:
    /// единица там, где ждёшь ноль, сама по себе повод выбрать другое.
    let transFat: Double?

    /// Холестерин, в миллиграммах.
    let cholesterol: Double?

    let sodium: Double?
    let fiber: Double?

    /// Архетип блюда — имя изображения в каталоге ассетов.
    ///
    /// Не фотография конкретной позиции сети: снимок общий для всех
    /// чизбургеров, потому что чизбургер выглядит чизбургером везде.
    let image: String?

    /// Снимок именно этого блюда. Где его нет, показывается картинка
    /// по архетипу — она есть всегда.
    let photo: MenuPack.Photo?

    /// Пометки позиции. Множество, а не набор булевых свойств: термины
    /// приходят из пака и там открыты — адаптер сети добавит свои.
    ///
    /// Незнакомый термин молча отбрасывается, а не ломает разбор: пак
    /// обновляется публикацией, приложение — релизом, и старая версия
    /// обязана прочитать новый пак.
    let flags: Set<Flag>

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

    /// Пометка позиции.
    ///
    /// Порядок объявления — порядок показа: сперва что это за порция,
    /// потом где и когда её можно застать.
    enum Flag: String, CaseIterable, Hashable, Sendable {
        /// Детская порция.
        case kids
        /// Порция на компанию — этим и объясняются её калории.
        case shareable
        /// Есть не во всех точках сети.
        case regional
        /// На момент снятия данных блюдо было сезонным.
        ///
        /// Не «действует до»: срок из снимка 2018 года давно истёк. Это
        /// признак того, что блюда, скорее всего, уже нет, — и лучший из
        /// имеющихся там, где присутствие в меню никто не проверял.
        case seasonal
    }

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
        /// Название без варианта. Пусто у паков, выпущенных до того, как
        /// конвейер начал его считать.
        let base: String?

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
    /// Берём из пака, а не режем имя сами: правило отрезания знает только
    /// конвейер, и первая же попытка повторить его здесь разошлась с ним в
    /// регистре единицы («3 piece» против «3 Piece»). Пак без базы — старый;
    /// там честнее показать полное имя, чем угадывать.
    var baseName: String {
        variant?.base ?? name
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
        self.sugar = packItem.sugar
        self.satFat = packItem.satFat
        self.transFat = packItem.transFat
        self.cholesterol = packItem.cholesterol
        self.sodium = packItem.sodium
        self.fiber = packItem.fiber
        self.image = packItem.image
        self.photo = packItem.photo
        self.variant = packItem.variant.map {
            MenuItem.Variant(group: $0.group, label: $0.label, order: $0.order,
                             kind: MenuItem.Variant.Kind(pack: $0.kind), base: $0.base)
        }
        self.flags = Set((packItem.flags ?? []).compactMap(Flag.init(rawValue:)))
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

    /// Насколько дорого в этой сети: 1 = `$`, 4 = `$$$$`.
    ///
    /// Полоса по сети, а не средний чек по ресторану: чека по конкретной
    /// точке нет ни в одном открытом источнике, а придумывать его нельзя.
    /// `nil` — полосу не проставляли.
    let priceTier: Int?

    init(name: String, itemCount: Int, priceTier: Int? = nil) {
        self.name = name
        self.itemCount = itemCount
        self.priceTier = priceTier
    }

    /// `$$` — то, как эту полосу пишут везде, включая карточку места Apple.
    var priceBand: String? {
        guard let priceTier, (1...4).contains(priceTier) else { return nil }
        return String(repeating: "$", count: priceTier)
    }
}
