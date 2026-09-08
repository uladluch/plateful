import SwiftUI

/// Снятые с меню позиции — отдельным экраном, старым списком строк.
///
/// Не карточками: здесь важна не витрина, а честное объяснение под списком —
/// что эти блюда стояли в меню на момент записи, а сеть их больше не подаёт.
struct ArchiveMenuView: View {

    let chain: MenuChain
    let items: [MenuItem]

    @Environment(MenuRepository.self) private var menu

    var body: some View {
        List {
            Section {
                ForEach(items) { item in
                    NavigationLink(value: item) {
                        MenuItemRow(item: item, showsChain: false,
                                    variants: menu.variants(of: item))
                    }
                }
            } footer: {
                Text("These were on the menu when the data was collected. \(chain.name) does not list them today.")
            }
        }
        .navigationTitle("Archive")
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    NavigationStack {
        ArchiveMenuView(
            chain: MenuChain(name: "McDonald's", itemCount: 1),
            items: [MenuRepository.previewItem(name: "Big Mac")])
    }
    .environment(MenuRepository.preview)
}
