import Foundation
import Testing

@testable import plateful

@Suite("Нормализация и сопоставление")
struct TextIndexTests {

    private func normalized(_ text: String) -> String {
        String(decoding: TextIndex.normalized(text), as: UTF8.self)
    }

    @Test("регистр, дефисы и пунктуация схлопываются в пробелы")
    func collapsesPunctuation() {
        #expect(normalized("Chick-Fil-A") == "chick fil a")
        #expect(normalized("  Big   Mac  ") == "big mac")
        #expect(normalized("Bacon, Egg & Cheese") == "bacon egg cheese")
        #expect(normalized("") == "")
        #expect(normalized("   ") == "")
    }

    /// Пишут «mcdonalds», а не «mcdonald's». Если апостроф станет пробелом,
    /// запрос не найдёт ничего — это ловил живой прогон по каталогу.
    @Test("апостроф выпадает, а не разделяет")
    func dropsApostrophes() {
        #expect(normalized("McDonald's") == "mcdonalds")
        #expect(normalized("Wendy\u{2019}s") == "wendys")
        #expect(normalized("Dunkin' Donuts") == "dunkin donuts")
    }

    @Test("диакритика снимается")
    func foldsDiacritics() {
        #expect(normalized("Crème Brûlée") == "creme brulee")
    }

    @Test("совпадение оценивается по позиции в строке")
    func ranksByPosition() {
        let text = ArraySlice(TextIndex.normalized("big mac sauce"))
        #expect(TextIndex.match(Array("big".utf8), in: text) == .leading)
        #expect(TextIndex.match(Array("mac".utf8), in: text) == .wordStart)
        #expect(TextIndex.match(Array("auce".utf8), in: text) == .inside)
        #expect(TextIndex.match(Array("zzz".utf8), in: text) == .none)
    }

    @Test("запрос длиннее строки не совпадает")
    func rejectsOverlongToken() {
        let text = ArraySlice(TextIndex.normalized("mac"))
        #expect(TextIndex.match(Array("macaroni".utf8), in: text) == .none)
        #expect(TextIndex.match([], in: text) == .none)
    }
}
