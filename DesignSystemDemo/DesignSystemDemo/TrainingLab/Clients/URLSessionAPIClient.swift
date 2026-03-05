import Foundation

struct URLSessionAPIClient: APIClient {
    struct Configuration: Sendable {
        var baseURL: URL
        var apiKey: String

        static let `default` = Configuration(
            baseURL: URL(string: "https://api.training-lab.mauro42k.com")!,
            apiKey: ""
        )
    }

    private let configuration: Configuration
    private let session: URLSession
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    init(configuration: Configuration = .default, session: URLSession = .shared) {
        self.configuration = configuration
        self.session = session

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        self.encoder = encoder

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        self.decoder = decoder
    }

    func ingestWorkouts(idempotencyKey: String, payload: WorkoutIngestDTO) async throws -> IngestResponseDTO {
        var request = try makeRequest(path: "v1/ingest/workouts", method: "POST")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(idempotencyKey, forHTTPHeaderField: "X-Idempotency-Key")

        do {
            request.httpBody = try encoder.encode(payload)
        } catch {
            throw APIClientError.encodingFailed
        }

        let (data, response) = try await session.data(for: request)
        let statusCode = try validate(response: response)

        guard statusCode == 200 else {
            throw APIClientError.unexpectedStatus(statusCode)
        }

        return try decoder.decode(IngestResponseDTO.self, from: data)
    }

    func fetchWorkouts(from: Date, to: Date, sport: SportType?) async throws -> [WorkoutDTO] {
        var components = URLComponents(url: try pathURL("v1/workouts"), resolvingAgainstBaseURL: false)
        var items: [URLQueryItem] = [
            URLQueryItem(name: "from", value: iso8601String(from)),
            URLQueryItem(name: "to", value: iso8601String(to))
        ]
        if let sport {
            items.append(URLQueryItem(name: "sport", value: sport.rawValue))
        }
        components?.queryItems = items

        guard let url = components?.url else {
            throw APIClientError.invalidURL
        }

        let request = try makeRequest(url: url, method: "GET")
        let (data, response) = try await session.data(for: request)
        _ = try validate(response: response)

        return try decoder.decode([WorkoutDTO].self, from: data)
    }

    func fetchDaily(from: Date, to: Date) async throws -> [DailyItemDTO] {
        var components = URLComponents(url: try pathURL("v1/daily"), resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "from", value: iso8601String(from)),
            URLQueryItem(name: "to", value: iso8601String(to))
        ]

        guard let url = components?.url else {
            throw APIClientError.invalidURL
        }

        let request = try makeRequest(url: url, method: "GET")
        let (data, response) = try await session.data(for: request)
        _ = try validate(response: response)

        return try decoder.decode([DailyItemDTO].self, from: data)
    }

    private func makeRequest(path: String, method: String) throws -> URLRequest {
        try makeRequest(url: pathURL(path), method: method)
    }

    private func makeRequest(url: URL, method: String) throws -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue(configuration.apiKey, forHTTPHeaderField: "X-API-KEY")
        return request
    }

    private func pathURL(_ path: String) throws -> URL {
        guard let url = URL(string: path, relativeTo: configuration.baseURL)?.absoluteURL else {
            throw APIClientError.invalidURL
        }
        return url
    }

    private func validate(response: URLResponse) throws -> Int {
        guard let http = response as? HTTPURLResponse else {
            throw APIClientError.unexpectedStatus(-1)
        }

        switch http.statusCode {
        case 200:
            return http.statusCode
        case 401:
            throw APIClientError.unauthorized
        case 409:
            throw APIClientError.conflict
        default:
            throw APIClientError.unexpectedStatus(http.statusCode)
        }
    }

    private func iso8601String(_ date: Date) -> String {
        ISO8601DateFormatter().string(from: date)
    }
}
