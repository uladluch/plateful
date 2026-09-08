import Foundation
import Testing
import UIKit

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

    /// Слаг в приложении и слаг в конвейере обязаны совпадать: по нему
    /// ищется файл логотипа, и расхождение оставило бы сеть без картинки.
    @Test("слаг совпадает с тем, что делает конвейер")
    func slugMatchesPipeline() {
        #expect(ChainMark.slug(for: "McDonald's") == "mcdonald-s")
        #expect(ChainMark.slug(for: "Chick-Fil-A") == "chick-fil-a")
        #expect(ChainMark.slug(for: "7 Eleven") == "7-eleven")
        #expect(ChainMark.slug(for: "Dunkin' Donuts") == "dunkin-donuts")
        #expect(ChainMark.slug(for: "BJ's Restaurant & Brewhouse")
                == "bj-s-restaurant-brewhouse")
        #expect(ChainMark.slug(for: "") == "")
    }

    /// Логотип ищется по слагу; если ассет не находится, сеть молча получает
    /// инициалы — и никто не заметит, что картинка пропала.
    @Test("логотипы ключевых сетей лежат в бандле")
    func keyLogosAreBundled() {
        for chain in ["McDonald's", "Chick-Fil-A", "Starbucks", "Subway", "Taco Bell"] {
            let name = ChainMarkView.logoPrefix + ChainMark.slug(for: chain)
            #expect(UIImage(named: name) != nil, "нет ассета \(name)")
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
