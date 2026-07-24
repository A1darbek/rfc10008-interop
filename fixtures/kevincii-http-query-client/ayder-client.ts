import { createClient, HttpError } from "@kevincii/http-query-client";

type QueryDocument = {
  source: {
    topic: string;
    partition: number;
    from_offset: number;
    to_offset: number;
    limit: number;
    sealed_only: boolean;
  };
  filter: Array<{ field: string; op: string; value: string | boolean }>;
  include: { metadata: boolean; commit_status_for_group: string };
  transform: { left_fields: string[] };
  explain: boolean;
};

type TraceItem = {
  phase: "request" | "response";
  method?: string;
  url?: string;
  contentType?: string | null;
  ifNoneMatch?: string | null;
  body?: unknown;
  status?: number;
  acceptQuery?: string | null;
  etag?: string | null;
};

const baseUrl = process.env.AYDER_URL;
if (!baseUrl) throw new Error("AYDER_URL is required");

const authorization = `Bearer ${process.env.AYDER_TOKEN ?? "dev"}`;
const topic = "kevincii-query-client";
const group = "kevincii-query-client";

const queryDocument: QueryDocument = {
  source: {
    topic,
    partition: 0,
    from_offset: 0,
    to_offset: 3,
    limit: 10,
    sealed_only: true,
  },
  filter: [
    { field: "provider_commitment", op: "eq", value: "UNKNOWN" },
    { field: "safe_to_close", op: "eq", value: false },
  ],
  include: {
    metadata: true,
    commit_status_for_group: group,
  },
  transform: {
    left_fields: [
      "event_id",
      "payment_id",
      "provider_order_id",
      "provider_commitment",
      "safe_to_close",
      "manual_reconciliation_required",
    ],
  },
  explain: true,
};

function headerValue(headers: RequestInit["headers"], name: string): string | null {
  return new Headers(headers).get(name);
}

function parsedBody(body: unknown): unknown {
  if (typeof body !== "string" || body.length === 0) return null;
  return JSON.parse(body);
}

async function requireOk(response: Response, label: string): Promise<void> {
  if (!response.ok) {
    throw new Error(`${label} failed with HTTP ${response.status}: ${await response.text()}`);
  }
}

async function seedAyder(): Promise<void> {
  const jsonHeaders = {
    Authorization: authorization,
    "Content-Type": "application/json",
  };
  await requireOk(
    await fetch(`${baseUrl}/broker/topics`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ name: topic, partitions: 1 }),
    }),
    "create topic",
  );

  const events = [
    {
      event_id: "pay_evt_001",
      payment_id: "pay_001",
      provider_order_id: "po_001",
      provider_commitment: "UNKNOWN",
      safe_to_close: false,
      manual_reconciliation_required: true,
    },
    {
      event_id: "pay_evt_002",
      payment_id: "pay_002",
      provider_order_id: "po_002",
      provider_commitment: "SUCCESS",
      safe_to_close: true,
      manual_reconciliation_required: false,
    },
    {
      event_id: "pay_evt_003",
      payment_id: "pay_003",
      provider_order_id: "po_003",
      provider_commitment: "UNKNOWN",
      safe_to_close: false,
      manual_reconciliation_required: true,
    },
  ];
  await requireOk(
    await fetch(
      `${baseUrl}/broker/topics/${topic}/produce-ndjson?partition=0&timeout_ms=5000&idempotency_key=kevincii_initial`,
      {
        method: "POST",
        headers: {
          Authorization: authorization,
          "Content-Type": "application/x-ndjson",
        },
        body: `${events.map((event) => JSON.stringify(event)).join("\n")}\n`,
      },
    ),
    "produce events",
  );
  await requireOk(
    await fetch(`${baseUrl}/broker/commit`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ topic, group, partition: 0, offset: 0 }),
    }),
    "commit baseline",
  );
}

await seedAyder();

const trace: TraceItem[] = [];
const client = createClient({
  baseUrl,
  fallback: null,
  headers: { Authorization: authorization },
});

client.middleware.useBefore((request) => {
  trace.push({
    phase: "request",
    method: request.method,
    url: request.url,
    contentType: headerValue(request.headers, "content-type"),
    ifNoneMatch: headerValue(request.headers, "if-none-match"),
    body: parsedBody(request.body),
  });
  return request;
});

client.middleware.useAfter((response) => {
  trace.push({
    phase: "response",
    status: response.status,
    acceptQuery: response.headers.get("accept-query"),
    etag: response.headers.get("etag"),
  });
  return response;
});

const nativeStart = trace.length;
const nativeResult = await client.query<Record<string, unknown>, QueryDocument>(
  "/broker/query",
  queryDocument,
);
const nativeTrace = trace.slice(nativeStart);
const responseEvidence = nativeTrace.find((item) => item.phase === "response");
const etag = responseEvidence?.etag ?? null;

const conditionalStart = trace.length;
let conditionalError: {
  name: string;
  httpError: boolean;
  status: number | null;
} | null = null;
try {
  if (!etag) throw new Error("native response did not expose ETag");
  await client.query<Record<string, unknown>, QueryDocument>(
    "/broker/query",
    queryDocument,
    { headers: { "If-None-Match": etag } },
  );
} catch (error) {
  conditionalError = {
    name: error instanceof Error ? error.name : typeof error,
    httpError: error instanceof HttpError,
    status: error instanceof HttpError ? error.status : null,
  };
}
const conditionalTrace = trace.slice(conditionalStart);

console.log(
  `INTEROP_RESULT=${JSON.stringify({
    configuredBody: queryDocument,
    native: {
      trace: nativeTrace,
      requestMethods: nativeTrace
        .filter((item) => item.phase === "request")
        .map((item) => item.method),
      responseParsedAsJsonObject:
        typeof nativeResult === "object" && nativeResult !== null && !Array.isArray(nativeResult),
      responseHasRows: Array.isArray(nativeResult.rows),
      responseRowCount: Array.isArray(nativeResult.rows) ? nativeResult.rows.length : null,
      acceptQuery: responseEvidence?.acceptQuery ?? null,
      etag,
    },
    conditional: {
      trace: conditionalTrace,
      wireStatus:
        conditionalTrace.find((item) => item.phase === "response")?.status ?? null,
      requestIfNoneMatch:
        conditionalTrace.find((item) => item.phase === "request")?.ifNoneMatch ?? null,
      error: conditionalError,
    },
  })}`,
);
