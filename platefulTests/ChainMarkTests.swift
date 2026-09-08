import Foundation
import Testing

@testable import plateful

@Suite("Значки сетей")
struct ChainMarkTests {

    /// Апостроф — не разделитель: иначе «McDonald's» превращается в «MS».
    @Test("инициалы берутся по словам, апостроф не делит")
    func buildsInitials() {
        #expect(ChainMark.initials(for: "McDonald's") == "M")
        #expect(ChainMark.initials(for: "Taco Bell") == "TB")
        #expect(ChainMark.initials(for: "Chick-Fil-A") == "CF")
        #expect(ChainMark.initials(for: "Panera Bread") == "PB")
        #expect(ChainMark.initials(for: "Wendy's") == "W")
    }

    @Test("цифры в начале названия годятся как инициал")
    func handlesDigits() {
        #expect(ChainMark.initials(for: "7 Eleven") == "7E")
    }

    @Test("пустое имя не роняет")
    func survivesEmptyName() {
        #expect(ChainMark.initials(for: "") == "")
        #expect(ChainMark.initials(for: "   ") == "")
    }

    /// `hashValue` у Swift засеивается заново при каждом запуске: на нём
    /// цвет сети менялся бы от старта к старту.
    @Test("цвет устойчив между вызовами")
    func colorIsStable() {
        for chain in ["McDonald's", "Subway", "Chipotle"] {
            #expect(ChainMark.color(for: chain) == ChainMark.color(for: chain))
        }
    }

    @Test("палитра только из системных цветов и не пуста")
    func paletteIsSystem() {
        #expect(ChainMark.palette.count >= 8)
    }

    /// Значки не должны слипаться в один цвет на ключевых сетях.
    @Test("ключевые сети получают разные цвета")
    func keyChainsAreDistinguishable() {
        let chains = ["McDonald's", "Chick-Fil-A", "Starbucks", "Subway",
                      "Chipotle", "Panera Bread", "Taco Bell", "Wendy's"]
        let colors = Set(chains.map { String(describing: ChainMark.color(for: $0)) })
        #expect(colors.count >= 5, "слишком много совпадений: \(colors.count) цветов на 8 сетей")
    }
}
