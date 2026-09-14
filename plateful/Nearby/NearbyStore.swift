import CoreLocation
import MapKit
import Observation
import OSLog

/// Что рядом: геопозиция у системы, заведения у карты, меню из пака.
///
/// Карту спрашиваем **по имени каждой сети из пака**, а не «что вокруг»:
/// первый вариант экрана брал все заведения в радиусе и опознавал их по
/// имени — на Таймс-сквер из 48 опознались два. Запрос «Burger King»
/// возвращает Burger King, и так для каждой сети, чьё меню приложение
/// умеет открыть. Своей базы точек нет и не будет: у Apple есть все 96
/// сетей уже сегодня, а своя база — это по импортёру на сеть с тех же
/// сайтов, что режут скрейперы.
///
/// Разрешение спрашиваем в момент, когда человек сам открыл экран, — не на
/// старте. Приложение обещает работать без онбординга, и диалог о геопозиции
/// при первом запуске это обещание нарушал бы.
///
/// **Карта ограничивает частоту.** С каталогом в 90 сетей один залп
/// получил отказ `loadingThrottled` у 48 сетей — на Таймс-сквер показывались
/// 30 сетей из 90, и каждый раз другие. Отсюда два правила: хранилище одно
/// на приложение (главный экран и вкладка «рядом» раньше слали по своему
/// залпу), и отказанные сети спрашиваются снова, с паузой, пока не ответят.
@MainActor
@Observable
final class NearbyStore: NSObject {

    enum State: Equatable {
        case idle
        case locating
        case searching
        case ready([NearbyChain])
        /// Человек отказал или система запретила. Не ошибка — выбор.
        case denied
        case failed(String)
    }

    private(set) var state: State = .idle
    private(set) var venues: [Venue] = []

    /// Решение человека о геопозиции. Экраны читают его отсюда, а не заводят
    /// `CLLocationManager` в `body`: тот и стоил на каждый рендер, и смену
    /// разрешения экран не видел.
    private(set) var authorization: CLAuthorizationStatus = .notDetermined

    /// Залп ещё идёт — в том числе после первой пачки, когда состояние уже
    /// `ready`, а до многих сетей очередь не дошла.
    private(set) var isSearching = false

    /// Сети, на которые карта в этом залпе уже ответила — заведениями или
    /// «рядом нет». По нему экран одной сети отличает «ещё не спросили» от
    /// «спросили, пусто».
    private(set) var answered: Set<String> = []

    /// Радиус поиска.
    static let radius: CLLocationDistance = 5_000

    /// Сколько сетей спрашивается у карты разом. Она ограничивает частоту
    /// запросов (`MKError.loadingThrottled`), и девяносто шесть параллельных
    /// вопросов получили бы отказ вместо ответа.
    static let width = 4

    /// Сколько раз спрашивать сети, которым карта отказала по частоте.
    /// Замер на 90 сетях: первый проход — отказ у 48, после паузы ≥ минуты
    /// ответили все. Хватает одного повтора; остальные два — запас на случай,
    /// если карта в этот раз строже.
    static let passes = 4

    /// Сколько ответ считается свежим для второго экрана. За пять минут
    /// человек не уходит из радиуса в пять километров, а второй залп в
    /// девяносто запросов карта почти целиком отклонила бы.
    static let freshFor: TimeInterval = 5 * 60

    /// Пауза перед повтором. Окно ограничения карта не публикует, замерено:
    /// повтор через 30 секунд получил отказ у тех же 48 сетей, через 90 от
    /// первого прохода ответили все. Поэтому сразу минута — полминуты это
    /// проход, потраченный на тот же отказ.
    static func delay(beforePass pass: Int) -> TimeInterval {
        pass < 1 ? 0 : 60
    }

    /// Можно ли отдать уже идущий или свежий ответ вместо нового поиска.
    ///
    /// Отказ в геопозиции и сбой — не ответ: человек мог включить геопозицию
    /// в настройках, а сеть — вернуться, и спросить надо заново.
    static func reuses(_ state: State, sameCatalog: Bool,
                       startedAt: Date?, now: Date) -> Bool {
        guard sameCatalog else { return false }
        switch state {
        case .locating, .searching:
            return true
        case .ready:
            guard let startedAt else { return false }
            return now.timeIntervalSince(startedAt) < freshFor
        case .idle, .denied, .failed:
            return false
        }
    }

    private let manager = CLLocationManager()
    /// Когда начался последний поиск — по нему второй экран понимает, что
    /// ответ свежий.
    private var startedAt: Date?
    private let log = Logger(subsystem: "com.anluch.plateful", category: "nearby")
    private var catalog: [String] = []
    private var pending = false
    /// Сами объекты карты — для её карточки места и маршрута.
    private var items: [Venue.ID: MKMapItem] = [:]

    /// Ответ карты на одну сеть, каким его можно вынести из дочерней задачи.
    ///
    /// `MKMapItem` не `Sendable`, а результат задачи в группе обязан им быть.
    /// Сама карта отдаёт эти объекты на главном акторе (её обработчики
    /// помечены `NS_SWIFT_UI_ACTOR`), и читаем мы их тоже только там —
    /// поэтому обещание честное, а не для компилятора.
    nonisolated private struct Answer: @unchecked Sendable {

        /// Что ответила карта. Три отказа — три разные вещи, и сваливать их в
        /// одно «не ответила» нельзя: `MKLocalSearch` на «такой сети рядом
        /// нет» не возвращает пустой список, а бросает `placemarkNotFound`.
        /// С каталогом в 90 сетей это обычный ответ для большинства из них, и
        /// пока он считался отказом, в лог писалось «не ответили 40», а экран
        /// без единой нашей сети вокруг говорил бы «карта не отвечает».
        nonisolated enum Outcome {
            case found([MKMapItem])
            /// Ответила: этой сети в радиусе нет.
            case none
            /// Попросила спрашивать реже.
            case throttled
            case failed
        }

        let chain: String
        let outcome: Outcome
    }

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
        authorization = manager.authorizationStatus
    }

    /// Спрашивает, что рядом. Каталог передаётся снаружи: хранилище знает
    /// про карту, но не про меню.
    func find(chains: [String]) {
        if Self.reuses(state, sameCatalog: chains == catalog,
                       startedAt: startedAt, now: .now) {
            log.info("Рядом: ответ уже есть или в пути — второй залп не шлю")
            return
        }
        catalog = chains
        pending = true
        venues = []
        items = [:]
        answered = []

        switch manager.authorizationStatus {
        case .notDetermined:
            state = .locating
            manager.requestWhenInUseAuthorization()
        case .denied, .restricted:
            state = .denied
        default:
            state = .locating
            manager.requestLocation()
        }
    }

    /// Объект карты для заведения — карточке Apple нужен именно он.
    func mapItem(for venue: Venue) -> MKMapItem? {
        items[venue.id]
    }

    /// Заведения одной сети без геопозиции человека.
    ///
    /// Спросить «рядом» нечем, но саму сеть карта может найти и без региона
    /// человека. Расстояние в таком ответе не значит ничего, поэтому
    /// сортируем по алфавиту адреса, а не по метрам.
    func venuesWithoutLocation(for chain: String) async -> [Venue] {
        // Центр континентальных США — не «рядом с кем-то», а просто точка,
        // без которой `MKLocalSearch` не примет регион.
        let region = MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: 39.8283, longitude: -98.5795),
            latitudinalMeters: 4_000_000, longitudinalMeters: 4_000_000)
        guard case .found(let found) = await Self.ask(chain, in: region).outcome else {
            return []
        }

        let index = NearbyCatalog([chain])
        var result: [Venue] = []
        for item in found {
            guard let name = item.name, index.chain(of: name) != nil else { continue }
            let coordinate = item.placemark.coordinate
            let venue = Venue(
                chain: chain, extKey: Self.key(of: item),
                latitude: coordinate.latitude, longitude: coordinate.longitude,
                address: item.placemark.title ?? "",
                phone: item.phoneNumber,
                distance: 0)
            // Карточке заведения нужен объект карты — у этих тоже.
            items[venue.id] = item
            result.append(venue)
        }
        return result.sorted { $0.address < $1.address }
    }

    private func search(around coordinate: CLLocationCoordinate2D) async {
        state = .searching
        isSearching = true
        defer { isSearching = false }
        startedAt = .now
        let origin = CLLocation(latitude: coordinate.latitude,
                                longitude: coordinate.longitude)
        let region = MKCoordinateRegion(center: coordinate,
                                        latitudinalMeters: Self.radius * 2,
                                        longitudinalMeters: Self.radius * 2)
        let index = NearbyCatalog(catalog)

        var found: [Venue] = []
        var none = 0
        /// Ответила, но чужими заведениями: на «Firehouse Subs» в месте без
        /// Firehouse карта отдаёт соседние сэндвичные. Без этого счётчика
        /// сети в логе не сходились с каталогом — 70 найдено, «рядом нет 0»,
        /// а ещё двадцать будто пропали.
        var unmatched = 0
        var failed = 0
        var remaining = catalog

        for pass in 0..<Self.passes {
            if pass > 0 {
                guard !remaining.isEmpty else { break }
                let delay = Self.delay(beforePass: pass)
                log.info("Отказ по частоте у \(remaining.count) сетей — повтор через \(Int(delay)) с")
                try? await Task.sleep(for: .seconds(delay))
            }

            var throttled: [String] = []
            // По `width` сетей за раз: результаты публикуются после каждой
            // пачки, и экран заполняется, не дожидаясь последней сети.
            var queue = remaining[...]
            while !queue.isEmpty {
                let batch = Array(queue.prefix(Self.width))
                queue = queue.dropFirst(Self.width)
                await withTaskGroup(of: Answer.self) { group in
                    for chain in batch {
                        group.addTask { await Self.ask(chain, in: region) }
                    }
                    for await answer in group {
                        let chain = answer.chain
                        let result: [MKMapItem]
                        switch answer.outcome {
                        case .found(let items): result = items; answered.insert(chain)
                        case .none: none += 1; answered.insert(chain); continue
                        case .throttled: throttled.append(chain); continue
                        case .failed: failed += 1; answered.insert(chain); continue
                        }
                        for item in result {
                            guard let place = Self.place(from: item, origin: origin),
                                  let matched = index.chain(of: place.name),
                                  matched == chain else { continue }
                            let venue = Venue(chain: matched, extKey: Self.key(of: item),
                                              latitude: place.latitude,
                                              longitude: place.longitude,
                                              address: place.address ?? "",
                                              phone: item.phoneNumber,
                                              distance: place.distance)
                            guard items[venue.id] == nil else { continue }
                            items[venue.id] = item
                            found.append(venue)
                        }
                        if !found.contains(where: { $0.chain == chain }) { unmatched += 1 }
                    }
                }
                venues = found.sorted { $0.distance < $1.distance }
                state = .ready(NearbyMatch.chains(from: venues))
            }

            log.info("Рядом, проход \(pass + 1): \(found.count) точек у \(Set(found.map(\.chain)).count) сетей из \(self.catalog.count); рядом нет \(none), ответила чужими \(unmatched), отказ по частоте \(throttled.count), сбой \(failed)")
            remaining = throttled
        }

        // «Карта не отвечает» — только если не ответила ни на один вопрос.
        // Если на все ответила «рядом нет», это пустой список, а не сбой.
        let answered = catalog.count - remaining.count - failed
        if found.isEmpty, answered == 0, !catalog.isEmpty {
            state = .failed("The map didn't answer. Try again in a moment.")
        }
    }

    /// Одна сеть у карты. Ответ уезжает из дочерней задачи в конверте —
    /// граница акторов пропускает только его.
    private static func ask(_ chain: String,
                            in region: MKCoordinateRegion) async -> Answer {
        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = chain
        request.region = region
        request.resultTypes = .pointOfInterest
        // Фастфуда отдельной категорией у карты нет — он лежит в
        // «ресторанах». Кофейни и пекарни нужны отдельно: Starbucks и
        // Dunkin' приходят как кафе, Krispy Kreme как пекарня.
        request.pointOfInterestFilter = MKPointOfInterestFilter(
            including: [.restaurant, .cafe, .bakery])
        do {
            return Answer(chain: chain,
                          outcome: .found(try await MKLocalSearch(request: request).start().mapItems))
        } catch {
            switch (error as? MKError)?.code {
            case .placemarkNotFound: return Answer(chain: chain, outcome: .none)
            case .loadingThrottled: return Answer(chain: chain, outcome: .throttled)
            default: return Answer(chain: chain, outcome: .failed)
            }
        }
    }

    /// Устойчивый ключ места. У Apple он есть с iOS 18; без него —
    /// координата, и этого хватает, чтобы две точки не слиплись.
    private static func key(of item: MKMapItem) -> String {
        if let id = item.identifier?.rawValue { return id }
        let c = item.placemark.coordinate
        return "map:\(c.latitude),\(c.longitude)"
    }

    /// `MKMapItem` → наше значение: имя, расстояние, координата и адрес.
    private static func place(from item: MKMapItem,
                              origin: CLLocation) -> NearbyPlace? {
        guard let name = item.name else { return nil }
        let coordinate = item.placemark.coordinate
        let distance = origin.distance(
            from: CLLocation(latitude: coordinate.latitude,
                             longitude: coordinate.longitude))
        return NearbyPlace(
            name: name,
            distance: distance,
            address: item.placemark.title,
            latitude: coordinate.latitude,
            longitude: coordinate.longitude)
    }
}

extension NearbyStore: CLLocationManagerDelegate {

    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        // Сам `manager` через границу актора не передаём — он не Sendable,
        // а свой у нас и так есть. Через границу едет только статус.
        let status = manager.authorizationStatus
        Task { @MainActor in
            authorization = status
            switch status {
            case .authorizedWhenInUse, .authorizedAlways:
                if pending { self.manager.requestLocation() }
            case .denied, .restricted:
                state = .denied
            default:
                break
            }
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager,
                                     didUpdateLocations locations: [CLLocation]) {
        guard let coordinate = locations.last?.coordinate else { return }
        Task { @MainActor in
            guard pending else { return }
            pending = false
            await search(around: coordinate)
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager,
                                     didFailWithError error: Error) {
        let message = error.localizedDescription
        Task { @MainActor in
            pending = false
            // Отказ приходит сюда же кодом denied — но это выбор, а не сбой.
            state = (error as? CLError)?.code == .denied ? .denied : .failed(message)
        }
    }
}
