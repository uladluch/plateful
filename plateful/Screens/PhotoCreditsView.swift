import SwiftUI

/// Авторы фотографий и логотипов.
///
/// Лицензии CC BY и CC BY-SA требуют указать автора — это не вежливость,
/// а условие использования. Снимки под CC0 и в общественном достоянии
/// в списке не нужны и его не засоряют.
struct PhotoCreditsView: View {

    @State private var credits: [Credit] = []

    struct Credit: Decodable, Identifiable, Sendable {
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
        .task { credits = Self.load() }
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
