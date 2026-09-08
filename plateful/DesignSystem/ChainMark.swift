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

    /// Слаг сети — тот же, что в конвейере и в базе.
    ///
    /// Считается здесь же, чтобы имя ассета с логотипом и ключ сети в базе
    /// никогда не разошлись.
    static func slug(for chain: String) -> String {
        var slug = ""
        var pendingSeparator = false
        for character in chain.lowercased() {
            if character.isLetter || character.isNumber {
                if pendingSeparator, !slug.isEmpty { slug.append("-") }
                pendingSeparator = false
                slug.append(character)
            } else {
                pendingSeparator = true
            }
        }
        return slug
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

/// Значок сети: логотип, если он у нас есть, иначе инициалы.
///
/// Логотип берётся из каталога ассетов по слагу сети. Там, где его найти не
/// удалось, остаются инициалы — пустого места в списке не бывает.
struct ChainMarkView: View {

    let chain: String
    var size: CGFloat = 30

    /// Префикс имён в каталоге ассетов: `logo-mcdonald-s`, `logo-subway`…
    static let logoPrefix = "logo-"

    private var logoName: String? {
        let name = Self.logoPrefix + ChainMark.slug(for: chain)
        return UIImage(named: name) == nil ? nil : name
    }

    var body: some View {
        Group {
            if let logoName {
                Image(logoName)
                    .resizable()
                    .scaledToFit()
                    .padding(size * 0.1)
                    .frame(width: size, height: size)
                    .background(Color(.secondarySystemFill), in: .circle)
            } else {
                Text(ChainMark.initials(for: chain))
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundStyle(.white)
                    .frame(width: size, height: size)
                    .background(ChainMark.color(for: chain), in: .circle)
            }
        }
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
