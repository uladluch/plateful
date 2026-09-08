import Foundation
import Testing

@testable import plateful

@Suite("Снимки конкретных блюд")
struct ItemPhotoTests {

    private static func catalog(photo: [String: Any]?) throws -> MenuCatalog {
        var item: [String: Any] = [
            "chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
            "kcal": 580, "protein": 25, "carbs": 45, "fat": 34, "image": "cheeseburger",
        ]
        if let photo { item["photo"] = photo }
        let json: [String: Any] = [
            "format": 1, "version": 4,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": 1]],
            "items": [item],
        ]
        return MenuCatalog(
            pack: try MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
    }

    @Test("снимок с атрибуцией доезжает из пака")
    func carriesPhoto() throws {
        let catalog = try Self.catalog(photo: [
            "url": "https://example.com/big-mac.jpg",
            "license": "CC BY-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
            "creator": "Anemonemma", "title": "Big Mac.png",
            "page": "https://commons.wikimedia.org/wiki/File:Big_Mac.png",
        ])
        let photo = try #require(catalog.items.first?.photo)

        #expect(photo.url.absoluteString == "https://example.com/big-mac.jpg")
        #expect(photo.license == "CC BY-SA 4.0")
        #expect(photo.creator == "Anemonemma")
    }

    /// У большинства позиций своего снимка нет и не будет — пак обязан
    /// читаться, а картинка браться по архетипу.
    @Test("позиция без снимка остаётся с архетипом")
    func fallsBackToArchetype() throws {
        let item = try #require(try Self.catalog(photo: nil).items.first)
        #expect(item.photo == nil)
        #expect(item.image == "cheeseburger")
    }

    /// Снимок без лицензии — нарушение условий использования, поэтому
    /// поле обязательное и такой пак разбираться не должен.
    @Test("снимок без лицензии отвергает разбор пака")
    func rejectsPhotoWithoutLicense() throws {
        #expect(throws: MenuPack.LoadError.self) {
            _ = try Self.catalog(photo: ["url": "https://example.com/x.jpg"])
        }
    }

    /// Опубликованный пак должен нести снимки — иначе выкладка прошла,
    /// а данные до приложения не доехали. Версия берётся из манифеста,
    /// чтобы тест не устаревал с каждым релизом пака.
    @Test("в опубликованном паке есть снимки блюд")
    func publishedPackHasPhotos() async throws {
        let (manifestData, _) = try await URLSession.shared.data(from: PackUpdater.manifestURL)
        let manifest = try PackManifest.decode(from: manifestData)
        let (data, _) = try await URLSession.shared.data(from: manifest.url)
        let raw = try #require((data as NSData).decompressed(using: .zlib) as Data?)
        let pack = try MenuPack.decode(from: raw)

        let withPhoto = pack.items.filter { $0.photo != nil }
        #expect(withPhoto.count >= 5, "снимков в паке: \(withPhoto.count)")
        #expect(withPhoto.allSatisfy { !($0.photo?.license.isEmpty ?? true) })
    }
}
