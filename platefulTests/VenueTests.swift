import Foundation
import Testing
@testable import plateful

/// Часы работы заведения и разбор ответа базы.
///
/// Всё считается без сети: строки приходят из `venues_near`, а правила
/// «открыто ли сейчас» — наши, и ошибка в них отправляет человека к
/// закрытой двери.
@Suite("Заведения")
struct VenueTests {

    /// Календарь с постоянным поясом: иначе тест про «открыто в 23:00»
    /// проходил бы в Европе и падал в Калифорнии.
    static let calendar: Calendar = {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "UTC")!
        return calendar
    }()

    /// Сентябрь 2026: 7-е — понедельник, 6-е — воскресенье.
    static func moment(day: Int, hour: Int, minute: Int = 0) -> Date {
        calendar.date(from: DateComponents(year: 2026, month: 9, day: day,
                                           hour: hour, minute: minute))!
    }

    static func week(_ days: [String: WeekHours.Day]) -> WeekHours {
        WeekHours(days: days)
    }

    static func day(_ opens: Int, _ closes: Int, allDay: Bool = false) -> WeekHours.Day {
        WeekHours.Day(opens: opens, closes: closes, allDay: allDay)
    }

    // MARK: - Открыто ли сейчас

    @Test("в рабочие часы открыто и видно, до скольки")
    func openDuringHours() {
        let hours = Self.week(["mon": Self.day(6 * 60, 22 * 60)])

        let status = hours.status(at: Self.moment(day: 7, hour: 10),
                                  calendar: Self.calendar)

        #expect(status == .open(until: 22 * 60))
    }

    @Test("до открытия закрыто, и видно, когда откроется")
    func closedBeforeOpening() {
        let hours = Self.week(["mon": Self.day(6 * 60, 22 * 60)])

        let status = hours.status(at: Self.moment(day: 7, hour: 5),
                                  calendar: Self.calendar)

        #expect(status == .closed(until: 6 * 60))
    }

    /// Popeyes на Бродвее работает с 10:00 до 06:00 следующего дня.
    /// Закрытие раньше открытия — норма, а не ошибка данных.
    @Test("закрытие за полночь: вечером ещё открыто")
    func openLateAtNight() {
        let hours = Self.week(["mon": Self.day(10 * 60, 6 * 60)])

        let status = hours.status(at: Self.moment(day: 7, hour: 23),
                                  calendar: Self.calendar)

        #expect(status == .open(until: 6 * 60))
    }

    @Test("закрытие за полночь: ночью открыто по вчерашней записи")
    func openAfterMidnight() {
        // Вторник в два часа ночи — это ещё понедельничная смена.
        let hours = Self.week(["mon": Self.day(10 * 60, 6 * 60)])

        let status = hours.status(at: Self.moment(day: 8, hour: 2),
                                  calendar: Self.calendar)

        #expect(status == .open(until: 6 * 60))
    }

    @Test("после закрытия за полночь уже закрыто")
    func closedAfterLateClosing() {
        let hours = Self.week(["mon": Self.day(10 * 60, 6 * 60),
                               "tue": Self.day(10 * 60, 6 * 60)])

        let status = hours.status(at: Self.moment(day: 8, hour: 7),
                                  calendar: Self.calendar)

        #expect(status == .closed(until: 10 * 60))
    }

    @Test("круглые сутки")
    func roundTheClock() {
        let hours = Self.week(["mon": Self.day(0, 23 * 60 + 59, allDay: true)])

        let status = hours.status(at: Self.moment(day: 7, hour: 3),
                                  calendar: Self.calendar)

        #expect(status == .open(until: nil))
    }

    /// У ресторана на военной базе воскресенья в данных нет вовсе.
    @Test("день без записи — закрыто, и ждём следующего открытия")
    func missingDayIsClosed() {
        let hours = Self.week(["mon": Self.day(6 * 60, 22 * 60)])

        let status = hours.status(at: Self.moment(day: 6, hour: 12),
                                  calendar: Self.calendar)

        #expect(status == .closed(until: 6 * 60))
    }

    /// «Не знаем» и «закрыто» — разные вещи: первое не должно уводить
    /// человека от открытой двери.
    @Test("без часов состояние неизвестно, а не «закрыто»")
    func noHoursIsUnknown() {
        let status = Self.week([:]).status(at: Self.moment(day: 7, hour: 12),
                                           calendar: Self.calendar)

        #expect(status == .unknown)
        #expect(NearbyView.statusText(.unknown) == nil)
    }

    // MARK: - Ответ базы

    static let json = """
    [{"chain": "Popeyes", "ext_key": "12345",
      "latitude": 40.7581, "longitude": -73.9855,
      "address": "1530 Broadway, New York, NY", "phone": "(212) 555-0100",
      "hours": {"mon": {"open": "10:00", "close": "06:00"},
                "thu": {"open": "00:00", "close": "23:59", "h24": true}},
      "drive_thru_hours": null,
      "amenities": ["delivery", "wifi"], "distance_m": 68.7}]
    """

    @Test("строка из venues_near разбирается целиком")
    func decodesResponse() throws {
        let venues = try JSONDecoder().decode([Venue].self,
                                              from: Data(Self.json.utf8))
        let venue = try #require(venues.first)

        #expect(venue.chain == "Popeyes")
        #expect(venue.extKey == "12345")
        #expect(venue.id == "Popeyes#12345")
        #expect(venue.distance == 68.7)
        #expect(venue.amenities == ["delivery", "wifi"])
        #expect(venue.driveThruHours == nil)
        #expect(venue.hours?.days["mon"] == Self.day(600, 360))
        #expect(venue.hours?.days["thu"]?.allDay == true)
    }

    @Test("непонятное время выбрасывается вместе с днём")
    func dropsBrokenClock() throws {
        let json = """
        [{"chain": "X", "ext_key": "1", "latitude": 1, "longitude": 2,
          "address": "", "hours": {"mon": {"open": "25:00", "close": "10:00"},
                                   "tue": {"open": "08:00", "close": "20:00"}},
          "amenities": [], "distance_m": 5}]
        """
        let venues = try JSONDecoder().decode([Venue].self, from: Data(json.utf8))

        #expect(venues.first?.hours?.days.keys.sorted() == ["tue"])
    }

    // MARK: - Группировка по сетям

    static func venue(_ chain: String, _ metres: Double, key: String = "1") -> Venue {
        Venue(chain: chain, extKey: key, latitude: 40.7, longitude: -74.0,
              address: "\(key) Main St", phone: nil, hours: nil,
              driveThruHours: nil, amenities: [], distance: metres)
    }

    @Test("сети идут ближайшими вперёд, с числом точек")
    func groupsByChain() {
        let chains = NearbyMatch.chains(from: [
            Self.venue("Popeyes", 800, key: "a"),
            Self.venue("Burger King", 120, key: "b"),
            Self.venue("Popeyes", 300, key: "c"),
        ])

        #expect(chains.map(\.chain) == ["Burger King", "Popeyes"])
        #expect(chains.last?.venues == 2)
        #expect(chains.last?.nearest.extKey == "c")
    }

    // MARK: - Полоса цены

    @Test("полоса рисуется долларами по числу")
    func priceBand() {
        #expect(MenuChain(name: "X", itemCount: 1, priceTier: 1).priceBand == "$")
        #expect(MenuChain(name: "X", itemCount: 1, priceTier: 4).priceBand == "$$$$")
    }

    /// «Не проставили» и «бесплатно» — разные вещи, и пустая строка вместо
    /// полосы честнее любой цифры.
    @Test("без полосы ничего не показываем")
    func missingPriceBand() {
        #expect(MenuChain(name: "X", itemCount: 1).priceBand == nil)
        #expect(MenuChain(name: "X", itemCount: 1, priceTier: 0).priceBand == nil)
        #expect(MenuChain(name: "X", itemCount: 1, priceTier: 9).priceBand == nil)
    }

    @Test("пак без полосы читается по-прежнему")
    func packWithoutPriceTier() throws {
        let json = #"{"name": "Popeyes", "itemCount": 169}"#
        let chain = try JSONDecoder().decode(MenuPack.Chain.self,
                                             from: Data(json.utf8))

        #expect(chain.priceTier == nil)
        #expect(chain.itemCount == 169)
    }

    @Test("неделя в карточке начинается с сегодняшнего дня")
    func weekStartsToday() {
        let week = VenueDetailView.weekFromToday(now: Self.moment(day: 10, hour: 12),
                                                 calendar: Self.calendar)

        // Четверг — четвёртый день недели, считая с воскресенья.
        #expect(week.first == 4)
        #expect(week.count == 7)
        #expect(Set(week).count == 7)
    }
}
