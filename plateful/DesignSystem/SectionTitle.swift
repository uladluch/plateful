import SwiftUI

/// Заголовок секции — единый на всё приложение.
///
/// Headline 3, жирным, основным цветом текста — вместо мелкого системного
/// header капсом вторичным цветом. Разделы здесь несут вес заголовка блюда
/// или категории, а не служебную подпись над списком, и должны читаться
/// одной системой везде: на карточках сети, на меню, на «рядом», на
/// сохранённом.
///
/// Единственное место, где называется стиль заголовка секции — менять
/// внешний вид у всех сразу значит менять этот файл, а не выискивать
/// текст по экранам.
struct SectionTitle: View {

    let title: String

    init(_ title: String) {
        self.title = title
    }

    var body: some View {
        Text(title)
            .font(.title3)
            .fontWeight(.bold)
            .foregroundStyle(Tokens.Color.textPrimary)
            // Отменяет капс, который List иначе накладывает на header
            // сам — без него заголовок читался бы «PROTEIN», а не «Protein».
            .textCase(nil)
    }
}

#Preview {
    List {
        Section {
            Text("Row")
        } header: {
            SectionTitle("Section title")
        }
    }
}
