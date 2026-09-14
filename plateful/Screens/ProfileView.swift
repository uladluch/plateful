import SwiftData
import SwiftUI

/// Цели человека. Пока это весь «профиль»: аккаунта нет и не планируется,
/// всё лежит на устройстве и уезжает в iCloud вместе с остальными данными.
struct ProfileView: View {

    @Binding var path: [Route]

    @Environment(\.modelContext) private var context
    @Query private var stored: [UserGoals]

    @State private var calorieCeiling: Int?
    @State private var proteinFloor: Int?

    /// Шаги подобраны под то, как люди думают о еде: сотня калорий и пять
    /// граммов белка — различимые величины, единица — нет.
    private static let calorieOptions = stride(from: 200, through: 1500, by: 100).map { $0 }
    private static let proteinOptions = stride(from: 5, through: 80, by: 5).map { $0 }

    var body: some View {
        NavigationStack(path: $path) {
            Form {
                Section {
                    goalPicker("Calorie ceiling", selection: calorieSelection,
                               options: Self.calorieOptions) { "\($0) cal" }
                    goalPicker("Protein floor", selection: proteinSelection,
                               options: Self.proteinOptions) { MenuItem.grams(Double($0)) }
                } header: {
                    SectionTitle("Goals")
                } footer: {
                    Text("Used to filter menus. Leave them off and nothing is hidden.")
                }

                if goals?.isEmpty == false {
                    Section {
                        Button("Clear goals", role: .destructive) {
                            calorieCeiling = nil
                            proteinFloor = nil
                            persist()
                        }
                    }
                }

                Section {
                    NavigationLink("Image credits", value: Route.photoCredits)
                }

                Section {
                    LabeledContent("Account", value: "None")
                } footer: {
                    Text("Plateful has no accounts. Your goals, history and saved orders stay on your devices and sync through iCloud.")
                }
            }
            .navigationTitle("Profile")
            .navigationBarTitleDisplayMode(.inline)
            .routeDestinations()
            // Только чтение: запись идёт по выбору человека, а не на каждое
            // появление экрана — раньше загрузка будила `onChange`, и в
            // SwiftData писалось ровно то, что только что прочитали.
            .task { loadGoals() }
        }
    }

    private var goals: UserGoals? { stored.first }

    /// Цель сохраняется в момент выбора.
    private var calorieSelection: Binding<Int?> {
        Binding(get: { calorieCeiling },
                set: { calorieCeiling = $0; persist() })
    }

    private var proteinSelection: Binding<Int?> {
        Binding(get: { proteinFloor },
                set: { proteinFloor = $0; persist() })
    }

    private func goalPicker(
        _ title: String,
        selection: Binding<Int?>,
        options: [Int],
        label: @escaping (Int) -> String
    ) -> some View {
        Picker(title, selection: selection) {
            Text("Off").tag(Int?.none)
            ForEach(options, id: \.self) { value in
                Text(label(value)).tag(Int?.some(value))
            }
        }
    }

    private func loadGoals() {
        guard let goals = try? UserDataStore(context: context).goals() else { return }
        calorieCeiling = goals.calorieCeiling
        proteinFloor = goals.proteinFloor
    }

    private func persist() {
        UserDataStore.attempt("Сохранение целей") {
            try UserDataStore(context: context)
                .updateGoals(calorieCeiling: calorieCeiling, proteinFloor: proteinFloor)
        }
    }
}

#Preview {
    ProfileView(path: .constant([]))
}
