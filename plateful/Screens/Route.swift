import SwiftData
import SwiftUI

/// Куда можно перейти внутри стека вкладки.
///
/// Одно перечисление и одно место, где маршрут превращается в экран. Раньше
/// переходы были двух видов — по значению и замыканием, — и назначения
/// объявлялись там, где понадобились: экран «Nearby» завёл свой стек внутри
/// стека «Discovery», а шит заведения не знал, куда вести блюдо, и нажатие
/// на карточку в нём молча ничего не делало.
nonisolated enum Route: Hashable {
    case chain(MenuChain)
    case item(MenuItem)
    case archive(MenuChain, [MenuItem])
    case venue(Venue)
    case nearby
    case order(MenuItem)
    /// Ссылка на сохранённый заказ, а не сама модель: заказ могут удалить
    /// свайпом или синхронизацией iCloud, пока его экран открыт.
    case savedOrder(PersistentIdentifier)
    case photoCredits
}

/// Вкладки корня.
enum AppTab: Hashable {
    case discovery, meals, analytics, profile
}

extension View {

    /// Назначения всех маршрутов. Вешается на корень каждого стека — вкладки
    /// и шита, — чтобы экран, открытый где угодно, умел вести дальше.
    func routeDestinations() -> some View {
        navigationDestination(for: Route.self) { RouteDestination(route: $0) }
    }
}

private struct RouteDestination: View {

    let route: Route

    var body: some View {
        switch route {
        case .chain(let chain):
            ChainMenuView(chain: chain)
        case .item(let item):
            ItemDetailView(item: item)
        case .archive(let chain, let items):
            ArchiveMenuView(chain: chain, items: items)
        case .venue(let venue):
            VenueDetailView(venue: venue)
        case .nearby:
            NearbyView()
        case .order(let item):
            OrderView(startingWith: item)
        case .savedOrder(let id):
            SavedOrderDetailView(id: id)
        case .photoCredits:
            PhotoCreditsView()
        }
    }
}
