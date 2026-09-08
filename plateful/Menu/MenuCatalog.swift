import Foundation

/// Каталог целиком в памяти: 25 тысяч позиций, поиск линейным проходом.
///
/// Почему не SQLite и не SwiftData: каталог read-only и приезжает готовым
/// файлом. Открытие базы и разбор запроса стоят дороже, чем сам проход по
/// такому объёму. SwiftData остаётся для того, что пишет пользователь.
///
/// Значимый тип и `Sendable` — каталог собирается вне главного потока и
/// переезжает на него целиком.
// Проект собирается с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor — это верно
// для SwiftUI, но не для слоя данных: каталог разбирается и строится вне
// главного потока. Отсюда `nonisolated` на типах ниже.
nonisolated struct MenuCatalog: Sendable {

    let version: Int
    let source: String
    let observed: String
    let chains: [MenuChain]
    let items: [MenuItem]

    private let index: TextIndex
    private let chainItems: [String: [Int32]]

    init(pack: MenuPack) {
        self.version = pack.version
        self.source = pack.source
        self.observed = pack.observed

        var items: [MenuItem] = []
        items.reserveCapacity(pack.items.count)
        var chainItems: [String: [Int32]] = [:]
        var names = TextIndex.Builder(capacity: pack.items.count)
        var chainNames = TextIndex.Builder(capacity: pack.items.count)

        for (offset, packItem) in pack.items.enumerated() {
            items.append(MenuItem(id: offset, packItem: packItem, defaults: pack))
            chainItems[packItem.chain, default: []].append(Int32(offset))
            names.append(packItem.name)
            chainNames.append(packItem.chain)
        }

        self.items = items
        self.chainItems = chainItems
        self.index = TextIndex(names: names.build(), chains: chainNames.build())

        // Порядок сетей из пака: он уже отсортирован по названию.
        self.chains = pack.chains.map { MenuChain(name: $0.name, itemCount: $0.itemCount) }
    }

    /// Позиции одной сети, в порядке пака (по названию).
    func items(in chain: String) -> [MenuItem] {
        (chainItems[chain] ?? []).map { items[Int($0)] }
    }

    /// Поиск по названию блюда и названию сети.
    ///
    /// Запрос режется на слова, и каждое обязано найтись — так работает
    /// «mcdonalds big mac». Совпадение в начале слова ценится выше, чем
    /// внутри; совпадение по сети — ниже, чем по названию блюда.
    func search(_ query: String, in chain: String? = nil, limit: Int = 50) -> [MenuItem] {
        let tokens = TextIndex.normalized(query)
            .split(separator: TextIndex.space)
            .map { Array($0) }
        guard !tokens.isEmpty else { return [] }

        let candidates: [Int32] = if let chain {
            chainItems[chain] ?? []
        } else {
            []  // пустой массив = идём по всем, см. ниже
        }

        var hits: [(score: Int32, length: Int32, item: Int32)] = []
        hits.reserveCapacity(min(limit * 8, 512))

        let scan: (Int32) -> Void = { position in
            let offset = Int(position)
            let name = self.index.name(offset)
            // Внутри сети её название искать бессмысленно: оно у всех одно.
            let chainName = chain == nil ? self.index.chain(offset) : nil

            var total: Int32 = 0
            for token in tokens {
                let inName = TextIndex.match(token, in: name)
                let inChain = chainName.map { TextIndex.match(token, in: $0) } ?? .none
                if inName == .none && inChain == .none { return }
                // Название блюда весит вдвое: «chicken» у Chick-fil-A не должен
                // выбрасывать наверх весь их ассортимент.
                total += Int32(inName.rawValue) * 2 + Int32(inChain.rawValue)
            }
            hits.append((total, Int32(name.count), position))
        }

        if chain == nil {
            for position in 0..<Int32(items.count) { scan(position) }
        } else {
            for position in candidates { scan(position) }
        }

        // Снятые с меню опускаем в конец при любой релевантности: заказать
        // их всё равно нельзя, но и прятать нечестно.
        hits.sort {
            let leftArchived = items[Int($0.item)].isOffMenu
            let rightArchived = items[Int($1.item)].isOffMenu
            if leftArchived != rightArchived { return !leftArchived }
            if $0.score != $1.score { return $0.score > $1.score }
            if $0.length != $1.length { return $0.length < $1.length }
            return $0.item < $1.item
        }
        return hits.prefix(limit).map { items[Int($0.item)] }
    }
}
