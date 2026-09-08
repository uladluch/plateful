#if DEBUG
import Foundation

/// Данные для превью. В сборку для App Store не попадают.
extension MenuRepository {

    static let preview: MenuRepository = {
        MenuRepository(catalog: previewCatalog)
    }()

    static func previewItem(name: String) -> MenuItem {
        previewCatalog.items.first { $0.name == name } ?? previewCatalog.items[0]
    }

    private static let previewCatalog: MenuCatalog = {
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [
                ["name": "Chick-Fil-A", "itemCount": 1],
                ["name": "McDonald's", "itemCount": 5],
            ],
            "items": [
                ["chain": "Chick-Fil-A", "key": "chicken-sandwich", "name": "Chicken Sandwich",
                 "category": "Entrees", "serving": "1 sandwich",
                 "kcal": 440, "protein": 28, "carbs": 40, "fat": 19],
                ["chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
                 "category": "Burgers", "kcal": 540, "protein": 25, "carbs": 46, "fat": 28],
                ["chain": "McDonald's", "key": "quarter-pounder-w-cheese",
                 "name": "Quarter Pounder w/ Cheese", "category": "Burgers",
                 "serving": "1 sandwich",
                 "kcal": 520, "protein": 30, "carbs": 42, "fat": 26,
                 "source": "mcdonalds.com", "observed": "2026-09-07", "stale": false],
                // Одно блюдо в трёх размерах: превью должно показывать
                // переключатель, а не три карточки картошки подряд.
                ["chain": "McDonald's", "key": "world-famous-fries-small",
                 "name": "World Famous Fries, Small", "category": "Fried Potatoes",
                 "kcal": 230, "protein": 3, "carbs": 30, "fat": 11,
                 "group": "world-famous-fries", "size": "Small", "sizeOrder": 0],
                ["chain": "McDonald's", "key": "world-famous-fries-medium",
                 "name": "World Famous Fries, Medium", "category": "Fried Potatoes",
                 "kcal": 340, "protein": 4, "carbs": 44, "fat": 16,
                 "group": "world-famous-fries", "size": "Medium", "sizeOrder": 1],
                ["chain": "McDonald's", "key": "world-famous-fries-large",
                 "name": "World Famous Fries, Large", "category": "Fried Potatoes",
                 "kcal": 490, "protein": 7, "carbs": 66, "fat": 23,
                 "group": "world-famous-fries", "size": "Large", "sizeOrder": 2],
            ],
        ]
        let data = try! JSONSerialization.data(withJSONObject: json)
        return MenuCatalog(pack: try! MenuPack.decode(from: data))
    }()
}
#endif
