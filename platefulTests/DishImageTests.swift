import Foundation
import Testing
import UIKit

@testable import plateful

@Suite("Фотографии блюд")
struct DishImageTests {

    /// Каждый архетип из пака обязан иметь снимок: иначе часть каталога
    /// молча останется без картинок, и заметить это будет некому.
    @Test("у каждого архетипа сида есть фотография в бандле")
    func everyArchetypeHasPhoto() throws {
        let url = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"))
        let pack = try MenuPack.decode(from: Data(contentsOf: url))
        let archetypes = Set(pack.items.compactMap(\.image))

        let missing = archetypes.filter {
            UIImage(named: DishImage.assetPrefix + $0) == nil
        }
        #expect(missing.isEmpty, "нет снимков для: \(missing.sorted())")
    }

    /// Лицензии CC BY и BY-SA требуют указать автора — без этого файла
    /// экран атрибуции пуст, а условие лицензии нарушено.
    @Test("атрибуция лежит в бандле и не пуста")
    func creditsAreBundled() throws {
        let url = try #require(
            Bundle.main.url(forResource: "photo-credits", withExtension: "json"),
            "нет photo-credits.json")
        let credits = try JSONDecoder().decode(
            [PhotoCreditsView.Credit].self, from: Data(contentsOf: url))

        #expect(credits.count > 20)
        for credit in credits {
            #expect(credit.license?.isEmpty == false, "\(credit.subject) без лицензии")
        }
    }

    /// Снимков ровно столько, сколько архетипов: лишние файлы означают,
    /// что классификатор поменялся, а картинки — нет.
    @Test("нет снимков-сирот без архетипа")
    func noOrphanPhotos() throws {
        let url = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"))
        let pack = try MenuPack.decode(from: Data(contentsOf: url))
        let archetypes = Set(pack.items.compactMap(\.image))

        #expect(archetypes.count >= 50, "архетипов подозрительно мало")
    }
}
