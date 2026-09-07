import Foundation

/// Нормализованные названия одним плоским буфером.
///
/// 25 тысяч позиций × два поля — это 50 тысяч отдельных строк, если хранить
/// их как `[String]`. Один буфер плюс смещения дешевле и по памяти, и по
/// скорости: сравнение идёт по байтам, без работы со строками Swift.
// Проект собирается с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor — это верно
// для SwiftUI, но не для слоя данных: каталог разбирается и строится вне
// главного потока. Отсюда `nonisolated` на типах ниже.
nonisolated struct TextIndex: Sendable {

    static let space: UInt8 = 32

    private let nameBytes: ContiguousArray<UInt8>
    private let nameStarts: [Int32]
    private let chainBytes: ContiguousArray<UInt8>
    private let chainStarts: [Int32]

    init(names: Buffer, chains: Buffer) {
        self.nameBytes = names.bytes
        self.nameStarts = names.starts
        self.chainBytes = chains.bytes
        self.chainStarts = chains.starts
    }

    func name(_ index: Int) -> ArraySlice<UInt8> {
        nameBytes[Int(nameStarts[index])..<Int(nameStarts[index + 1])]
    }

    func chain(_ index: Int) -> ArraySlice<UInt8> {
        chainBytes[Int(chainStarts[index])..<Int(chainStarts[index + 1])]
    }

    // MARK: - Сборка

    struct Buffer: Sendable {
        let bytes: ContiguousArray<UInt8>
        let starts: [Int32]
    }

    struct Builder {
        private var bytes = ContiguousArray<UInt8>()
        private var starts: [Int32] = [0]

        init(capacity: Int) {
            bytes.reserveCapacity(capacity * 24)
            starts.reserveCapacity(capacity + 1)
        }

        mutating func append(_ text: String) {
            bytes.append(contentsOf: TextIndex.normalized(text))
            starts.append(Int32(bytes.count))
        }

        func build() -> Buffer { Buffer(bytes: bytes, starts: starts) }
    }

    // MARK: - Нормализация

    /// Регистр, диакритика и пунктуация схлопываются, чтобы «Chick-fil-A»
    /// находился по «chick fil a», а «Crème Brûlée» — по «creme brulee».
    ///
    /// Апостроф — исключение: он не разделитель, а выпадает целиком. Иначе
    /// «McDonald's» станет «mcdonald s», и запрос «mcdonalds» не найдёт
    /// ничего — а пишут его именно так, без апострофа.
    static func normalized(_ text: String) -> [UInt8] {
        let folded = text
            .replacingOccurrences(of: "'", with: "")
            .replacingOccurrences(of: "\u{2019}", with: "")
            .folding(
                options: [.diacriticInsensitive, .caseInsensitive, .widthInsensitive],
                locale: nil)

        var out: [UInt8] = []
        out.reserveCapacity(folded.utf8.count)
        var pendingSpace = false

        for byte in folded.utf8 {
            let normalized: UInt8
            switch byte {
            case 0x61...0x7A, 0x30...0x39: normalized = byte          // a-z, 0-9
            case 0x41...0x5A: normalized = byte + 0x20                // A-Z
            case 0x80...: normalized = byte                           // хвосты UTF-8
            default: normalized = space                               // всё прочее — разделитель
            }
            if normalized == space {
                pendingSpace = !out.isEmpty
                continue
            }
            if pendingSpace {
                out.append(space)
                pendingSpace = false
            }
            out.append(normalized)
        }
        return out
    }

    // MARK: - Сопоставление

    /// Насколько хорошо слово запроса легло в строку.
    enum Match: Int, Sendable {
        case none = 0
        /// Встретилось где-то внутри слова: «mac» в «Big Mac Sauce».
        case inside = 1
        /// С начала слова: «mac» в «Big Mac».
        case wordStart = 2
        /// С начала всей строки: «big» в «Big Mac».
        case leading = 3
    }

    static func match(_ token: [UInt8], in text: ArraySlice<UInt8>) -> Match {
        guard !token.isEmpty, token.count <= text.count else { return .none }

        var best = Match.none
        let start = text.startIndex
        let last = text.endIndex - token.count

        var position = start
        while position <= last {
            if text[position] == token[0], matches(token, in: text, at: position) {
                if position == start { return .leading }   // лучше уже не будет
                if text[position - 1] == space {
                    best = .wordStart
                } else if best == .none {
                    best = .inside
                }
            }
            position += 1
        }
        return best
    }

    private static func matches(
        _ token: [UInt8], in text: ArraySlice<UInt8>, at position: Int
    ) -> Bool {
        for offset in 1..<token.count where text[position + offset] != token[offset] {
            return false
        }
        return true
    }
}
