import SwiftUI

/// Аналитика — пока пустая вкладка, экран без содержимого.
struct AnalyticsView: View {
    var body: some View {
        NavigationStack {
            ContentUnavailableView(
                "Analytics",
                systemImage: "chart.bar",
                description: Text("Coming soon."))
                .navigationTitle("Analytics")
                .navigationBarTitleDisplayMode(.inline)
        }
    }
}

#Preview {
    AnalyticsView()
}
