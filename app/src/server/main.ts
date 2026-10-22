import * as NodeHttpServer from "@effect/platform-node/NodeHttpServer";
import * as NodeRuntime from "@effect/platform-node/NodeRuntime";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Schema from "effect/Schema";
import * as HttpApiBuilder from "effect/http-api/HttpApiBuilder";
import * as HttpRouter from "effect/http/HttpRouter";
import * as HttpServerResponse from "effect/http/HttpServerResponse";
import { createServer } from "node:http";
import { stat } from "node:fs/promises";
import { resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import * as A from "../shared/player-analysis.js";
import { Publication, publicationLayer } from "./publication.js";

try {
  const { values, tokens } = parseArgs({
    options: {
      publication: { type: "string" },
      port: { type: "string" },
      "api-only": { type: "boolean", default: false },
    },
    tokens: true,
    allowPositionals: false,
  });
  for (const name of ["publication", "port", "api-only"]) {
    if (tokens.filter((token) => token.kind === "option" && token.name === name).length > 1)
      throw new Error(`supply --${name} once`);
  }
  const port = values.port === undefined ? 3000 : Number(values.port);
  if (
    values.publication === undefined ||
    values.publication === "" ||
    (values.port !== undefined && !/^[1-9]\d*$/.test(values.port)) ||
    !Number.isInteger(port) ||
    port < 1 ||
    port > 65535
  )
    throw new Error("use --publication <active.sqlite> [--port <local port>]");
  const filename = resolve(values.publication);
  const assets = fileURLToPath(new URL("../../client/", import.meta.url));
  const program = Effect.gen(function* () {
    const publication = yield* Publication;
    if (!values["api-only"]) {
      yield* Effect.tryPromise(async () => {
        if (!(await stat(resolve(assets, "index.html"))).isFile())
          throw new Error("built index.html is missing; run npm run build");
      });
    }
    const readFailure = (error: unknown) => {
      console.error("publication read failed", error);
      return {
        _tag: "ReadFailure",
        message: "results could not be loaded. please retry.",
      } as const;
    };
    const failure = (error: unknown): A.ApiError => {
      const cause =
        typeof error === "object" &&
        error !== null &&
        "_tag" in error &&
        error._tag === "UnknownError" &&
        "cause" in error
          ? error.cause
          : error;
      if (Schema.is(A.ApiError)(cause)) return cause;
      if (cause instanceof A.SelectionError)
        return {
          _tag: cause.status === 400 ? "InvalidSelection" : "NotFound",
          message: cause.message,
        };
      return readFailure(error);
    };
    const select = <T>(request: { url: string }, parse: (query: URLSearchParams) => T) =>
      Effect.try({
        try: () => parse(new URL(request.url, "http://127.0.0.1").searchParams),
        catch: failure,
      });
    const playerId = (id: string) =>
      Effect.try({
        try: () => {
          if (!Schema.is(A.Id)(id))
            throw { _tag: "InvalidPlayerId", message: "invalid player id" } satisfies A.ApiError;
          return id;
        },
        catch: failure,
      });
    const seasons = publication.seasons.map((row) => row.season);
    const handlers = HttpApiBuilder.group(A.PlayerAnalysisApi, "analysis", (handlers) =>
      handlers
        .handle("league", ({ request }) =>
          Effect.gen(function* () {
            const selection = yield* select(request, (query) =>
              A.parseLeagueSelection(query, seasons),
            );
            return yield* publication.league(selection).pipe(Effect.mapError(failure));
          }),
        )
        .handle("player", ({ params, request }) =>
          Effect.gen(function* () {
            const id = yield* playerId(params.playerId),
              season = yield* select(request, (query) => A.parsePlayerSelection(query, seasons));
            const response = yield* publication.player(season, id).pipe(Effect.mapError(failure));
            if (response === undefined)
              return yield* Effect.fail({
                _tag: "PlayerNotFound",
                message: "player not found in this publication",
              } as const);
            return response;
          }),
        )
        .handle("maps", ({ request }) =>
          Effect.gen(function* () {
            const selection = yield* select(request, (query) =>
              A.parseMapSelection(query, seasons),
            );
            return yield* publication.maps(selection).pipe(Effect.mapError(failure));
          }),
        )
        .handle("evidence", ({ params, request }) =>
          Effect.gen(function* () {
            const id = yield* playerId(params.playerId),
              selection = yield* select(request, (query) =>
                A.parseEvidenceSelection(query, seasons, id),
              );
            return yield* publication.evidence(selection).pipe(Effect.mapError(failure));
          }),
        )
        .handle("context", ({ params, request }) =>
          Effect.gen(function* () {
            const id = yield* playerId(params.playerId),
              selection = yield* select(request, (query) =>
                A.parseContextSelection(query, seasons, id),
              );
            return yield* publication.context(selection).pipe(Effect.mapError(failure));
          }),
        ),
    );
    const api = HttpApiBuilder.layer(A.PlayerAnalysisApi).pipe(Layer.provide(handlers));
    const staticFiles = HttpRouter.add("*", "/*", (request) =>
      Effect.gen(function* () {
        const path = new URL(request.url, "http://127.0.0.1").pathname;
        if (path === "/api" || path.startsWith("/api/"))
          return HttpServerResponse.jsonUnsafe({ message: "api route not found" }, { status: 404 });
        if (values["api-only"] || (request.method !== "GET" && request.method !== "HEAD"))
          return HttpServerResponse.text("not found", { status: 404 });
        let filename: string;
        if (path === "/" || /^\/compare\/?$/.test(path) || /^\/players\/[^/]+\/?$/.test(path))
          filename = resolve(assets, "index.html");
        else if (path.startsWith("/assets/")) {
          const decoded = yield* Effect.try(() => decodeURIComponent(path));
          filename = resolve(assets, `.${decoded}`);
          if (!filename.startsWith(resolve(assets, "assets") + sep))
            return HttpServerResponse.text("not found", { status: 404 });
        } else return HttpServerResponse.text("not found", { status: 404 });
        return yield* HttpServerResponse.file(filename, {
          headers: {
            "cache-control": filename.endsWith(".html")
              ? "no-store"
              : "public, max-age=31536000, immutable",
          },
        }).pipe(
          Effect.catch((error) => {
            if (error.reason._tag === "NotFound")
              return Effect.succeed(HttpServerResponse.text("not found", { status: 404 }));
            console.error("asset read failed", error);
            return Effect.succeed(
              HttpServerResponse.text("page could not be loaded. please retry.", { status: 500 }),
            );
          }),
        );
      }),
    );
    const cachePolicy = HttpRouter.middleware(
      (effect) =>
        effect.pipe(
          Effect.map((response) =>
            response.headers["cache-control"] === undefined
              ? HttpServerResponse.setHeader(response, "cache-control", "no-store")
              : response,
          ),
        ),
      { global: true },
    );
    yield* Layer.launch(
      HttpRouter.serve(Layer.mergeAll(api, staticFiles, cachePolicy)).pipe(
        Layer.provide(NodeHttpServer.layer(createServer, { host: "127.0.0.1", port })),
      ),
    );
  }).pipe(Effect.provide(publicationLayer(filename)));
  NodeRuntime.runMain(program);
} catch (error) {
  console.error("local server arguments failed", error);
  process.exitCode = 1;
}
