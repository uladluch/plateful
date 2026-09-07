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

    let chains: [Chain]
    let items: [Item]

    struct Chain: Decodable, Sendable {
        let name: String
        let itemCount: Int
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

        let source: String?
        let observed: String?
        let stale: Bool?
    }
}

nonisolated extension MenuPack {

    enum LoadError: Error, LocalizedError, Sendable {
        case unsupportedFormat(Int)
        case empty
        case checksumMismatch
        case decompressionFailed
        case noPackAvailable

        var errorDescription: String? {
            switch self {
            case .unsupportedFormat(let format):
                "Формат пака \(format) не поддерживается, нужен \(MenuPack.supportedFormat)"
            case .empty:
                "В паке нет ни одной позиции"
            case .checksumMismatch:
                "Контрольная сумма пака не совпала"
            case .decompressionFailed:
                "Пак не распаковался"
            case .noPackAvailable:
                "Не найден ни скачанный пак, ни сид в бандле"
            }
        }
    }

    static func decode(from data: Data) throws -> MenuPack {
        let pack = try JSONDecoder().decode(MenuPack.self, from: data)
        guard pack.format == supportedFormat else {
            throw LoadError.unsupportedFormat(pack.format)
        }
        guard !pack.items.isEmpty else { throw LoadError.empty }
        return pack
    }
}
