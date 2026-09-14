import SwiftUI

extension View {

    /// Панель, прикреплённая к верху прокручиваемого экрана.
    ///
    /// На iOS 26 — системная `safeAreaBar`: контент уходит под неё с тем же
    /// эффектом края, что под навбар. Раньше такой нет, и панель стоит в
    /// `safeAreaInset` на материале панелей — тоже системном.
    @ViewBuilder
    func topBar<Bar: View>(@ViewBuilder _ bar: () -> Bar) -> some View {
        if #available(iOS 26, *) {
            safeAreaBar(edge: .top) { bar() }
        } else {
            safeAreaInset(edge: .top, spacing: 0) {
                bar().background(.bar)
            }
        }
    }
}
