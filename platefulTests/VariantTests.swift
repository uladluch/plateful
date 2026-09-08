import Foundation
import Testing

@testable import plateful

/// Размерные варианты одного блюда.
///
/// Четыре карточки колы подряд — не выбор, а шум, поэтому в списке группа
/// занимает одну строку, а размеры уходят в переключатель на карточке.
/// Группу считает конвейер; здесь проверяется, что приложение её понимает.
@Suite("Варианты одного блюда")
struct VariantTests {

    private struct Row {
        let name: String
        let kcal: Double
        var group: String?
        var size: String?
        var order: Int?
        var kind: String = "size"
        var photo: Bool = false
        var category: String = "Drinks"
    }

    private static func catalog(_ rows: [Row]) -> MenuCatalog {
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "sections": ["Drinks", "Burgers", "Sides", "Salads"],
            "chains": [["name": "McDonald's", "itemCount": rows.count]],
            "items": rows.map { row -> [String: Any] in
                var item: [String: Any] = [
                    "chain": "McDonald's",
                    "key": row.name.lowercased()
                        .replacingOccurrences(of: ", ", with: "-")
                        .replacingOccurrences(of: " ", with: "-"),
                    "name": row.name, "category": row.category,
                    "section": row.category,
                    "kcal": row.kcal, "protein": row.kcal / 100,
                    "carbs": 40, "fat": 25,
                ]
                if let group = row.group, let size = row.size {
                    // База — как её считает конвейер: имя без подписи.
                    let base = row.name
                        .replacingOccurrences(of: ", \(size)", with: "")
                        .replacingOccurrences(of: " w/ \(size)", with: "")
                        .replacingOccurrences(of: "\(size) ", with: "")
                    item["variant"] = ["group": group, "label": size,
                                       "order": row.order ?? 0, "kind": row.kind,
                                       "base": size == "Plain" ? row.name : base]
                }
                if row.photo {
                    item["photo"] = ["url": "https://example.com/a.jpg",
                                     "license": "© McDonald's"]
                }
                return item
            },
        ]
        return MenuCatalog(
            pack: try! MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
    }

    private static let cola = [
        Row(name: "Coca Cola, Large", kcal: 290, group: "coca-cola", size: "Large", order: 3),
        Row(name: "Coca Cola, Extra Small", kcal: 100, group: "coca-cola",
            size: "Extra Small", order: 0),
        Row(name: "Coca Cola, Medium", kcal: 210, group: "coca-cola", size: "Medium", order: 2),
        Row(name: "Coca Cola, Small", kcal: 150, group: "coca-cola", size: "Small", order: 1),
        Row(name: "Big Mac", kcal: 540, category: "Burgers"),
    ]

    /// Позиции в паке отсортированы по названию, и «Large» лежит первой.
    /// Порядок сегментов должен идти от `sizeOrder`, а не от порядка строк.
    @Test("размеры выстраиваются по sizeOrder, а не по порядку в паке")
    func ordersBySizeOrder() {
        let catalog = Self.catalog(Self.cola)
        let any = catalog.items(in: "McDonald's").first { $0.variant != nil }!

        #expect(catalog.variants(of: any).map { $0.variant?.label }
            == ["Extra Small", "Small", "Medium", "Large"])
    }

    @Test("у блюда без размеров вариантов нет")
    func plainItemHasNoVariants() {
        let catalog = Self.catalog(Self.cola)
        let bigMac = catalog.items(in: "McDonald's").first { $0.name == "Big Mac" }!

        #expect(catalog.variants(of: bigMac).isEmpty)
        #expect(bigMac.variant == nil)
        #expect(bigMac.baseName == "Big Mac")
    }

    /// Переключатель с одним сегментом бесполезен, а карточка при этом
    /// теряет размер из названия — «Apple Slices» вместо «1 Package».
    @Test("одинокий размер группой не считается")
    func singleVariantIsNotAGroup() {
        let catalog = Self.catalog([
            Row(name: "Apple Slices, 1 Package", kcal: 15,
                group: "apple-slices", size: "1 Package", order: 0),
        ])
        let item = catalog.items(in: "McDonald's")[0]

        #expect(catalog.variants(of: item).isEmpty)
        #expect(catalog.collapsingVariants([item]).count == 1)
    }

    @Test("название теряет только размер, а не хвост после запятой")
    func baseNameDropsOnlyTheSize() {
        let catalog = Self.catalog([
            Row(name: "Iced Coffee, Vanilla, Small", kcal: 100,
                group: "iced-coffee-vanilla", size: "Small", order: 0),
            Row(name: "Iced Coffee, Vanilla, Large", kcal: 200,
                group: "iced-coffee-vanilla", size: "Large", order: 1),
            Row(name: "Cobb Salad, w/ Nuggets", kcal: 500, category: "Salads"),
        ])
        let items = catalog.items(in: "McDonald's")

        #expect(items.first { $0.variant?.label == "Small" }?.baseName == "Iced Coffee, Vanilla")
        #expect(items.first { $0.name.hasPrefix("Cobb") }?.baseName == "Cobb Salad, w/ Nuggets")
    }

    @Test("название теряет счёт, стоящий перед ним")
    func baseNameDropsALeadingCount() {
        let catalog = Self.catalog([
            Row(name: "4 Chicken McNuggets", kcal: 180, group: "chicken-mcnugget",
                size: "4", order: 0, category: "Entrees"),
            Row(name: "10 Chicken McNuggets", kcal: 440, group: "chicken-mcnugget",
                size: "10", order: 1, category: "Entrees"),
        ])

        #expect(catalog.items(in: "McDonald's").map(\.baseName)
            == ["Chicken McNuggets", "Chicken McNuggets"])
    }

    @Test("название теряет добавку после «w/», но не саму базу")
    func baseNameDropsTheOption() {
        let catalog = Self.catalog([
            Row(name: "Big Breakfast", kcal: 750, group: "big-breakfast",
                size: "Plain", order: 0, kind: "option", category: "Breakfast"),
            Row(name: "Big Breakfast w/ Hotcakes", kcal: 1350, group: "big-breakfast",
                size: "Hotcakes", order: 1, kind: "option", category: "Breakfast"),
        ])

        #expect(catalog.items(in: "McDonald's").map(\.baseName)
            == ["Big Breakfast", "Big Breakfast"])
    }

    /// Сокращать нечего: в исполнении блюда не шкала, а список, и первая
    /// буква «Egg» ничего не значит.
    @Test("подписи исполнений не сокращаются")
    func optionLabelsStayWhole() {
        let option = MenuItem.Variant(group: "g", label: "Large", order: 0, kind: .option, base: nil)
        #expect(option.shortLabel == "Large")
    }

    // MARK: - Свёртка списка

    @Test("группа занимает в списке одну строку")
    func collapsesToOneRow() {
        let catalog = Self.catalog(Self.cola)
        let collapsed = catalog.collapsingVariants(catalog.items(in: "McDonald's"))

        #expect(collapsed.count == 2)
        #expect(collapsed.contains { $0.name == "Big Mac" })
        #expect(collapsed.filter { $0.variant != nil }.count == 1)
    }

    /// Середина ряда описывает блюдо честнее, чем детская порция или ведро.
    @Test("группу представляет средний размер")
    func picksTheMiddleSize() {
        let catalog = Self.catalog(Self.cola)
        let collapsed = catalog.collapsingVariants(catalog.items(in: "McDonald's"))

        #expect(collapsed.first { $0.variant != nil }?.variant?.label == "Small")
    }

    /// Пустая карточка там, где снимок лежит у соседнего сегмента,
    /// читается как потерянная картинка.
    @Test("если снят только один размер, представляет он")
    func prefersThePhotographedSize() {
        let catalog = Self.catalog([
            Row(name: "Waffle Fries, Small", kcal: 300, group: "waffle-fries",
                size: "Small", order: 0, category: "Sides"),
            Row(name: "Waffle Fries, Medium", kcal: 400, group: "waffle-fries",
                size: "Medium", order: 1, category: "Sides"),
            Row(name: "Waffle Fries, Large", kcal: 500, group: "waffle-fries",
                size: "Large", order: 2, photo: true, category: "Sides"),
        ])
        let collapsed = catalog.collapsingVariants(catalog.items(in: "McDonald's"))

        #expect(collapsed.map { $0.variant?.label } == ["Large"])
    }

    @Test("свёртка сохраняет порядок и место группы в списке")
    func keepsOrder() {
        let catalog = Self.catalog([
            Row(name: "Apple Pie", kcal: 240, category: "Desserts"),
            Row(name: "Coca Cola, Small", kcal: 150, group: "coca-cola", size: "Small", order: 0),
            Row(name: "Coca Cola, Large", kcal: 290, group: "coca-cola", size: "Large", order: 1),
            Row(name: "Big Mac", kcal: 540, category: "Burgers"),
        ])
        let collapsed = catalog.collapsingVariants(catalog.items(in: "McDonald's"))

        #expect(collapsed.map(\.baseName) == ["Apple Pie", "Coca Cola", "Big Mac"])
    }

    /// Свёртка идёт после фильтра. Иначе цель «до 200 ккал» вычеркнула бы
    /// всю колу из-за среднего размера, хотя маленькая в цель укладывается.
    @Test("фильтр видит все размеры, а не только представителя")
    func filterSeesEveryVariant() {
        let catalog = Self.catalog(Self.cola)
        var filter = MenuFilter.none
        filter.maxCalories = 200

        let shown = catalog.collapsingVariants(
            filter.apply(to: catalog.items(in: "McDonald's")))

        #expect(shown.count == 1)
        #expect(shown[0].baseName == "Coca Cola")
        #expect(shown[0].kcal <= 200)
    }

    @Test("разделы меню тоже сворачиваются")
    func collapsesSections() {
        let catalog = Self.catalog(Self.cola)
        let sections = catalog.collapsingVariants(catalog.sections(for: "McDonald's"))

        #expect(sections.map(\.title) == ["Drinks", "Burgers"])
        #expect(sections[0].items.count == 1)
    }

    /// Какой размер представляет группу в выдаче, решает запрос: «coca cola
    /// large» поднимает Large выше остальных сам.
    @Test("в поиске остаётся самый релевантный размер")
    func searchKeepsTheBestMatch() {
        let catalog = Self.catalog(Self.cola)
        let results = catalog.collapsingVariants(catalog.search("coca cola large"))

        #expect(results.count == 1)
        #expect(results[0].variant?.label == "Large")
    }

    // MARK: - Строка списка

    @Test("в строке показывается диапазон калорий по размерам")
    func showsCalorieRange() {
        let catalog = Self.catalog(Self.cola)
        let variants = catalog.variants(
            of: catalog.items(in: "McDonald's").first { $0.variant != nil }!)

        #expect(variants.calorieRangeText == "100–290")
    }

    @Test("одинаковые числа диапазоном не показываются")
    func collapsesEqualRange() {
        let catalog = Self.catalog([
            Row(name: "Coffee, Small", kcal: 5, group: "coffee", size: "Small", order: 0),
            Row(name: "Coffee, Large", kcal: 5, group: "coffee", size: "Large", order: 1),
        ])
        let variants = catalog.variants(of: catalog.items(in: "McDonald's")[0])

        #expect(variants.calorieRangeText == "5")
    }

    // MARK: - Подписи на сегментах

    /// «S · M · L» — то, чем размеры подписаны на табло у кассы.
    @Test("словарные размеры сокращаются до буквы")
    func abbreviatesKnownSizes() {
        let short = ["Extra Small": "XS", "Small": "S", "Medium": "M",
                     "Large": "L", "Extra Large": "XL", "Regular": "Reg"]
        for (label, expected) in short {
            #expect(MenuItem.Variant(group: "g", label: label, order: 0, kind: .size, base: nil).shortLabel == expected)
        }
    }

    /// Источник пишет и «Large», и «large».
    @Test("регистр в подписи не мешает сокращению")
    func abbreviationIgnoresCase() {
        #expect(MenuItem.Variant(group: "g", label: "large", order: 0, kind: .size, base: nil).shortLabel == "L")
    }

    /// Единица повторяется в каждом сегменте, места не стоит, а полное
    /// «12 oz» остаётся в строке «Serving» под переключателем.
    @Test("у объёма остаётся число без единицы")
    func dropsVolumeUnit() {
        #expect(MenuItem.Variant(group: "g", label: "12 oz", order: 0, kind: .size, base: nil).shortLabel == "12")
        #expect(MenuItem.Variant(group: "g", label: "16 fl oz", order: 0, kind: .size, base: nil).shortLabel == "16")
        #expect(MenuItem.Variant(group: "g", label: "1.5 fl oz", order: 0, kind: .size, base: nil).shortLabel == "1.5")
    }

    /// «Grande» — имя, а не мера: «G» рядом с «Venti» ничего не значит.
    @Test("фирменные и штучные размеры остаются как есть")
    func keepsNamedSizes() {
        for label in ["Kids", "Snack", "Mini", "Jr", "Short", "Tall",
                      "Grande", "Venti", "Bowl", "Cup", "2 Slices"] {
            #expect(MenuItem.Variant(group: "g", label: label, order: 0, kind: .size, base: nil).shortLabel == label)
        }
    }

    /// Сокращение экономит ширину, а не смысл: в паке не должно оказаться
    /// подписи, которая после сокращения стала пустой или чужой.
    @Test("в паке из бандла каждое сокращение непусто и коротко")
    func realSeedAbbreviationsAreSane() throws {
        let url = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"))
        let catalog = MenuCatalog(pack: try MenuPack.decode(from: Data(contentsOf: url)))
        let sizes = catalog.items.compactMap(\.variant)

        #expect(!sizes.isEmpty)
        #expect(sizes.allSatisfy { !$0.shortLabel.isEmpty })
        #expect(sizes.allSatisfy { $0.shortLabel.count <= $0.label.count })
    }

    // MARK: - Настоящие данные

    /// Группы считает конвейер, а показывает приложение. Проверка на паке из
    /// бандла ловит расхождение между ними — синтетические строки этого не
    /// умеют, они собраны по тем же правилам, что и ожидания.
    @Test("в паке из бандла размеры колы собраны в одну строку")
    func realSeedCollapsesCola() throws {
        let url = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"),
            "seed-pack.json нет в бандле — проверьте build_seed.py")
        let catalog = MenuCatalog(pack: try MenuPack.decode(from: Data(contentsOf: url)))

        let all = catalog.items(in: "McDonald's")
        let cola = try #require(all.first { $0.baseName == "Coca Cola" && $0.variant != nil })
        #expect(catalog.variants(of: cola).map { $0.variant?.label }
            == ["Extra Small", "Small", "Medium", "Large"])

        let collapsed = catalog.collapsingVariants(all)
        #expect(collapsed.count < all.count)
        // Каждая группа — ровно одна строка.
        let groups = collapsed.compactMap(\.variantGroupID)
        #expect(Set(groups).count == groups.count)
    }

    /// Единица одна на весь диапазон: «1 g–3 g» читается хуже, чем «1–3 g».
    @Test("у белка единица стоит один раз, в конце")
    func proteinRangeCarriesOneUnit() {
        let catalog = Self.catalog(Self.cola)
        let variants = catalog.variants(
            of: catalog.items(in: "McDonald's").first { $0.variant != nil }!)
        let text = variants.proteinRangeText

        #expect(text.hasPrefix("1–3"))
        #expect(text == "1–" + MenuItem.grams(2.9))
    }
}

/// Остальная этикетка: сахар, насыщенные жиры, натрий, клетчатка.
///
/// «Нет числа» значит, что сеть его не публикует, а не что там ноль.
/// Показать ноль вместо пробела у сахара — прямой вред тому, кто его считает.
@Suite("Этикетка")
struct LabelNutrientTests {

    private static func catalog(_ row: [String: Any]) -> MenuCatalog {
        var item: [String: Any] = [
            "chain": "McDonald's", "key": "big-mac", "name": "Big Mac",
            "kcal": 540, "protein": 25, "carbs": 46, "fat": 28,
        ]
        item.merge(row) { _, new in new }
        let json: [String: Any] = [
            "format": 1, "version": 1,
            "source": "menustat-2018", "observed": "2018-12-31", "stale": true,
            "chains": [["name": "McDonald's", "itemCount": 1]],
            "items": [item],
        ]
        return MenuCatalog(
            pack: try! MenuPack.decode(from: JSONSerialization.data(withJSONObject: json)))
    }

    @Test("этикетка доезжает из пака")
    func readsTheLabel() {
        let item = Self.catalog(["sugar": 9, "satFat": 10, "transFat": 1,
                                 "cholesterol": 80, "sodium": 950, "fiber": 3]).items[0]

        #expect(item.sugarText == MenuItem.grams(9))
        #expect(item.satFatText == MenuItem.grams(10))
        #expect(item.fiberText == MenuItem.grams(3))
        #expect(item.transFat == 1)
        #expect(item.cholesterol == 80)
    }

    /// Холестерин, как и натрий, стоит на этикетке в миллиграммах.
    @Test("холестерин показывается в миллиграммах")
    func cholesterolInMilligrams() {
        let item = Self.catalog(["cholesterol": 80]).items[0]

        #expect(item.cholesterolText?.contains("80") == true)
        #expect(item.cholesterolText?.contains("mg") == true)
    }

    /// Трансжиры меряют долями грамма, и «0.5 г» при округлении до целого
    /// стало бы успокоительным нулём.
    ///
    /// Сравниваем с нулевой отрисовкой, а не с литералом «0.5»: разделитель
    /// дробной части приходит из локали, и на машине с запятой литерал
    /// провалил бы тест, ничего не сказав о самом округлении.
    @Test("трансжиры не округляются до нуля")
    func transFatKeepsTheFraction() {
        let item = Self.catalog(["transFat": 0.5]).items[0]

        #expect(item.transFatText != MenuItem.grams(0))
        #expect(item.transFatText != MenuItem.grams(1))
    }

    /// Натрий стоит на этикетке в миллиграммах, и сравнивают его с дневной
    /// нормой в них же. Показать «0.95 g» — заставить считать в уме.
    @Test("натрий показывается в миллиграммах")
    func sodiumInMilligrams() {
        let item = Self.catalog(["sodium": 950]).items[0]

        #expect(item.sodiumText?.contains("950") == true)
        #expect(item.sodiumText?.contains("mg") == true)
    }

    @Test("отсутствие числа не превращается в ноль")
    func missingIsNotZero() {
        let item = Self.catalog([:]).items[0]

        #expect(item.sugar == nil)
        #expect(item.sugarText == nil)
        #expect(item.sodiumText == nil)
        #expect(item.transFatText == nil)
        #expect(item.cholesterolText == nil)
    }

    /// Ноль — законное число: у диетической колы сахара действительно нет.
    @Test("честный ноль показывается")
    func zeroIsShown() {
        let item = Self.catalog(["sugar": 0]).items[0]

        #expect(item.sugarText == MenuItem.grams(0))
    }

    @Test("в паке из бандла сахар есть почти у всех")
    func realSeedHasSugar() throws {
        let url = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"))
        let catalog = MenuCatalog(pack: try MenuPack.decode(from: Data(contentsOf: url)))
        let withSugar = catalog.items.count { $0.sugar != nil }

        #expect(Double(withSugar) / Double(catalog.items.count) > 0.95)
        let bigMac = try #require(
            catalog.items(in: "McDonald's").first { $0.name == "Big Mac" })
        #expect(bigMac.sugar == 9)
        #expect(bigMac.sodium == 950)
        #expect(bigMac.cholesterol == 80)
        #expect(bigMac.transFat == 1)
    }

    /// Доля не бывает больше целого. Конвейер гасит такие числа, и в паке,
    /// который едет в бандле, их быть не должно ни одного: «Diet Dr Pepper»
    /// с нулём углеводов и 96 г сахара — сломанное число, а не напиток.
    @Test("в паке из бандла нет долей больше целого")
    func noFractionExceedsItsWhole() throws {
        let url = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"))
        let catalog = MenuCatalog(pack: try MenuPack.decode(from: Data(contentsOf: url)))

        let broken = catalog.items.filter {
            ($0.sugar ?? 0) > $0.carbs + 1 || ($0.fiber ?? 0) > $0.carbs + 1
                || ($0.satFat ?? 0) > $0.fat + 1 || ($0.transFat ?? 0) > $0.fat + 1
        }

        #expect(broken.isEmpty)
    }

    @Test("холестерин и трансжиры есть почти у всех")
    func realSeedHasTheRestOfTheLabel() throws {
        let url = try #require(
            Bundle.main.url(forResource: PackStore.seedResource, withExtension: "json"))
        let catalog = MenuCatalog(pack: try MenuPack.decode(from: Data(contentsOf: url)))

        let withCholesterol = catalog.items.count { $0.cholesterol != nil }
        let withTransFat = catalog.items.count { $0.transFat != nil }

        #expect(Double(withCholesterol) / Double(catalog.items.count) > 0.95)
        #expect(Double(withTransFat) / Double(catalog.items.count) > 0.90)
    }
}
