import Foundation

// Значения: считаются вне главного потока и проверяются без сети и без карты.

/// Заведение сети — то, что приходит из `venues_near`.
///
/// Своих ресторанов приложение не выдумывает: строка приходит из базы, куда
/// её положил импортёр, забравший её у самой сети. Поэтому здесь нет ни
/// «примерно», ни «похоже»: адрес и часы — то, что сеть опубликовала о себе.
nonisolated struct Venue: Identifiable, Hashable, Sendable {
    /// Имя сети ровно как в каталоге: по нему открывается меню.
    let chain: String
    /// Номер магазина у сети.
    let extKey: String
    let latitude: Double
    let longitude: Double
    let address: String
    let phone: String?
    let hours: WeekHours?
    /// Драйв-тру работает дольше зала, и для человека без машины это другой
    /// ответ — поэтому вторыми часами, а не вместо первых.
    let driveThruHours: WeekHours?
    let amenities: [String]
    /// Метры от человека до заведения — их считает база, а не клиент.
    let distance: Double

    var id: String { "\(chain)#\(extKey)" }
}

/// Часы работы на неделю.
///
/// Время местное — то самое, в котором стоит ресторан. Часового пояса в
/// данных нет, но экран показывает заведения в нескольких километрах от
/// человека, а на таком расстоянии пояс у него и у ресторана один.
nonisolated struct WeekHours: Hashable, Sendable {

    /// Один день. Минуты от полуночи, а не строки: сравнивать время
    /// строками — значит однажды сравнить «9:00» с «10:00» и получить,
    /// что девять больше.
    struct Day: Hashable, Sendable {
        let opens: Int
        let closes: Int
        /// Круглые сутки — так сказала сама сеть, а не мы вывели из 00:00–23:59.
        let allDay: Bool

        /// Закрытие раньше открытия значит «за полночь»: Popeyes на Бродвее
        /// работает с 10:00 до 06:00 следующего дня.
        var pastMidnight: Bool { closes <= opens && !allDay }
    }

    /// Ключи те же, что в базе: `mon`… `sun`. Дня нет — в этот день закрыто.
    let days: [String: Day]

    /// Порядок дней от воскресенья: `Calendar.weekday` считает так же,
    /// и это избавляет от переводной таблицы в двух местах.
    static let order = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]

    /// Открыто ли сейчас — и до какого времени.
    enum Status: Equatable, Sendable {
        /// Минуты от полуночи; `nil` — круглые сутки.
        case open(until: Int?)
        /// Минуты от полуночи ближайшего открытия; `nil` — не знаем.
        case closed(until: Int?)
        /// Часов у нас нет. Не то же самое, что «закрыто».
        case unknown
    }

    func status(at date: Date, calendar: Calendar = .current) -> Status {
        guard !days.isEmpty else { return .unknown }

        let parts = calendar.dateComponents([.weekday, .hour, .minute], from: date)
        guard let weekday = parts.weekday, let hour = parts.hour,
              let minute = parts.minute else { return .unknown }

        let today = (weekday - 1) % 7           // Calendar считает с единицы
        let now = hour * 60 + minute

        // Вчерашний вечер, затянувшийся за полночь: в 02:00 ресторан открыт
        // не по сегодняшней записи, а по вчерашней.
        let yesterday = (today + 6) % 7
        if let last = day(yesterday), last.pastMidnight, now < last.closes {
            return .open(until: last.closes)
        }

        if let entry = day(today) {
            if entry.allDay { return .open(until: nil) }
            if entry.pastMidnight {
                if now >= entry.opens { return .open(until: entry.closes) }
            } else if now >= entry.opens && now < entry.closes {
                return .open(until: entry.closes)
            }
            if now < entry.opens { return .closed(until: entry.opens) }
        }

        // Закрыто. Ближайшее открытие — в один из следующих шести дней.
        for ahead in 1...6 {
            if let next = day((today + ahead) % 7) {
                return .closed(until: next.opens)
            }
        }
        return .closed(until: nil)
    }

    /// День по номеру от воскресенья.
    func day(_ index: Int) -> Day? {
        days[Self.order[index % 7]]
    }
}

extension Venue: Decodable {

    enum CodingKeys: String, CodingKey {
        case chain, latitude, longitude, address, phone, hours, amenities
        case extKey = "ext_key"
        case driveThruHours = "drive_thru_hours"
        case distance = "distance_m"
    }

    init(from decoder: any Decoder) throws {
        let box = try decoder.container(keyedBy: CodingKeys.self)
        chain = try box.decode(String.self, forKey: .chain)
        extKey = try box.decode(String.self, forKey: .extKey)
        latitude = try box.decode(Double.self, forKey: .latitude)
        longitude = try box.decode(Double.self, forKey: .longitude)
        address = try box.decode(String.self, forKey: .address)
        phone = try box.decodeIfPresent(String.self, forKey: .phone)
        hours = try box.decodeIfPresent(WeekHours.self, forKey: .hours)
        driveThruHours = try box.decodeIfPresent(WeekHours.self, forKey: .driveThruHours)
        amenities = try box.decodeIfPresent([String].self, forKey: .amenities) ?? []
        distance = try box.decode(Double.self, forKey: .distance)
    }
}

extension WeekHours: Decodable {

    /// `{"mon": {"open": "06:00", "close": "01:00", "h24": true}}`.
    ///
    /// День, время которого не разбирается, выбрасывается целиком: показать
    /// «открыто до :00» хуже, чем не показать ничего.
    init(from decoder: any Decoder) throws {
        struct Raw: Decodable {
            let open: String
            let close: String
            let h24: Bool?
        }
        let raw = try decoder.singleValueContainer().decode([String: Raw].self)
        days = raw.reduce(into: [:]) { result, pair in
            guard Self.order.contains(pair.key),
                  let opens = Self.minutes(pair.value.open),
                  let closes = Self.minutes(pair.value.close) else { return }
            result[pair.key] = Day(opens: opens, closes: closes,
                                   allDay: pair.value.h24 == true)
        }
    }

    /// `06:30` → 390. Всё, что не похоже на время суток, — не время.
    static func minutes(_ clock: String) -> Int? {
        let parts = clock.split(separator: ":", omittingEmptySubsequences: false)
        guard parts.count == 2,
              let hour = Int(parts[0]), let minute = Int(parts[1]),
              (0...23).contains(hour), (0...59).contains(minute) else { return nil }
        return hour * 60 + minute
    }
}
