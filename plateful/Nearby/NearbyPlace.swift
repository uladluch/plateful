import Foundation

// Проект собран с SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor; всё здесь —
// значения, которые считаются вне главного потока и проверяются без карты.

/// Заведение, которое вернула карта.
///
/// Своё значение, а не `MKMapItem`: сопоставление с каталогом — правило,
/// а не работа с картой, и проверять его походом в MapKit значит зависеть
/// от того, что сегодня отдаёт Apple рядом с машиной, на которой идут тесты.
nonisolated struct NearbyPlace: Hashable, Sendable {
    let name: String
    /// Метры от человека до заведения.
    let distance: Double
    /// Адрес одной строкой, как его даёт карта. Часов работы карта не
    /// отдаёт вовсе — ни одно свойство `MKMapItem` их не несёт.
    let address: String?
    let latitude: Double
    let longitude: Double
}

/// Сеть из каталога, найденная поблизости.
nonisolated struct NearbyChain: Identifiable, Hashable, Sendable {
    /// Имя ровно как в каталоге: по нему открывается меню.
    let chain: String
    /// Ближайшее заведение этой сети.
    let nearest: NearbyPlace
    /// Сколько заведений сети попало в радиус.
    let venues: Int

    var id: String { chain }
}

/// Сопоставление того, что показала карта, с тем, что есть в каталоге.
///
/// Карта пишет «Chick-fil-A», каталог — «Chick-Fil-A»; карта пишет
/// «Starbucks Coffee» там, где у нас просто «Starbucks». Поэтому имена
/// сравниваются нормализованными, и тем же нормализатором, что и поиск:
/// иначе «McDonald's» разошёлся бы сам с собой в двух местах приложения.
nonisolated enum NearbyMatch {

    /// Сети каталога, найденные среди заведений вокруг, ближайшие первыми.
    ///
    /// Совпадением считается либо точное имя, либо имя сети в начале
    /// названия заведения на границе слова: «Sonic Drive-In» — это Sonic,
    /// а «Sonicare» — нет. Из нескольких подходящих сетей берётся самая
    /// длинная: «Panda Express» точнее, чем «Panda».
    static func chains(near places: [NearbyPlace], in catalog: [String]) -> [NearbyChain] {
        // Длинные вперёд: первое же совпадение окажется самым точным.
        let known = catalog
            .map { (name: $0, key: TextIndex.normalized($0)) }
            .filter { !$0.key.isEmpty }
            .sorted { $0.key.count > $1.key.count }

        var nearest: [String: NearbyPlace] = [:]
        var counts: [String: Int] = [:]

        for place in places {
            let key = TextIndex.normalized(place.name)
            guard let chain = known.first(where: { starts(key, with: $0.key) }) else {
                continue
            }
            counts[chain.name, default: 0] += 1
            if let known = nearest[chain.name], known.distance <= place.distance {
                continue
            }
            nearest[chain.name] = place
        }

        return nearest
            .map { NearbyChain(chain: $0.key, nearest: $0.value,
                               venues: counts[$0.key] ?? 1) }
            .sorted { ($0.nearest.distance, $0.chain) < ($1.nearest.distance, $1.chain) }
    }

    /// Имя заведения начинается с имени сети — целиком или до пробела.
    ///
    /// Граница слова обязательна. Без неё «Sonic» поймал бы «Sonicare», а
    /// «Wawa» — «Wawadyne»: имена сетей коротки, и подстрока ловит чужое.
    private static func starts(_ name: [UInt8], with chain: [UInt8]) -> Bool {
        guard name.count >= chain.count, name.prefix(chain.count).elementsEqual(chain)
        else { return false }
        return name.count == chain.count || name[chain.count] == UInt8(ascii: " ")
    }
}
