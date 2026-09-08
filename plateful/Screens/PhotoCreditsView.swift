import SwiftUI

/// Авторы фотографий и логотипов.
///
/// Лицензии CC BY и CC BY-SA требуют указать автора — это не вежливость,
/// а условие использования. Снимки под CC0 и в общественном достоянии
/// в списке не нужны и его не засоряют.
struct PhotoCreditsView: View {

    @Environment(MenuRepository.self) private var menu
    @State private var credits: [Credit] = []

    struct Credit: Decodable, Identifiable, Sendable {
        init(subject: String, title: String?, creator: String?,
             license: String?, page: String?) {
            self.subject = subject
            self.title = title
            self.creator = creator
            self.license = license
            self.page = page
        }

        let subject: String
        let title: String?
        let creator: String?
        let license: String?
        let page: String?

        var id: String { subject }
        var url: URL? { page.flatMap(URL.init(string:)) }
    }

    var body: some View {
        List {
            Section {
                ForEach(credits) { credit in
                    row(credit)
                }
            } header: {
                Text("\(credits.count) images")
            } footer: {
                Text("Photographs and logos used under Creative Commons licences. Images in the public domain or under CC0 are not listed, as they require no credit.")
            }
        }
        .navigationTitle("Image credits")
        .navigationBarTitleDisplayMode(.inline)
        .task { credits = Self.load() + Self.fromCatalog(menu.catalog) }
    }

    @ViewBuilder
    private func row(_ credit: Credit) -> some View {
        let content = VStack(alignment: .leading, spacing: Tokens.Spacing.xs) {
            Text(credit.subject)
                .font(.subheadline)
            if let title = credit.title {
                Text(title)
                    .font(.caption)
                    .foregroundStyle(Tokens.Color.textSecondary)
            }
            Text([credit.creator, credit.license].compactMap { $0 }.joined(separator: " · "))
                .font(.caption)
                .foregroundStyle(Tokens.Color.textSecondary)
        }

        if let url = credit.url {
            Link(destination: url) { content }
        } else {
            content
        }
    }

    /// Снимки конкретных блюд приезжают в паке, а не лежат в бандле,
    /// поэтому их авторы собираются из каталога на лету.
    private static func fromCatalog(_ catalog: MenuCatalog?) -> [Credit] {
        guard let catalog else { return [] }
        var seen = Set<URL>()
        return catalog.items.compactMap { item -> Credit? in
            guard let photo = item.photo, seen.insert(photo.url).inserted else { return nil }
            return Credit(subject: "\(item.chain): \(item.name)",
                          title: photo.title, creator: photo.creator,
                          license: photo.license, page: photo.page?.absoluteString)
        }
    }

    private static func load() -> [Credit] {
        guard let url = Bundle.main.url(forResource: "photo-credits", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let credits = try? JSONDecoder().decode([Credit].self, from: data)
        else { return [] }
        return credits
    }
}

#Preview {
    NavigationStack { PhotoCreditsView() }
}
