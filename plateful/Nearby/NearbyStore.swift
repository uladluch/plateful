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

    /// Радиус поиска.
    static let radius: CLLocationDistance = 5_000

    /// Сколько сетей спрашивается у карты разом. Она ограничивает частоту
    /// запросов (`MKError.loadingThrottled`), и девяносто шесть параллельных
    /// вопросов получили бы отказ вместо ответа.
    static let width = 4

    private let manager = CLLocationManager()
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
        let chain: String
        /// `nil` — карта не ответила; пустой список — ответила, что нет.
        let items: [MKMapItem]?
    }

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
    }

    /// Спрашивает, что рядом. Каталог передаётся снаружи: хранилище знает
    /// про карту, но не про меню.
    func find(chains: [String]) {
        catalog = chains
        pending = true
        venues = []
        items = [:]

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

    private func search(around coordinate: CLLocationCoordinate2D) async {
        state = .searching
        let origin = CLLocation(latitude: coordinate.latitude,
                                longitude: coordinate.longitude)
        let region = MKCoordinateRegion(center: coordinate,
                                        latitudinalMeters: Self.radius * 2,
                                        longitudinalMeters: Self.radius * 2)
        let index = NearbyCatalog(catalog)

        var found: [Venue] = []
        var failed = 0
        // По `width` сетей за раз: результаты каждой публикуются сразу,
        // чтобы с девяноста шестью сетями экран не ждал последнюю.
        var queue = catalog[...]
        while !queue.isEmpty {
            let batch = Array(queue.prefix(Self.width))
            queue = queue.dropFirst(Self.width)
            await withTaskGroup(of: Answer.self) { group in
                for chain in batch {
                    group.addTask { await Self.ask(chain, in: region) }
                }
                for await answer in group {
                    let chain = answer.chain
                    guard let result = answer.items else { failed += 1; continue }
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
                }
            }
            venues = found.sorted { $0.distance < $1.distance }
            state = .ready(NearbyMatch.chains(from: venues))
        }

        log.info("Рядом: \(found.count) точек у \(Set(found.map(\.chain)).count) сетей из \(self.catalog.count); не ответили \(failed)")
        if found.isEmpty, failed == catalog.count, !catalog.isEmpty {
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
                          items: try await MKLocalSearch(request: request).start().mapItems)
        } catch {
            // Чаще всего карта просит спрашивать не так часто.
            return Answer(chain: chain, items: nil)
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
