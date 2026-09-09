import Foundation

/// Откуда приложение берёт заведения. Подменяется в тестах, чтобы не
/// ходить в сеть, — как и транспорт паков.
nonisolated protocol VenueTransport: Sendable {
    func venues(latitude: Double, longitude: Double,
                radius: Double, chains: [String]) async throws -> [Venue]
}

/// Точки из нашей базы — единственный запрос, который приложение задаёт
/// Postgres напрямую.
///
/// Пак так возить нельзя: одиннадцать тысяч адресов не влезут в бандл, а
/// часы работы меняются чаще, чем выходит релиз. Поэтому здесь живой
/// запрос, и он же — единственная дверь к таблице: наружу открыта только
/// функция `venues_near`, сама таблица под RLS без политик.
///
/// Ключ публикуемый (`sb_publishable_…`), он и предназначен для клиента.
/// Служебного ключа в приложении нет и быть не может.
nonisolated struct SupabaseVenues: VenueTransport {

    static let endpoint = URL(
        string: "https://tnlmtyhuuqpjwuhzximh.supabase.co/rest/v1/rpc/venues_near")!
    static let key = "sb_publishable_WN4IWJmY2vZil6g6sQXwDg_bzhmremI"

    enum ServiceError: Error, LocalizedError, Sendable {
        case badResponse(Int)

        var errorDescription: String? {
            switch self {
            case .badResponse(let code): "Сервер ответил \(code)"
            }
        }
    }

    private struct Request: Encodable {
        let lat: Double
        let lng: Double
        let radius_m: Double
        let only_chains: [String]?
        let max_results: Int
    }

    let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func venues(latitude: Double, longitude: Double,
                radius: Double, chains: [String]) async throws -> [Venue] {
        var request = URLRequest(url: Self.endpoint)
        request.httpMethod = "POST"
        request.setValue(Self.key, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(Self.key)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 12
        // Пустой список означал бы «сети не важны» и вернул бы чужие
        // булавки; сети без каталога у нас не бывает, но `nil` честнее.
        request.httpBody = try JSONEncoder().encode(
            Request(lat: latitude, lng: longitude, radius_m: radius,
                    only_chains: chains.isEmpty ? nil : chains,
                    max_results: 60))

        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse,
           !(200..<300).contains(http.statusCode) {
            throw ServiceError.badResponse(http.statusCode)
        }
        return try JSONDecoder().decode([Venue].self, from: data)
    }
}
