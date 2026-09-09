import SwiftData
import SwiftUI

/// Цели человека. Пока это весь «профиль»: аккаунта нет и не планируется,
/// всё лежит на устройстве и уезжает в iCloud вместе с остальными данными.
struct ProfileView: View {

    @Environment(\.modelContext) private var context
    @Query private var stored: [UserGoals]

    @State private var calorieCeiling: Int?
    @State private var proteinFloor: Int?

    /// Шаги подобраны под то, как люди думают о еде: сотня калорий и пять
    /// граммов белка — различимые величины, единица — нет.
    private static let calorieOptions = stride(from: 200, through: 1500, by: 100).map { $0 }
    private static let proteinOptions = stride(from: 5, through: 80, by: 5).map { $0 }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    goalPicker("Calorie ceiling", selection: $calorieCeiling,
                               options: Self.calorieOptions) { "\($0) cal" }
                    goalPicker("Protein floor", selection: $proteinFloor,
                               options: Self.proteinOptions) { MenuItem.grams(Double($0)) }
                } header: {
                    Text("Goals")
                } footer: {
                    Text("Used to filter menus. Leave them off and nothing is hidden.")
                }

                if goals?.isEmpty == false {
                    Section {
                        Button("Clear goals", role: .destructive) {
                            calorieCeiling = nil
                            proteinFloor = nil
                        }
                    }
                }

                Section {
                    NavigationLink("Image credits") { PhotoCreditsView() }
                }

                Section {
                    LabeledContent("Account", value: "None")
                } footer: {
                    Text("Plateful has no accounts. Your goals, history and saved orders stay on your devices and sync through iCloud.")
                }
            }
            .navigationTitle("Profile")
            .navigationBarTitleDisplayMode(.inline)
            .onAppear(perform: loadGoals)
            .onChange(of: calorieCeiling) { persist() }
            .onChange(of: proteinFloor) { persist() }
        }
    }

    private var goals: UserGoals? { stored.first }

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
        try? UserDataStore(context: context)
            .updateGoals(calorieCeiling: calorieCeiling, proteinFloor: proteinFloor)
    }
}

#Preview {
    ProfileView()
}
