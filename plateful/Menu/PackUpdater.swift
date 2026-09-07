import Foundation
import OSLog

/// Откуда приложение берёт обновления каталога.
///
/// Подменяется в тестах, чтобы не ходить в сеть.
nonisolated protocol PackTransport: Sendable {
    func data(from url: URL) async throws -> Data
}

nonisolated struct NetworkPackTransport: PackTransport {

    let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func data(from url: URL) async throws -> Data {
        let (data, response) = try await session.data(from: url)
        guard let http = response as? HTTPURLResponse else { return data }
        guard (200..<300).contains(http.statusCode) else {
            throw PackUpdater.UpdateError.badResponse(http.statusCode)
        }
        return data
    }
}

/// Проверяет манифест и ставит новый пак.
///
/// Обновление — вещь необязательная: сид в бандле уже работает, поэтому любая
/// неудача здесь тихо оставляет приложение на том, что есть.
nonisolated struct PackUpdater: Sendable {

    static let manifestURL = URL(
        string: "https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/packs/manifest.json")!

    enum UpdateError: Error, LocalizedError, Sendable {
        case badResponse(Int)
        case untrustedPackHost(String?)

        var errorDescription: String? {
            switch self {
            case .badResponse(let code): "Сервер ответил \(code)"
            case .untrustedPackHost(let host): "Пак с чужого хоста: \(host ?? "неизвестен")"
            }
        }
    }

    enum Outcome: Sendable, Equatable {
        case upToDate(version: Int)
        case installed(version: Int, itemCount: Int)
    }

    let store: PackStore
    let transport: PackTransport
    let manifestURL: URL

    init(store: PackStore,
         transport: PackTransport = NetworkPackTransport(),
         manifestURL: URL = PackUpdater.manifestURL) {
        self.store = store
        self.transport = transport
        self.manifestURL = manifestURL
    }

    /// Скачивает манифест и, если пак новее, ставит его.
    func update(currentVersion: Int) async throws -> Outcome {
        let manifest = try PackManifest.decode(from: try await transport.data(from: manifestURL))

        guard manifest.version > currentVersion else {
            return .upToDate(version: currentVersion)
        }

        // Манифест мы получили по HTTPS со своего хоста, но ссылку внутри него
        // всё равно проверяем: подменённый манифест не должен уводить загрузку
        // на чужой сервер.
        guard manifest.url.host() == manifestURL.host() else {
            throw UpdateError.untrustedPackHost(manifest.url.host())
        }

        let compressed = try await transport.data(from: manifest.url)
        let result = try store.install(
            compressed: compressed,
            expectedSHA256: manifest.sha256,
            newerThan: currentVersion)

        return switch result {
        case .installed(let pack): .installed(version: pack.version, itemCount: pack.items.count)
        case .skipped(let version): .upToDate(version: version)
        }
    }
}
