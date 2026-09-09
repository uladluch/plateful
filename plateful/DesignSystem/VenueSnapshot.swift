import MapKit
import OSLog
import UIKit

/// Снимок заведения: вид с улицы, а если его нет — спутник.
///
/// Нужен ради одной вещи: отличить этот McDonald's от следующего. Фасады у
/// сети одинаковые по замыслу, и опознают точку не по вывеске, а по углу,
/// парковке и тому, с какой стороны к ней подъезжают. Поэтому годятся оба
/// вида: Look Around показывает вывеску с дороги, спутник — форму здания и
/// петлю драйв-тру. Различают они одинаково хорошо.
///
/// Ничего не сохраняется на диск и не уезжает к нам в базу: условия Apple
/// Maps разрешают показывать эти кадры в приложении, но не складывать их.
/// Отсюда и устройство — только память, которую система вправе забрать.
@MainActor
final class VenueSnapshot {

    static let shared = VenueSnapshot()

    /// Сколько кадров держим в памяти. Ступеней размера всего две — строка
    /// списка и карточка, — так что это сотни заведений, больше чем бывает
    /// в одном сеансе.
    nonisolated static let memoryLimit = 32 << 20

    /// Сколько кадров рисуется разом. `MKMapSnapshotter` — не бесплатная
    /// вещь: два десятка одновременных снимков видимых строк отвечают
    /// ошибкой вместо картинки, и список остаётся с пустыми квадратами.
    nonisolated static let width = 3

    /// Сторона квадрата вокруг точки. Полтораста метров — здание с
    /// парковкой и кусок улицы; ближе видно только крышу, дальше здание
    /// теряется среди соседних.
    nonisolated static let span: CLLocationDistance = 150

    private let memory = NSCache<NSString, UIImage>()
    private var inFlight: [String: Task<UIImage?, Never>] = [:]
    private var running = 0
    private var waiting: [CheckedContinuation<Void, Never>] = []
    private let log = Logger(subsystem: "com.anluch.plateful", category: "photos")

    init() {
        memory.totalCostLimit = Self.memoryLimit
    }

    /// Ключ кэша. Размер входит в него: карточка просит крупный кадр, и
    /// подсунуть ей растянутый кадр строки значит показать мыло.
    nonisolated static func key(_ venue: Venue, side: CGFloat) -> String {
        "\(venue.id)@\(Int(side.rounded()))"
    }

    /// Готовый кадр, если он уже в памяти. Синхронно — чтобы строка не
    /// мигала заглушкой на возврате из карточки.
    func cached(_ venue: Venue, side: CGFloat) -> UIImage? {
        memory.object(forKey: Self.key(venue, side: side) as NSString)
    }

    func image(for venue: Venue, side: CGFloat) async -> UIImage? {
        let key = Self.key(venue, side: side)
        if let ready = memory.object(forKey: key as NSString) { return ready }
        if let running = inFlight[key] { return await running.value }

        let task = Task { [weak self] () -> UIImage? in
            guard let self else { return nil }
            await self.enter()
            defer { self.leave() }
            let (image, source) = await Self.render(venue: venue, side: side)
            self.log.info("Кадр \(venue.id, privacy: .public): \(source, privacy: .public)")
            if let image {
                self.memory.setObject(image, forKey: key as NSString,
                                      cost: Int(image.size.width * image.size.height * 4))
            }
            return image
        }
        inFlight[key] = task
        let image = await task.value
        inFlight[key] = nil
        return image
    }

    // MARK: - Очередь

    private func enter() async {
        if running < Self.width {
            running += 1
            return
        }
        await withCheckedContinuation { waiting.append($0) }
        running += 1
    }

    private func leave() {
        running -= 1
        guard !waiting.isEmpty else { return }
        waiting.removeFirst().resume()
    }

    // MARK: - Рисование

    /// Кадр и то, откуда он взялся: по логу видно, какая доля точек
    /// получила вид с улицы, а какая обошлась спутником.
    private static func render(venue: Venue,
                               side: CGFloat) async -> (UIImage?, String) {
        let coordinate = CLLocationCoordinate2D(latitude: venue.latitude,
                                                longitude: venue.longitude)
        let size = CGSize(width: side, height: side)
        if let street = await lookAround(at: coordinate, size: size) {
            return (street, "с улицы")
        }
        if let sky = await satellite(at: coordinate, size: size) {
            return (sky, "спутник")
        }
        return (nil, "нет кадра")
    }

    /// Вид с улицы. Есть не везде: за пределами городов и трасс Apple
    /// возвращает пустую сцену, и это не ошибка, а отсутствие покрытия.
    private static func lookAround(at coordinate: CLLocationCoordinate2D,
                                   size: CGSize) async -> UIImage? {
        guard let scene = try? await MKLookAroundSceneRequest(coordinate: coordinate).scene
        else { return nil }
        let options = MKLookAroundSnapshotter.Options()
        options.size = size
        // Значки чужих заведений в кадре размером с ноготь только мешают.
        options.pointOfInterestFilter = .excludingAll
        return try? await MKLookAroundSnapshotter(scene: scene, options: options)
            .snapshot.image
    }

    /// Спутник с подписями: видно здание, парковку и перекрёсток — то, чем
    /// одна точка сети отличается от другой.
    private static func satellite(at coordinate: CLLocationCoordinate2D,
                                  size: CGSize) async -> UIImage? {
        let options = MKMapSnapshotter.Options()
        options.region = MKCoordinateRegion(center: coordinate,
                                            latitudinalMeters: span,
                                            longitudinalMeters: span)
        options.size = size
        options.preferredConfiguration = MKHybridMapConfiguration()
        options.pointOfInterestFilter = .excludingAll
        return try? await MKMapSnapshotter(options: options).start().image
    }
}
