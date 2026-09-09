import Foundation

/// Контракт пака — ровно то, что пишет `backend/plateful_data/pack.py`.
///
/// Один формат у сида в бандле и у скачанного обновления: у репозитория
/// должен быть ровно один декодер, иначе два пути разойдутся.
// Проект собирается с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor — это верно
// для SwiftUI, но не для слоя данных: каталог разбирается и строится вне
// главного потока. Отсюда `nonisolated` на типах ниже.
nonisolated struct MenuPack: Decodable, Sendable {

    /// Формат, который умеет читать эта версия приложения. Пак с другим
    /// номером отвергаем целиком: молча прочитать половину полей хуже,
    /// чем остаться на сиде.
    static let supportedFormat = 1

    let format: Int
    let version: Int

    /// Происхождение по умолчанию. У позиции те же поля появляются только
    /// там, где отличаются — после ручной правки в `overrides`.
    let source: String
    let observed: String
    let stale: Bool

    /// Порядок разделов меню, один на весь каталог. Приходит из пака, а не
    /// зашит в приложение: у источника порядка нет вовсе, и менять его
    /// хочется публикацией, а не релизом.
    let sections: [String]?

    let chains: [Chain]
    let items: [Item]

    /// Фотография блюда с обязательной атрибуцией.
    ///
    /// Лицензия и автор — не украшение: CC BY и BY-SA требуют их указать,
    /// поэтому в модели они не опциональны рядом с самим снимком.
    struct Photo: Decodable, Sendable, Hashable {
        let url: URL
        let license: String
        let licenseUrl: URL?
        let creator: String?
        let title: String?
        let page: URL?
        /// `contain` — вписать целиком: у предметной съёмки на прозрачном
        /// фоне обрезка отъедает края. Иначе кадрируем по заполнению.
        let fit: String?

        var fitsInside: Bool { fit == "contain" }
    }

    /// Вариант блюда: «Small», «10», «w/ Egg».
    struct Variant: Decodable, Sendable, Hashable {
        /// Ключ группы. Уникален внутри сети, но не между сетями:
        /// `coca-cola` есть у половины каталога.
        let group: String
        let label: String
        let order: Int
        /// `size` — порция, `option` — исполнение. Порции сокращаются до
        /// буквы, опции нет: «Egg» не сократить.
        let kind: String
        /// Название без варианта: «Chicken McNuggets» для «10 Chicken
        /// McNuggets». Считает конвейер: правило отрезания знает только тот,
        /// кто отрезал. Необязательное — паки до v14 его не несут.
        let base: String?
    }

    struct Chain: Decodable, Sendable {
        let name: String
        let itemCount: Int
        /// 1 = `$`, 4 = `$$$$`. Поля нет у сетей, которым полосу не
        /// проставили: паки до v31 не несут его вовсе.
        let priceTier: Int?
    }

    struct Item: Decodable, Sendable {
        let chain: String
        let key: String
        let name: String
        let category: String?
        let serving: String?
        let kcal: Double
        let protein: Double
        let carbs: Double
        let fat: Double

        /// Остальная этикетка. Источник раскрывает её наравне с калориями,
        /// поэтому она есть почти везде — но не везде, и «нет числа» это не
        /// «ноль».
        let sugar: Double?
        let satFat: Double?
        let transFat: Double?
        let cholesterol: Double?
        let sodium: Double?
        let fiber: Double?

        /// Архетип блюда: по нему подбирается снимок. Необязательный —
        /// паки, выпущенные до появления картинок, его не несут.
        let image: String?

        /// Снимок именно этого блюда, если он найден. Есть у немногих позиций.
        let photo: Photo?

        /// Раздел меню. Категория источника, а поверх неё выделенный
        /// завтрак: он не категория, а время дня, и в источнике размазан
        /// по сэндвичам и горячему.
        let section: String?

        /// Порция или опция одного блюда. Позиции с одинаковым `group`
        /// внутри сети приложение показывает одной карточкой.
        let variant: Variant?

        /// Пометки позиции: детская порция, на компанию, не во всех точках,
        /// сезонное. Строками, а не набором булевых полей: словарь открытый,
        /// адаптеры сетей добавят к нему своё, и пак с незнакомым термином
        /// обязан читаться старым приложением.
        let flags: [String]?

        /// Позиции больше нет в меню сети. Приходит только когда это правда.
        let offMenu: Bool?

        let source: String?
        let observed: String?
        let stale: Bool?
    }
}

nonisolated extension MenuPack {

    enum LoadError: Error, LocalizedError, Sendable {
        case unsupportedFormat(Int)
        case empty
        case malformed(String)
        case checksumMismatch
        case decompressionFailed
        case noPackAvailable

        var errorDescription: String? {
            switch self {
            case .unsupportedFormat(let format):
                "Формат пака \(format) не поддерживается, нужен \(MenuPack.supportedFormat)"
            case .empty:
                "В паке нет ни одной позиции"
            case .malformed(let detail):
                "Пак не разобрался: \(detail)"
            case .checksumMismatch:
                "Контрольная сумма пака не совпала"
            case .decompressionFailed:
                "Пак не распаковался"
            case .noPackAvailable:
                "Не найден ни скачанный пак, ни сид в бандле"
            }
        }
    }

    /// Любая неудача разбора выходит наружу как `LoadError`.
    ///
    /// Повреждённые байты ведут себя по-разному: иногда не распаковываются
    /// вовсе, иногда распаковываются в мусор, и тогда падает уже JSONDecoder.
    /// Вызывающему это различие не нужно — ему нужно одно решение: остаться
    /// на том паке, который уже работает.
    static func decode(from data: Data) throws -> MenuPack {
        let pack: MenuPack
        do {
            pack = try JSONDecoder().decode(MenuPack.self, from: data)
        } catch let error as LoadError {
            throw error
        } catch {
            throw LoadError.malformed(String(describing: error))
        }
        guard pack.format == supportedFormat else {
            throw LoadError.unsupportedFormat(pack.format)
        }
        guard !pack.items.isEmpty else { throw LoadError.empty }
        return pack
    }
}
