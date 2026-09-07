---
name: ios-native-ui
description: Правила UI для iOS-приложений uladluch — системный подход на iOS 26 SDK. Использовать при любой работе со SwiftUI/UIKit-вёрсткой, шрифтами, цветами, компонентами, дизайн-токенами, при ревью UI-кода и при выборе «системный компонент или кастом».
---

# iOS Native UI — системный подход

Целевой SDK: **iOS 26** (Xcode 26, Liquid Glass). Локальный SDK:
`/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS26.5.sdk`

## Три правила, которые не обсуждаются

### 1. Сначала системный компонент, кастом — только если его нет

Порядок действий перед любой новой вью:
1. Спросить: «какой системный компонент это делает?» — `List`, `Form`, `NavigationStack`,
   `TabView`, `Picker`, `Toggle`, `Slider`, `Menu`, `ContentUnavailableView`, `.searchable`,
   `.sheet`, `.confirmationDialog`, `.swipeActions`, `.refreshable`, `Label`, `Gauge`,
   `ProgressView`, `ShareLink`, `Section` с header/footer.
2. Проверить, что API есть в SDK (см. «Как проверить API» ниже).
3. Только если системного нет — писать кастом, и он должен выглядеть как системный:
   те же отступы, те же шрифты, те же цвета, та же реакция на Dynamic Type и Dark Mode.

Запрещено переизобретать: свои навбары, свои таббары, свои свитчи, свои списки на `VStack`
вместо `List`, свои шиты. Если кажется, что системный «не такой» — сначала искать
модификатор (`.listStyle`, `.toolbar`, `.navigationBarTitleDisplayMode`, `.buttonStyle`,
`.pickerStyle`), потом кастом.

### 2. Только системные шрифты и только текстовые стили. `.rounded` запрещён

- Всегда через семантические стили: `.largeTitle`, `.title`, `.title2`, `.title3`,
  `.headline`, `.subheadline`, `.body`, `.callout`, `.footnote`, `.caption`, `.caption2`.
- Начертание — модификаторами стиля: `.fontWeight(.semibold)`, `.bold()`, `.italic()`,
  `.monospacedDigit()` для чисел в таблицах.
- **`Font.Design` — только `.default`.** `.rounded`, `.serif`, `.monospaced` как дизайн — нет.
  (`.monospacedDigit()` — это не дизайн, а фича шрифта, разрешён для цифр.)
- Запрещено: `Font.custom(...)`, `.system(size: 17)` с жёстким размером, `UIFont(name:)`.
  Если нужен размер «между» — берём ближайший стиль, не число. Dynamic Type должен работать.

```swift
// ✅
Text("540").font(.title).fontWeight(.semibold).monospacedDigit()
Text("kcal").font(.caption).foregroundStyle(.secondary)

// ❌
Text("540").font(.system(size: 28, weight: .semibold, design: .rounded))
```

### 3. Только системные цвета, и только через токены

Никаких литералов цвета в вью. Все цвета — через один файл токенов, который
маппит семантику на системные цвета. Менять дизайн-систему = менять один файл.

```swift
// DesignSystem/Tokens.swift
enum Tokens {
    enum Color {
        static let textPrimary   = SwiftUI.Color.primary
        static let textSecondary = SwiftUI.Color.secondary
        static let background    = SwiftUI.Color(.systemBackground)
        static let groupedBg     = SwiftUI.Color(.systemGroupedBackground)
        static let cardBg        = SwiftUI.Color(.secondarySystemGroupedBackground)
        static let separator     = SwiftUI.Color(.separator)
        static let accent        = SwiftUI.Color.accentColor
        // макросы — тоже системные
        static let protein = SwiftUI.Color(.systemBlue)
        static let carbs   = SwiftUI.Color(.systemOrange)
        static let fat     = SwiftUI.Color(.systemPink)
        static let kcal    = SwiftUI.Color.primary
    }
    enum Spacing { static let xs: CGFloat = 4, s: CGFloat = 8, m: CGFloat = 16, l: CGFloat = 24 }
    enum Radius  { static let card: CGFloat = 12 }
}
```

- Разрешённые источники цвета: `Color.primary/.secondary/.accentColor`, `Color(.system…)`,
  `Color(.label)/(.secondaryLabel)/(.tertiaryLabel)`, `.tint`, `foregroundStyle(.secondary)`,
  системные `.systemRed/.systemBlue/...`.
- Запрещено: `Color(red:green:blue:)`, `Color(hex:)`, `Color("Name")` из ассетов (кроме
  `AccentColor`), `.white/.black` как цвет текста или фона.
- Материалы — системные: `.regularMaterial`, `.thinMaterial`, `.glassEffect()` (iOS 26).

## iOS 26 — что учитывать

- **Liquid Glass** — навбары, таббары, тулбары стеклянные сами по себе. Не красить их фон.
  `.glassEffect()` для своих плавающих элементов; `GlassEffectContainer` для групп.
- `TabView` с `Tab(...)` API (iOS 18+), `.tabBarMinimizeBehavior(.onScrollDown)` (iOS 26).
- `NavigationStack`, не `NavigationView`. `.navigationTitle` + `.navigationSubtitle` (iOS 26).
- `.searchable` — в тулбаре, системная; на iOS 26 может уезжать вниз сама. Не делать свою.
- `@Observable` вместо `ObservableObject`. `@State` для владения, `@Bindable` для привязки.
- `ContentUnavailableView.search` для пустого поиска.
- `.contentTransition(.numericText())` для меняющихся чисел.
- Symbols: только `Image(systemName:)`, SF Symbols 7; `.symbolEffect` для анимаций.
- Deployment target проекта — **iOS 18.0**; iOS 26-only API оборачивать в `if #available(iOS 26, *)`.

## Как проверить API в локальном SDK

Не гадать — grep по swiftinterface:

```bash
SDK=$(xcrun --sdk iphoneos --show-sdk-path)
grep -n "func glassEffect" "$SDK/System/Library/Frameworks/SwiftUI.framework/Modules/SwiftUI.swiftmodule/arm64-apple-ios.swiftinterface" | head
```
Там же видна `@available` — по ней решать, нужен ли `#available`.

## Чек-лист ревью любой вью

- [ ] Нет `.font(.system(size:` и нет `design: .rounded`
- [ ] Нет литералов цвета; всё через `Tokens.Color`
- [ ] Список — `List`, форма — `Form`, навигация — `NavigationStack`
- [ ] Работает в Dark Mode и при Dynamic Type xxxLarge (проверить в Preview)
- [ ] Числа — `.monospacedDigit()`
- [ ] Кастомная вью существует только потому, что системной нет — и это написано в комментарии
