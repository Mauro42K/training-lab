import Foundation
import OSLog

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
    #if DEBUG
    private let networkLogger = Logger(subsystem: "com.traininglab.designsystemdemo", category: "network")
    #endif
    private static let internetDateTimeFormatter = ISO8601DateFormatter()
    private static let internetDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .iso8601)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        // Date-only payloads represent calendar days; decode using local time
        // to avoid shifting the day when rendering/aggregating in the UI.
        formatter.timeZone = TimeZone.autoupdatingCurrent
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()

    init(configuration: Configuration = .default, session: URLSession = .shared) {
        self.configuration = configuration
        self.session = session

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        self.encoder = encoder

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let raw = try container.decode(String.self)
            if let dateTime = URLSessionAPIClient.internetDateTimeFormatter.date(from: raw) {
                return dateTime
            }
            if let dateOnly = URLSessionAPIClient.internetDateFormatter.date(from: raw) {
                return dateOnly
            }
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Unsupported date format: \(raw)"
            )
        }
        self.decoder = decoder
    }

    func ingestWorkouts(idempotencyKey: String, payload: WorkoutIngestDTO) async throws -> IngestResponseDTO {
        try await ingestPayload(
            path: "v1/ingest/workouts",
            idempotencyKey: idempotencyKey,
            payload: payload,
            logLabel: "ingest_workouts",
            itemCount: payload.workouts.count
        )
    }

    func ingestSleepSessions(idempotencyKey: String, payload: SleepSessionsIngestDTO) async throws -> IngestResponseDTO {
        try await ingestPayload(
            path: "v1/ingest/sleep",
            idempotencyKey: idempotencyKey,
            payload: payload,
            logLabel: "ingest_sleep",
            itemCount: payload.sleepSessions.count
        )
    }

    func ingestRecoverySignals(idempotencyKey: String, payload: RecoverySignalsIngestDTO) async throws -> IngestResponseDTO {
        try await ingestPayload(
            path: "v1/ingest/recovery-signals",
            idempotencyKey: idempotencyKey,
            payload: payload,
            logLabel: "ingest_recovery",
            itemCount: payload.recoverySignals.count
        )
    }

    private func ingestPayload<Payload: Encodable>(
        path: String,
        idempotencyKey: String,
        payload: Payload,
        logLabel: String,
        itemCount: Int
    ) async throws -> IngestResponseDTO {
        var request = try makeRequest(path: path, method: "POST")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(idempotencyKey, forHTTPHeaderField: "X-Idempotency-Key")

        do {
            request.httpBody = try encoder.encode(payload)
        } catch {
            throw APIClientError.encodingFailed
        }

        #if DEBUG
        networkLogger.log("\(logLabel, privacy: .public) request start url=\(request.url?.absoluteString ?? "nil", privacy: .public) items=\(itemCount)")
        #endif
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            #if DEBUG
            networkLogger.error("\(logLabel, privacy: .public) transport_failed error=\(error.localizedDescription, privacy: .public)")
            #endif
            throw error
        }
        let statusCode = try validate(response: response, data: data)
        #if DEBUG
        networkLogger.log("\(logLabel, privacy: .public) request success status=\(statusCode)")
        #endif

        guard statusCode == 200 else {
            throw APIClientError.unexpectedStatus(statusCode)
        }

        do {
            return try decoder.decode(IngestResponseDTO.self, from: data)
        } catch {
            #if DEBUG
            networkLogger.error(
                "\(logLabel, privacy: .public) decode_failed error=\(error.localizedDescription, privacy: .public) body=\(summarizedResponseBody(from: data), privacy: .public)"
            )
            #endif
            throw error
        }
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

        return try decoder.decode(WorkoutsSummaryDTO.self, from: data).items
    }

    func fetchDaily(from: Date, to: Date) async throws -> [DailyItemDTO] {
        var components = URLComponents(url: try pathURL("v1/daily"), resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "from", value: dateOnlyString(from)),
            URLQueryItem(name: "to", value: dateOnlyString(to))
        ]

        guard let url = components?.url else {
            throw APIClientError.invalidURL
        }

        let request = try makeRequest(url: url, method: "GET")
        #if DEBUG
        networkLogger.log("daily request start url=\(url.absoluteString, privacy: .public)")
        #endif
        let (data, response) = try await session.data(for: request)
        _ = try validate(response: response)

        return try decoder.decode(DailySummaryDTO.self, from: data).items
    }

    func fetchHomeSummary(date: Date) async throws -> HomeSummaryDTO {
        var components = URLComponents(url: try pathURL("v1/home/summary"), resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "date", value: dateOnlyString(date))
        ]

        guard let url = components?.url else {
            throw APIClientError.invalidURL
        }

        let request = try makeRequest(url: url, method: "GET")
        #if DEBUG
        networkLogger.log("home_summary request start url=\(url.absoluteString, privacy: .public)")
        #endif
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            #if DEBUG
            networkLogger.error("home_summary transport_failed error=\(error.localizedDescription, privacy: .public)")
            #endif
            throw error
        }
        let statusCode = try validate(response: response, data: data)
        #if DEBUG
        networkLogger.log("home_summary request success status=\(statusCode)")
        #endif
        do {
            return try decoder.decode(HomeSummaryDTO.self, from: data)
        } catch {
            #if DEBUG
            networkLogger.error(
                "home_summary decode_failed error=\(error.localizedDescription, privacy: .public) body=\(summarizedResponseBody(from: data), privacy: .public)"
            )
            #endif
            throw error
        }
    }

    func fetchTrainingLoad(days: Int, sport: TrainingLoadSportFilter) async throws -> TrainingLoadSummaryDTO {
        var components = URLComponents(url: try pathURL("v1/training-load"), resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "days", value: String(days)),
            URLQueryItem(name: "sport", value: sport.rawValue)
        ]

        guard let url = components?.url else {
            throw APIClientError.invalidURL
        }

        let request = try makeRequest(url: url, method: "GET")
        #if DEBUG
        networkLogger.log("training_load request start url=\(url.absoluteString, privacy: .public)")
        #endif
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            #if DEBUG
            networkLogger.error("training_load transport_failed error=\(error.localizedDescription, privacy: .public)")
            #endif
            throw error
        }
        let statusCode = try validate(response: response, data: data)
        #if DEBUG
        networkLogger.log("training_load request success status=\(statusCode)")
        #endif
        do {
            return try decoder.decode(TrainingLoadSummaryDTO.self, from: data)
        } catch {
            #if DEBUG
            networkLogger.error(
                "training_load decode_failed error=\(error.localizedDescription, privacy: .public) body=\(summarizedResponseBody(from: data), privacy: .public)"
            )
            #endif
            throw error
        }
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

    private func validate(response: URLResponse, data: Data? = nil) throws -> Int {
        guard let http = response as? HTTPURLResponse else {
            throw APIClientError.unexpectedStatus(-1)
        }

        switch http.statusCode {
        case 200:
            return http.statusCode
        case 401:
            #if DEBUG
            networkLogger.error("http status=401 detail=\(summarizedResponseBody(from: data), privacy: .public)")
            #endif
            throw APIClientError.unauthorized
        case 409:
            #if DEBUG
            networkLogger.error("http status=409 detail=\(summarizedResponseBody(from: data), privacy: .public)")
            #endif
            throw APIClientError.conflict
        default:
            #if DEBUG
            networkLogger.error("http status=\(http.statusCode) detail=\(summarizedResponseBody(from: data), privacy: .public)")
            #endif
            throw APIClientError.unexpectedStatus(http.statusCode)
        }
    }

    private func iso8601String(_ date: Date) -> String {
        ISO8601DateFormatter().string(from: date)
    }

    private func dateOnlyString(_ date: Date) -> String {
        URLSessionAPIClient.internetDateFormatter.string(from: date)
    }

    #if DEBUG
    private func summarizedResponseBody(from data: Data?) -> String {
        guard let data, !data.isEmpty else {
            return "none"
        }

        if
            let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let detail = object["detail"]
        {
            return String(describing: detail)
        }

        let raw = String(data: data, encoding: .utf8) ?? "non-utf8-body"
        return String(raw.prefix(200))
    }
    #endif
}
