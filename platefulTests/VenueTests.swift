import Foundation
import Testing
@testable import plateful

/// Заведения, найденные картой: группировка по сетям и то, что к ним
/// пририсовано. Всё без карты — правила наши.
@Suite("Заведения")
struct VenueTests {

    // MARK: - Группировка по сетям

    static func venue(_ chain: String, _ metres: Double, key: String = "1") -> Venue {
        Venue(chain: chain, extKey: key, latitude: 40.7, longitude: -74.0,
              address: "\(key) Main St", phone: nil, distance: metres)
    }

    @Test("сети идут ближайшими вперёд, с числом точек")
    func groupsByChain() {
        let chains = NearbyMatch.chains(from: [
            Self.venue("Popeyes", 800, key: "a"),
            Self.venue("Burger King", 120, key: "b"),
            Self.venue("Popeyes", 300, key: "c"),
        ])

        #expect(chains.map(\.chain) == ["Burger King", "Popeyes"])
        #expect(chains.last?.venues == 2)
        #expect(chains.last?.nearest.extKey == "c")
    }

    // MARK: - Полоса цены

    @Test("полоса рисуется долларами по числу")
    func priceBand() {
        #expect(MenuChain(name: "X", itemCount: 1, priceTier: 1).priceBand == "$")
        #expect(MenuChain(name: "X", itemCount: 1, priceTier: 4).priceBand == "$$$$")
    }

    /// «Не проставили» и «бесплатно» — разные вещи, и пустая строка вместо
    /// полосы честнее любой цифры.
    @Test("без полосы ничего не показываем")
    func missingPriceBand() {
        #expect(MenuChain(name: "X", itemCount: 1).priceBand == nil)
        #expect(MenuChain(name: "X", itemCount: 1, priceTier: 0).priceBand == nil)
        #expect(MenuChain(name: "X", itemCount: 1, priceTier: 9).priceBand == nil)
    }

    @Test("пак без полосы читается по-прежнему")
    func packWithoutPriceTier() throws {
        let json = #"{"name": "Popeyes", "itemCount": 169}"#
        let chain = try JSONDecoder().decode(MenuPack.Chain.self,
                                             from: Data(json.utf8))

        #expect(chain.priceTier == nil)
        #expect(chain.itemCount == 169)
    }

    // MARK: - Снимок заведения

    /// Кадр строки и кадр шапки — разные картинки, и общий ключ подсунул
    /// бы карточке растянутый кадр строки.
    @Test("размер входит в ключ кадра")
    func snapshotKeyIncludesSize() {
        let venue = Self.venue("Popeyes", 100, key: "12345")

        #expect(VenueSnapshot.key(venue, side: 168) == "Popeyes#12345@168")
        #expect(VenueSnapshot.key(venue, side: 168)
                != VenueSnapshot.key(venue, side: 660))
    }

    @Test("две точки одной сети — разные кадры")
    func snapshotKeySeparatesVenues() {
        let near = Self.venue("McDonald's", 120, key: "39147")
        let next = Self.venue("McDonald's", 800, key: "10074")

        #expect(VenueSnapshot.key(near, side: 168)
                != VenueSnapshot.key(next, side: 168))
    }
}
