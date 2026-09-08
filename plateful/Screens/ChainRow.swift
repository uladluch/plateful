import SwiftUI

/// Строка сети: марка, название, сколько позиций.
///
/// Отдельным типом, потому что сеть перечисляют два экрана — список
/// «Ресторанов» и результаты поиска, — и выглядеть она обязана одинаково.
struct ChainRow: View {

    let chain: MenuChain

    var body: some View {
        LabeledContent {
            Text(chain.itemCount.formatted())
                .monospacedDigit()
        } label: {
            Label {
                Text(chain.name)
            } icon: {
                ChainMarkView(chain: chain.name)
            }
        }
    }
}

#Preview {
    List {
        ChainRow(chain: MenuChain(name: "Chick-Fil-A", itemCount: 101))
    }
}
