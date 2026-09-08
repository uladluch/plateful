import Foundation
import Testing

@testable import plateful

@Suite("Представление меню")
struct MenuPresentationTests {

    private static func catalog(_ items: [(chain: String, name: String, category: String?)])
        -> MenuCatalog
    {
        let chains = Dictionary(grouping: items, by: \.chain)
            .map { ["name": $0.key, "itemCount": $0.value.count] as [String: Any] }
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": chains,
            "items": items.map { item -> [String: Any] in
                var row: [String: Any] = [
                    "chain": item.chain,
                    "key": item.name.lowercased().replacingOccurrences(of: " ", with: "-"),
                    "name": item.name,
                    "kcal": 100, "protein": 1, "carbs": 2, "fat": 3,
                ]
                if let category = item.category { row["category"] = category }
                return row
            },
        ]
        let data = try! JSONSerialization.data(withJSONObject: json)
        return MenuCatalog(pack: try! MenuPack.decode(from: data))
    }

    /// Порядок категорий берётся из пака, а не из алфавита: источник ставит
    /// завтраки раньше десертов, и это осмысленнее сортировки по букве.
    @Test("категории идут в порядке пака, а не по алфавиту")
    func keepsSourceOrder() {
        let sections = Self.catalog([
            ("McDonald's", "Egg McMuffin", "Breakfast"),
            ("McDonald's", "Big Mac", "Burgers"),
            ("McDonald's", "Sausage Biscuit", "Breakfast"),
            ("McDonald's", "Apple Pie", "Desserts"),
        ]).sections(for: "McDonald's")

        #expect(sections.map(\.title) == ["Breakfast", "Burgers", "Desserts"])
        #expect(sections[0].items.map(\.name) == ["Egg McMuffin", "Sausage Biscuit"])
    }

    @Test("позиции без категории собираются в отдельный раздел")
    func groupsUncategorized() {
        let sections = Self.catalog([
            ("Wendy's", "Baconator", "Burgers"),
            ("Wendy's", "Mystery Item", nil),
        ]).sections(for: "Wendy's")

        #expect(sections.map(\.title) == ["Burgers", MenuSection.uncategorized])
        #expect(sections.last?.items.map(\.name) == ["Mystery Item"])
    }

    @Test("у неизвестной сети разделов нет")
    func emptyForUnknownChain() {
        #expect(Self.catalog([("Wendy's", "Baconator", "Burgers")])
            .sections(for: "Нет такой").isEmpty)
    }

    @Test("калории показываются целым числом")
    func formatsCalories() {
        let item = Self.catalog([("McDonald's", "Big Mac", nil)]).items[0]
        #expect(item.calorieText == "100")
        #expect(!item.calorieText.contains("."))
    }

    @Test("граммы приходят с единицей из системы")
    func formatsGrams() {
        let text = MenuItem.grams(25)
        #expect(text.contains("25"))
        #expect(text.rangeOfCharacter(from: .letters) != nil, "нет единицы измерения: \(text)")
        #expect(!text.contains(".0"))
    }

    /// В интерфейсе не должно быть внутренних слагов вроде `menustat-2018`.
    @Test("источник называется по-человечески")
    func namesSourceForHumans() {
        let item = Self.catalog([("McDonald's", "Big Mac", nil)]).items[0]
        #expect(item.sourceDisplayName == "MenuStat, NYC Dept. of Health")
        #expect(item.observedDisplay == "2018")
        #expect(item.provenanceText.contains("2018"))
    }

    @Test("домен сети показывается как есть")
    func keepsChainDomain() throws {
        let json: [String: Any] = [
            "format": 1, "version": 2,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": 1]],
            "items": [[
                "chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
                "kcal": 580, "protein": 25, "carbs": 45, "fat": 34,
                "source": "mcdonalds.com", "observed": "2026-09-07", "stale": false,
            ]],
        ]
        let catalog = MenuCatalog(
            pack: try MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
        let item = try #require(catalog.items.first)

        #expect(item.sourceDisplayName == "mcdonalds.com")
        #expect(item.observedDisplay == "2026")
    }

    /// Предупреждение обязано исчезать у сверенных позиций — иначе честность
    /// превращается в шум, который перестают читать.
    @Test("предупреждение только у устаревших данных")
    func warnsOnlyWhenStale() throws {
        let stale = Self.catalog([("McDonald's", "Big Mac", nil)]).items[0]
        #expect(stale.staleNotice != nil)
        #expect(stale.staleNotice?.contains("2018") == true)

        let json: [String: Any] = [
            "format": 1, "version": 2,
            "source": "mcdonalds.com", "observed": "2026-09-07", "stale": false,
            "chains": [["name": "McDonald's", "itemCount": 1]],
            "items": [["chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
                       "kcal": 580, "protein": 25, "carbs": 45, "fat": 34]],
        ]
        let fresh = MenuCatalog(
            pack: try MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
        #expect(fresh.items[0].staleNotice == nil)
    }

    @Test("разделы доступны через репозиторий")
    func sectionsThroughRepository() {
        let repository = MenuRepository(catalog: Self.catalog([
            ("McDonald's", "Big Mac", "Burgers"),
        ]))
        #expect(repository.sections(for: "McDonald's").count == 1)
        #expect(repository.sections(for: "Нет такой").isEmpty)
    }
}

@Suite("Витрина по цифрам")
struct HighlightShelfTests {

    private static func catalog(_ items: [[String: Any]]) -> MenuCatalog {
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": items.count]],
            "items": items,
        ]
        let data = try! JSONSerialization.data(withJSONObject: json)
        return MenuCatalog(pack: try! MenuPack.decode(from: data))
    }

    private static func item(_ name: String, kcal: Double, protein: Double = 1,
                              sugar: Double? = nil, serving: String? = nil) -> [String: Any] {
        var row: [String: Any] = [
            "chain": "McDonald's", "key": name.lowercased().replacingOccurrences(of: " ", with: "-"),
            "name": name, "kcal": kcal, "protein": protein, "carbs": 1, "fat": 1,
        ]
        if let sugar { row["sugar"] = sugar }
        if let serving { row["serving"] = serving }
        return row
    }

    /// Бренды и общие слова — по словам целиком, не подстрокой.
    @Test("газировка узнаётся по имени, не по случайной подстроке")
    func recognizesSodaByWholeWord() {
        let catalog = Self.catalog([Self.item("Coca-Cola", kcal: 140), Self.item("Chocolate Shake", kcal: 800)])
        #expect(catalog.items[0].isSoda)
        #expect(!catalog.items[1].isSoda)
    }

    @Test("больше всего белка — первым, по убыванию")
    func highProteinDescends() {
        let catalog = Self.catalog([
            Self.item("Salad", kcal: 200, protein: 5),
            Self.item("Grilled Chicken", kcal: 350, protein: 40),
        ])
        let shelf = catalog.highlightShelves(for: "McDonald's").first { $0.title == "High Protein" }
        #expect(shelf?.items.map(\.name) == ["Grilled Chicken", "Salad"])
    }

    /// Позиция без сахара на этикетке или без веса порции не притворяется
    /// нулём — она просто не участвует в подборке.
    @Test("меньше сахара пропускает позиции без сахара или без веса порции")
    func lessSugarSkipsUnknown() {
        let catalog = Self.catalog([
            Self.item("Fries", kcal: 300, serving: "100 g"),
            Self.item("Apple Slices", kcal: 40, sugar: 8, serving: "200 g"),
            Self.item("Mystery Cookie", kcal: 250, sugar: 20, serving: "1 Slice"),
        ])
        let shelf = catalog.highlightShelves(for: "McDonald's").first { $0.title == "Less Sugar" }
        #expect(shelf?.items.map(\.name) == ["Apple Slices"])
    }

    /// Порог — меньше 6 г сахара на 100 г продукта, а не абсолютная цифра
    /// порции: банка на 500 мл не должна проигрывать стакану на 200 мл
    /// только потому, что у неё больше сахара в граммах.
    @Test("порог считается на 100 г, а не на порцию")
    func lessSugarNormalizesPerHundredGrams() {
        let catalog = Self.catalog([
            // 40 г сахара на 500 г — 8 г/100 г, выше порога.
            Self.item("Big Soda", kcal: 200, sugar: 40, serving: "16.9 fl oz"),
            // 8 г сахара на 200 г — 4 г/100 г, ниже порога.
            Self.item("Small Yogurt", kcal: 120, sugar: 8, serving: "200 g"),
        ])
        let shelf = catalog.highlightShelves(for: "McDonald's").first { $0.title == "Less Sugar" }
        #expect(shelf?.items.map(\.name) == ["Small Yogurt"])
    }

    /// Газировка почти всегда самая низкокалорийная позиция в меню — и
    /// заняла бы подборку целиком, если её не отодвинуть в конец.
    @Test("газировка в подборке «меньше калорий» уходит в конец")
    func lessCaloriesPushesSodaToTheEnd() {
        let catalog = Self.catalog([
            Self.item("Diet Coke", kcal: 0),
            Self.item("Side Salad", kcal: 15),
            Self.item("Big Mac", kcal: 540),
        ])
        let shelf = catalog.highlightShelves(for: "McDonald's").first { $0.title == "Less Calories" }
        #expect(shelf?.items.map(\.name) == ["Side Salad", "Big Mac", "Diet Coke"])
    }

    @Test("снятые с меню позиции в витрину не попадают")
    func offMenuExcluded() throws {
        var offMenuRow = Self.item("Old Burger", kcal: 400)
        offMenuRow["offMenu"] = true
        let catalog = Self.catalog([offMenuRow, Self.item("Big Mac", kcal: 540)])
        let shelf = try #require(catalog.highlightShelves(for: "McDonald's").first { $0.title == "Less Calories" })
        #expect(!shelf.items.contains { $0.name == "Old Burger" })
    }
}
