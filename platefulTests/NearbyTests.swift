import Testing
@testable import plateful

/// Сопоставление того, что показала карта, с каталогом.
///
/// Проверяется без MapKit намеренно: правило про имена — наше, а поход
/// в карту сделал бы тест зависимым от того, что сегодня стоит рядом с
/// машиной, на которой он идёт.
@Suite("Рядом")
struct NearbyTests {

    private static func place(_ name: String, _ metres: Double,
                              address: String? = nil) -> NearbyPlace {
        NearbyPlace(name: name, distance: metres, address: address,
                    latitude: 40.7, longitude: -74.0)
    }

    private static let catalog = [
        "McDonald's", "Chick-Fil-A", "Subway", "Starbucks", "Sonic",
        "Panda Express", "Wendy's", "Taco Bell",
    ]

    @Test("карта пишет имя иначе, чем каталог")
    func normalisesNames() {
        // Карта: «Chick-fil-A». Каталог: «Chick-Fil-A».
        let found = NearbyMatch.chains(
            near: [Self.place("Chick-fil-A", 100)], in: Self.catalog)

        #expect(found.map(\.chain) == ["Chick-Fil-A"])
    }

    @Test("апостроф не мешает")
    func apostropheIsIgnored() {
        let found = NearbyMatch.chains(
            near: [Self.place("McDonalds", 50)], in: Self.catalog)

        #expect(found.first?.chain == "McDonald's")
    }

    @Test("хвост в названии заведения не мешает")
    func matchesWithTrailingWords() {
        let found = NearbyMatch.chains(
            near: [Self.place("Starbucks Coffee", 120),
                   Self.place("Sonic Drive-In", 300)], in: Self.catalog)

        #expect(Set(found.map(\.chain)) == ["Starbucks", "Sonic"])
    }

    /// Имена сетей коротки, и подстрока ловит чужое.
    @Test("похожее слово не считается сетью")
    func requiresWordBoundary() {
        let found = NearbyMatch.chains(
            near: [Self.place("Sonicare Dental", 40),
                   Self.place("Subwaystation Deli", 60)], in: Self.catalog)

        #expect(found.isEmpty)
    }

    @Test("из двух подходящих сетей берётся точная")
    func longestChainWins() {
        let catalog = Self.catalog + ["Panda"]
        let found = NearbyMatch.chains(
            near: [Self.place("Panda Express", 200)], in: catalog)

        #expect(found.map(\.chain) == ["Panda Express"])
    }

    @Test("чужие заведения отбрасываются")
    func ignoresUnknownPlaces() {
        let found = NearbyMatch.chains(
            near: [Self.place("Joe's Pizza", 30),
                   Self.place("Subway", 500)], in: Self.catalog)

        #expect(found.map(\.chain) == ["Subway"])
    }

    @Test("ближайшие первыми")
    func sortsByDistance() {
        let found = NearbyMatch.chains(
            near: [Self.place("Subway", 900),
                   Self.place("Wendy's", 120),
                   Self.place("Taco Bell", 400)], in: Self.catalog)

        #expect(found.map(\.chain) == ["Wendy's", "Taco Bell", "Subway"])
    }

    /// У сети рядом бывает несколько точек — показываем ближайшую.
    @Test("из нескольких заведений сети берётся ближайшее")
    func keepsTheNearestVenue() {
        let found = NearbyMatch.chains(
            near: [Self.place("Subway", 800, address: "Far St"),
                   Self.place("Subway", 150, address: "Near St"),
                   Self.place("Subway", 400, address: "Middle St")],
            in: Self.catalog)

        #expect(found.count == 1)
        #expect(found.first?.nearest.address == "Near St")
        #expect(found.first?.venues == 3)
    }

    @Test("пустой каталог никого не находит")
    func emptyCatalogFindsNothing() {
        #expect(NearbyMatch.chains(near: [Self.place("Subway", 10)], in: []).isEmpty)
    }

    // MARK: - Каталог по одному заведению
    //
    // Тем же правилом, что и список сетей, пользуется карта: булавка
    // ставится на каждое заведение, и каждому нужно знать свою сеть.

    @Test("каталог узнаёт сеть в имени заведения")
    func catalogNamesTheChain() {
        let index = NearbyCatalog(Self.catalog)

        #expect(index.chain(of: "Chick-fil-A") == "Chick-Fil-A")
        #expect(index.chain(of: "Starbucks Coffee") == "Starbucks")
        #expect(index.chain(of: "McDonalds") == "McDonald's")
    }

    @Test("каталог не выдаёт чужое за сеть")
    func catalogRejectsStrangers() {
        let index = NearbyCatalog(Self.catalog)

        #expect(index.chain(of: "Sonicare Dental") == nil)
        #expect(index.chain(of: "Joe's Pizza") == nil)
        #expect(index.chain(of: "") == nil)
    }

    @Test("каталог берёт самую длинную подходящую сеть")
    func catalogPrefersTheLongestChain() {
        let index = NearbyCatalog(Self.catalog + ["Panda"])

        #expect(index.chain(of: "Panda Express") == "Panda Express")
        #expect(index.chain(of: "Panda Inn") == "Panda")
    }

    @Test("расстояние показывается в единицах системы")
    func formatsDistance() {
        let text = NearbyView.distance(1_200)

        #expect(!text.isEmpty)
        #expect(text.rangeOfCharacter(from: .decimalDigits) != nil)
    }
}
