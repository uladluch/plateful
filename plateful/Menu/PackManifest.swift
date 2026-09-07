import Foundation

// Проект собран с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor; манифест —
// значение, разбирается вне главного потока.

/// Манифест последнего опубликованного пака.
///
/// Пишется конвейером (`backend/plateful_data/pack.py::manifest`) и лежит в
/// публичном бакете Supabase Storage с коротким кэшем.
nonisolated struct PackManifest: Decodable, Sendable, Equatable {

    let format: Int
    let version: Int
    let url: URL
    /// Хеш **сжатых** байтов: клиент проверяет ещё до распаковки.
    let sha256: String
    let itemCount: Int
    let releasedAt: String

    static func decode(from data: Data) throws -> PackManifest {
        let manifest: PackManifest
        do {
            manifest = try JSONDecoder().decode(PackManifest.self, from: data)
        } catch {
            throw MenuPack.LoadError.malformed(String(describing: error))
        }
        guard manifest.format == MenuPack.supportedFormat else {
            throw MenuPack.LoadError.unsupportedFormat(manifest.format)
        }
        return manifest
    }
}
