import { createServer, type Server } from "node:http";
import { createClient, TimeoutError } from "@kevincii/http-query-client";

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
  server.closeAllConnections();
  return new Promise((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

const delayMs = 2000;
const timeoutMs = 50;
const abortAfterMs = 50;
const methods: string[] = [];
const server = createServer((request, response) => {
  methods.push(request.method ?? "");
  const timer = setTimeout(() => {
    if (!response.destroyed) {
      response.writeHead(200, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ ok: true }));
    }
  }, delayMs);
  response.on("close", () => clearTimeout(timer));
});

const baseUrl = await listen(server);
const client = createClient({ baseUrl });

const timeoutMethodStart = methods.length;
const timeoutStarted = Date.now();
let timeoutError: { name: string; typed: boolean; message: string } | null = null;
try {
  await client.query("/slow", { probe: "timeout" }, { timeout: timeoutMs });
} catch (error) {
  timeoutError = {
    name: error instanceof Error ? error.name : typeof error,
    typed: error instanceof TimeoutError,
    message: error instanceof Error ? error.message : String(error),
  };
}
const timeoutElapsedMs = Date.now() - timeoutStarted;
const timeoutRequestMethods = methods.slice(timeoutMethodStart);

const controller = new AbortController();
const abortTimer = setTimeout(() => controller.abort(), abortAfterMs);
const abortMethodStart = methods.length;
const abortStarted = Date.now();
let abortError: {
  name: string;
  constructorName: string;
  message: string;
} | null = null;
try {
  await client.query(
    "/slow",
    { probe: "external-abort" },
    { signal: controller.signal },
  );
} catch (error) {
  abortError = {
    name: error instanceof Error ? error.name : typeof error,
    constructorName:
      typeof error === "object" && error !== null
        ? error.constructor.name
        : typeof error,
    message: error instanceof Error ? error.message : String(error),
  };
}
clearTimeout(abortTimer);
const abortElapsedMs = Date.now() - abortStarted;
const abortRequestMethods = methods.slice(abortMethodStart);
await close(server);

console.log(
  `INTEROP_RESULT=${JSON.stringify({
    delayMs,
    timeout: {
      configuredMs: timeoutMs,
      elapsedMs: timeoutElapsedMs,
      error: timeoutError,
      requestMethods: timeoutRequestMethods,
    },
    externalAbort: {
      configuredMs: abortAfterMs,
      elapsedMs: abortElapsedMs,
      signalAborted: controller.signal.aborted,
      error: abortError,
      requestMethods: abortRequestMethods,
    },
  })}`,
);
