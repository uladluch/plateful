import SwiftUI

/// Управление фильтром в тулбаре.
///
/// Системное `Menu` с `Picker` внутри, а не своя панель: так фильтр не
/// занимает место на экране, где важнее сами блюда.
struct MenuFilterMenu: View {

    @Binding var filter: MenuFilter
    let goals: UserGoals?

    var body: some View {
        Menu {
            Picker("Sort", selection: $filter.sort) {
                ForEach(MenuSort.allCases) { sort in
                    Text(sort.title).tag(sort)
                }
            }
            .pickerStyle(.inline)

            if let goals, !goals.isEmpty {
                Section("Your goals") {
                    Toggle(isOn: goalsApplied) {
                        Label(goalsSummary(goals), systemImage: "target")
                    }
                }
            }

            if filter.isActive {
                Section {
                    Button("Clear filter", systemImage: "xmark") { filter = .none }
                }
            }
        } label: {
            Label("Filter", systemImage: filter.isActive
                  ? "line.3.horizontal.decrease.circle.fill"
                  : "line.3.horizontal.decrease.circle")
        }
    }

    /// Цели применяются целиком: две отдельные галочки для потолка и минимума
    /// дробят одно решение «фильтровать по моим целям» на два.
    private var goalsApplied: Binding<Bool> {
        Binding(
            get: { filter.isNarrowing },
            set: { isOn in
                filter.maxCalories = isOn ? goals?.calorieCeiling : nil
                filter.minProtein = isOn ? goals?.proteinFloor : nil
            })
    }

    private func goalsSummary(_ goals: UserGoals) -> String {
        [goals.calorieCeiling.map { "under \($0) cal" },
         goals.proteinFloor.map { "\($0)g+ protein" }]
            .compactMap { $0 }
            .joined(separator: ", ")
    }
}
