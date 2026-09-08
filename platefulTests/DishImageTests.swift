import Foundation
import Testing
import UIKit

@testable import plateful

@Suite("Заглушка блюда")
struct DishPlaceholderTests {

    /// Символ должен существовать в системе: несуществующее имя рисуется
    /// пустотой, и строка выглядит сломанной.
    @Test("все символы заглушек есть в SF Symbols")
    func symbolsExist() {
        let archetypes = ["coffee", "soda", "water", "wine", "cake", "salad",
                          "seafood", "chips", "fries", "cheeseburger", nil,
                          "неизвестный-архетип"]
        for archetype in archetypes {
            let name = DishPlaceholder.symbol(for: archetype)
            #expect(UIImage(systemName: name) != nil, "нет символа \(name)")
        }
    }

    @Test("напитки, десерты и еда различаются на вид")
    func symbolsAreDistinct() {
        #expect(DishPlaceholder.symbol(for: "coffee") != DishPlaceholder.symbol(for: "cake"))
        #expect(DishPlaceholder.symbol(for: "salad") != DishPlaceholder.symbol(for: "fries"))
    }

    /// Неизвестный архетип не должен ронять экран: приложение переживает
    /// пак, выпущенный с новыми типами блюд.
    @Test("неизвестный архетип даёт общий символ")
    func unknownFallsBack() {
        #expect(DishPlaceholder.symbol(for: "чего-то-новое") == "fork.knife")
        #expect(DishPlaceholder.symbol(for: nil) == "fork.knife")
    }
}
