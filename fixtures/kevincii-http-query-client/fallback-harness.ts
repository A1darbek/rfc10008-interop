import { createServer, type IncomingMessage, type Server } from "node:http";
import { createClient } from "@kevincii/http-query-client";

type Mode = "native" | "post" | "get";
type QueryDocument = {
  stream: string;
  limit: number;
  filter: { active: boolean };
  tags: string[];
};
type RequestEvidence = {
  method: string;
  url: string;
  body: unknown;
  rawBody: string;
};

const queryDocument: QueryDocument = {
  stream: "events",
  limit: 10,
  filter: { active: true },
  tags: ["priority", "audit"],
};

function listen(server: Server): Promise<string> {
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      if (!address || typeof address === "string") throw new Error("missing server port");
      resolve(`http://127.0.0.1:${address.port}`);
    });
  });
}

function close(server: Server): Promise<void> {
  return new Promise((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

async function runMode(mode: Mode): Promise<{
  mode: Mode;
  trace: RequestEvidence[];
  result: unknown;
}> {
  const trace: RequestEvidence[] = [];
  const server = createServer((request: IncomingMessage, response) => {
    const chunks: Buffer[] = [];
    request.on("data", (chunk: Buffer) => chunks.push(chunk));
    request.on("end", () => {
      const rawBody = Buffer.concat(chunks).toString("utf8");
      let body: unknown = null;
      if (rawBody) body = JSON.parse(rawBody);
      trace.push({
        method: request.method ?? "",
        url: request.url ?? "",
        body,
        rawBody,
      });

      const rejected =
        (mode === "post" && request.method === "QUERY") ||
        (mode === "get" && (request.method === "QUERY" || request.method === "POST"));
      if (rejected) {
        response.writeHead(405, {
          "Content-Type": "application/json",
          Allow: mode === "post" ? "POST, GET" : "GET",
        });
        response.end(JSON.stringify({ error: "method not supported" }));
        return;
      }

      response.writeHead(200, { "Content-Type": "application/json" });
      response.end(
        JSON.stringify({
          servedBy: request.method,
          url: request.url,
          body,
        }),
      );
    });
  });

  const baseUrl = await listen(server);
  const client = createClient({ baseUrl, fallback: "POST" });
  try {
    const result = await client.query<Record<string, unknown>, QueryDocument>(
      "/search",
      queryDocument,
    );
    return { mode, trace, result };
  } finally {
    await close(server);
  }
}

const native = await runMode("native");
const post = await runMode("post");
const get = await runMode("get");

console.log(
  `INTEROP_RESULT=${JSON.stringify({
    configuredBody: queryDocument,
    native,
    post,
    get,
  })}`,
);
