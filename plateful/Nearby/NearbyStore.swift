import CoreLocation
import MapKit
import Observation
import OSLog

/// Что рядом: геопозиция у системы, заведения у карты, сети из каталога.
///
/// Своих данных о ресторанах приложение не хранит вовсе. Три крупнейшие
/// сети США — это уже больше пятидесяти тысяч точек, а все девяносто шесть
/// дали бы за полтораста тысяч адресов: их пришлось бы собирать, лицензировать
/// и возить в паке ради ответа, который карта даёт запросом с устройства
/// и всегда свежим.
///
/// Разрешение спрашиваем в момент, когда человек сам открыл экран «рядом», —
/// не на старте. Приложение обещает работать без онбординга, и диалог о
/// геопозиции при первом запуске это обещание нарушал бы.
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

    /// Радиус поиска. Пятьдесят километров — потолок
    /// `MKLocalPointsOfInterestRequest`; столько и не нужно, но у карты
    /// свои соображения о том, сколько результатов вернуть.
    static let radius: CLLocationDistance = 5_000

    private let manager = CLLocationManager()
    private let log = Logger(subsystem: "com.anluch.plateful", category: "nearby")
    private var catalog: [String] = []
    private var pending = false

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
            let places = response.mapItems.compactMap { item in
                Self.place(from: item, origin: origin)
            }
            let found = NearbyMatch.chains(near: places, in: catalog)
            log.info("Рядом: \(places.count) заведений, из них наших сетей \(found.count)")
            // Чего мы не узнали — список сетей, которых не хватает каталогу.
            // Человек стоит рядом с ними прямо сейчас, и это лучший
            // приоритет для следующего адаптера, чем размер сети.
            let unknown = Set(places.map(\.name))
                .subtracting(found.map(\.nearest.name))
                .sorted()
                .prefix(12)
            log.info("Не опознаны: \(unknown.joined(separator: ", "))")
            state = .ready(found)
        } catch {
            log.error("Поиск рядом не удался: \(error.localizedDescription)")
            state = .failed(error.localizedDescription)
        }
    }

    /// `MKMapItem` → наше значение. Всё, что карта готова рассказать:
    /// имя, координата и адрес. Часов работы среди её свойств нет.
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
