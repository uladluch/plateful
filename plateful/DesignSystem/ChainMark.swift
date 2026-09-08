import SwiftUI

// Проект собран с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor; вычисление
// инициалов и цвета — чистые функции.

/// Значок сети: инициалы на системном цвете.
///
/// Не логотип. Чужие логотипы — товарные знаки, и тащить их в приложение,
/// которое в описании прямо говорит «не аффилировано ни с одной сетью»,
/// значит противоречить самому себе. Инициалы решают ту же задачу — узнать
/// строку в списке за долю секунды — и ничего не изображают.
nonisolated enum ChainMark {

    /// Палитра только из системных цветов: тёмная тема и режимы контраста
    /// достаются бесплатно.
    static let palette: [Color] = [
        Color(.systemBlue), Color(.systemGreen), Color(.systemOrange),
        Color(.systemPurple), Color(.systemTeal), Color(.systemIndigo),
        Color(.systemPink), Color(.systemBrown), Color(.systemRed),
        Color(.systemMint), Color(.systemCyan),
    ]

    /// Инициалы: до двух букв.
    ///
    /// Делим только по пробелам и дефисам — апостроф не разделитель, иначе
    /// «McDonald's» превратится в «MS».
    static func initials(for chain: String) -> String {
        let words = chain
            .split(whereSeparator: { $0 == " " || $0 == "-" || $0 == "/" })
            .filter { $0.first?.isLetter == true || $0.first?.isNumber == true }
        let letters = words.prefix(2).compactMap(\.first)
        return String(letters).uppercased()
    }

    /// Цвет по имени сети.
    ///
    /// Хеш свой, а не `hashValue`: у Swift он засеивается заново при каждом
    /// запуске, и цвета скакали бы от старта к старту.
    static func color(for chain: String) -> Color {
        var hash: UInt64 = 5381
        for byte in chain.utf8 {
            hash = hash &* 33 &+ UInt64(byte)
        }
        return palette[Int(hash % UInt64(palette.count))]
    }
}

/// Кружок с инициалами сети.
struct ChainMarkView: View {

    let chain: String
    var size: CGFloat = 30

    var body: some View {
        Text(ChainMark.initials(for: chain))
            .font(.caption)
            .fontWeight(.semibold)
            .foregroundStyle(.white)
            .frame(width: size, height: size)
            .background(ChainMark.color(for: chain), in: .circle)
            .accessibilityHidden(true)
    }
}

#Preview {
    List(["McDonald's", "Chick-Fil-A", "Taco Bell", "7 Eleven", "Panera Bread"], id: \.self) { chain in
        Label {
            Text(chain)
        } icon: {
            ChainMarkView(chain: chain)
        }
    }
}
