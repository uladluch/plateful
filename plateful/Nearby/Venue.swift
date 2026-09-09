import Foundation

// Значения: считаются вне главного потока и проверяются без карты.

/// Заведение сети, которое нашла карта.
///
/// Только то, что `MKMapItem` отдаёт данными: имя, координата, адрес,
/// телефон. Часов работы, снимков и ценника среди его свойств нет — их
/// показывает карточка места, которую рисует сама Apple, и ей нужен сам
/// `MKMapItem`; он живёт в хранилище рядом с этим значением.
nonisolated struct Venue: Identifiable, Hashable, Sendable {
    /// Имя сети ровно как в каталоге: по нему открывается меню.
    let chain: String
    /// Идентификатор места у Apple, а без него — координата: две точки
    /// одной сети различаются и так.
    let extKey: String
    let latitude: Double
    let longitude: Double
    let address: String
    let phone: String?
    /// Метры от человека до заведения.
    let distance: Double

    var id: String { "\(chain)#\(extKey)" }
}
