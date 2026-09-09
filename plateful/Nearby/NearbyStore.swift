import CoreLocation
import MapKit
import Observation
import OSLog

/// Что рядом: геопозиция у системы, заведения из нашей базы, меню из пака.
///
/// Раньше список заведений спрашивали у карты Apple и опознавали ответ по
/// имени. Так нельзя знать заранее, что показываешь: на Таймс-сквер из 48
/// заведений вокруг опознавались два. Теперь точки свои — те же сети,
/// которые публикуют их у себя на сайте, — и на карте ровно то, чьё меню
/// приложение умеет открыть.
///
/// Карта остаётся запасным путём: интернет бывает плохим, а «ничего не
/// нашлось» на экране «рядом» — плохой ответ, когда вокруг всё же стоит
/// знакомая вывеска.
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

    /// Откуда взялись точки. Видно на экране: у карты нет часов работы, и
    /// молча показывать заведение без них как полноценное — обман.
    enum Source: Equatable {
        case catalog
        case map
    }

    private(set) var state: State = .idle
    private(set) var venues: [Venue] = []
    private(set) var source: Source = .catalog

    /// Радиус поиска.
    static let radius: CLLocationDistance = 5_000

    private let manager = CLLocationManager()
    private let service: any VenueTransport
    private let log = Logger(subsystem: "com.anluch.plateful", category: "nearby")
    private var catalog: [String] = []
    private var pending = false

    init(service: any VenueTransport = SupabaseVenues()) {
        self.service = service
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
    }

    /// Спрашивает, что рядом. Каталог передаётся снаружи: хранилище знает
    /// про геопозицию, но не про меню.
    func find(chains: [String]) {
        catalog = chains
        pending = true
        venues = []

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

    private func search(around coordinate: CLLocationCoordinate2D) async {
        state = .searching
        do {
            let found = try await service.venues(
                latitude: coordinate.latitude, longitude: coordinate.longitude,
                radius: Self.radius, chains: catalog)
            let chains = NearbyMatch.chains(from: found)
            let withHours = found.count { $0.hours != nil }
            log.info("Рядом: \(found.count) наших точек у \(chains.count) сетей, часы у \(withHours)")
            venues = found
            source = .catalog
            state = .ready(chains)
        } catch {
            log.error("База точек не ответила: \(error.localizedDescription)")
            await searchOnMap(around: coordinate)
        }
    }

    /// Запасной путь: спросить карту и опознать её ответ по именам сетей.
    ///
    /// Ответ беднее — часов работы у карты нет вовсе, — но лучше, чем пустой
    /// экран при плохой связи.
    private func searchOnMap(around coordinate: CLLocationCoordinate2D) async {
        let request = MKLocalPointsOfInterestRequest(
            center: coordinate, radius: Self.radius)
        // Фастфуда отдельной категорией у карты нет — он лежит в
        // «ресторанах». Кофейни и пекарни нужны отдельно: Starbucks и
        // Dunkin' приходят как кафе, Krispy Kreme как пекарня.
        request.pointOfInterestFilter = MKPointOfInterestFilter(
            including: [.restaurant, .cafe, .bakery])

        do {
            let response = try await MKLocalSearch(request: request).start()
            let origin = CLLocation(latitude: coordinate.latitude,
                                    longitude: coordinate.longitude)
            let places = response.mapItems.compactMap { Self.place(from: $0, origin: origin) }
            let found = NearbyMatch.venues(among: places, in: NearbyCatalog(catalog))
            log.info("Запасной путь: карта дала \(places.count) заведений, наших \(found.count)")
            venues = found
            source = .map
            state = .ready(NearbyMatch.chains(from: found))
        } catch {
            log.error("И карта не ответила: \(error.localizedDescription)")
            venues = []
            state = .failed(error.localizedDescription)
        }
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
