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
    /// Адрес одной строкой, как его даёт карта. Часов работы и ценника карта
    /// не отдаёт вовсе — среди свойств `MKMapItem` их нет (iOS 26 SDK), их
    /// показывает только карточка места, которую рисует сама Apple.
    let address: String?
    let latitude: Double
    let longitude: Double
}

/// Сеть из каталога, найденная поблизости.
nonisolated struct NearbyChain: Identifiable, Hashable, Sendable {
    /// Имя ровно как в каталоге: по нему открывается меню.
    let chain: String
    /// Ближайшее заведение этой сети.
    let nearest: Venue
    /// Сколько заведений сети попало в радиус.
    let venues: Int

    var id: String { chain }
}

/// Каталог сетей, подготовленный к сопоставлению с картой.
///
/// Карта пишет «Chick-fil-A», каталог — «Chick-Fil-A»; карта пишет
/// «Starbucks Coffee» там, где у нас просто «Starbucks». Поэтому имена
/// сравниваются нормализованными, и тем же нормализатором, что и поиск:
/// иначе «McDonald's» разошёлся бы сам с собой в двух местах приложения.
///
/// Отдельный тип, а не функция: подготовка каталога стоит девяноста шести
/// нормализаций, а спрашивают его по разу на каждое заведение вокруг.
nonisolated struct NearbyCatalog: Sendable {

    private struct Known: Sendable {
        let name: String
        let key: [UInt8]
    }

    private let known: [Known]

    init(_ chains: [String]) {
        // Длинные вперёд: первое же совпадение окажется самым точным —
        // «Panda Express» точнее, чем «Panda».
        known = chains
            .map { Known(name: $0, key: TextIndex.normalized($0)) }
            .filter { !$0.key.isEmpty }
            .sorted { $0.key.count > $1.key.count }
    }

    /// Сеть каталога, которой принадлежит заведение, — или `nil`, если это
    /// не наша сеть.
    ///
    /// Совпадением считается либо точное имя, либо имя сети в начале
    /// названия заведения на границе слова: «Sonic Drive-In» — это Sonic,
    /// а «Sonicare» — нет.
    func chain(of placeName: String) -> String? {
        let key = TextIndex.normalized(placeName)
        return known.first { Self.starts(key, with: $0.key) }?.name
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

/// Сопоставление того, что показала карта, с тем, что есть в каталоге.
///
/// Нужно только запасному пути. Когда отвечает наша база, сети приходят
/// готовыми — угадывать по имени нечего.
nonisolated enum NearbyMatch {

    /// Сети из списка заведений, ближайшие первыми.
    ///
    /// Одна группировка на оба пути — и на точки из базы, и на то, что нашла
    /// карта: иначе список сетей вёл бы себя по-разному в зависимости от
    /// того, отвечал ли сервер, а человеку это различие не видно.
    static func chains(from venues: [Venue]) -> [NearbyChain] {
        var nearest: [String: Venue] = [:]
        var counts: [String: Int] = [:]

        for venue in venues {
            counts[venue.chain, default: 0] += 1
            if let known = nearest[venue.chain], known.distance <= venue.distance {
                continue
            }
            nearest[venue.chain] = venue
        }

        return nearest
            .map { NearbyChain(chain: $0.key, nearest: $0.value,
                               venues: counts[$0.key] ?? 1) }
            .sorted { ($0.nearest.distance, $0.chain) < ($1.nearest.distance, $1.chain) }
    }

    /// Заведения, которые карта нашла вокруг, — те из них, что наши.
    static func venues(among places: [NearbyPlace],
                       in catalog: NearbyCatalog) -> [Venue] {
        places.compactMap { place in
            guard let chain = catalog.chain(of: place.name) else { return nil }
            return Venue(chain: chain,
                         // У карты номера магазина нет; координата различает
                         // две точки одной сети не хуже.
                         extKey: "map:\(place.latitude),\(place.longitude)",
                         latitude: place.latitude,
                         longitude: place.longitude,
                         address: place.address ?? "",
                         phone: nil,
                         // Часов карта не отдаёт вовсе — и делать вид, что
                         // отдаёт, нельзя.
                         hours: nil,
                         driveThruHours: nil,
                         amenities: [],
                         distance: place.distance)
        }
    }

    static func chains(near places: [NearbyPlace], in catalog: [String]) -> [NearbyChain] {
        chains(near: places, in: NearbyCatalog(catalog))
    }

    static func chains(near places: [NearbyPlace],
                       in catalog: NearbyCatalog) -> [NearbyChain] {
        chains(from: venues(among: places, in: catalog))
    }
}
