import type { PlatformError } from "@effect/platform/Error";
import * as FetchHttpClient from "@effect/platform/FetchHttpClient";
import * as FileSystem from "@effect/platform/FileSystem";
import * as HttpClient from "@effect/platform/HttpClient";
import type { HttpClientResponse } from "@effect/platform/HttpClientResponse";
import * as Effect from "effect/Effect";
import * as Either from "effect/Either";
import { createHash } from "node:crypto";
import { join } from "node:path";

const responseHeaderNames = [
  "content-type",
  "content-encoding",
  "content-length",
  "date",
  "etag",
  "last-modified",
  "location",
] as const;

type GameSource = "play-by-play" | "boxscore" | "shifts" | "game-summary" | "play-report";

export type CaptureIdentity =
  | { readonly gameId: string; readonly source: GameSource }
  | { readonly seasonId: string; readonly source: "season-summary" | "season-games" | "skater-bios" | "goalie-bios" };

type CaptureMetadata = CaptureIdentity & {
  readonly schemaVersion: 1;
  readonly request: {
    readonly method: "GET";
    readonly url: string;
    readonly requestedAt: string;
  };
  readonly responseHeaders: Partial<Record<(typeof responseHeaderNames)[number], string>>;
};

export type CaptureRecord = CaptureMetadata & (
  | {
      readonly httpStatus: number;
      readonly state: "captured";
      readonly body: {
        readonly path: "body.bin";
        readonly representation: "http-client-body";
        readonly bytes: number;
        readonly sha256: string;
      };
      readonly failure: null;
    }
  | {
      readonly httpStatus: number | null;
      readonly state: "failed";
      readonly body: null;
      readonly failure: {
        readonly kind: "transport" | "body-read" | "timeout";
        readonly message: string;
      };
    }
);

// the caller supplies a ten-digit game id and a nonempty output path.
// creating the destination here owns the no-overwrite check before any request.
export const captureGame = ({
  gameId,
  outDirectory,
}: {
  readonly gameId: string;
  readonly outDirectory: string;
}): Effect.Effect<CaptureRecord[], PlatformError, FileSystem.FileSystem | HttpClient.HttpClient> =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem;
    yield* fs.makeDirectory(outDirectory);

    const seasonStart = gameId.slice(0, 4);
    const season = `${seasonStart}${Number(seasonStart) + 1}`;
    const sources = [
      { source: "play-by-play", url: `https://api-web.nhle.com/v1/gamecenter/${gameId}/play-by-play` },
      { source: "boxscore", url: `https://api-web.nhle.com/v1/gamecenter/${gameId}/boxscore` },
      { source: "shifts", url: `https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId%3D${gameId}&limit=-1` },
      { source: "game-summary", url: `https://www.nhl.com/scores/htmlreports/${season}/GS${gameId.slice(-6)}.HTM` },
      { source: "play-report", url: `https://www.nhl.com/scores/htmlreports/${season}/PL${gameId.slice(-6)}.HTM` },
    ] as const;
    const records: CaptureRecord[] = [];

    for (const { source, url } of sources) {
      records.push(yield* captureResponse({ identity: { gameId, source }, url, outDirectory }));
    }
    return records;
  });

// callers own the new output directory; each response owns its source directory.
export const captureResponse = ({ identity, url, outDirectory }: {
  readonly identity: CaptureIdentity;
  readonly url: string;
  readonly outDirectory: string;
}): Effect.Effect<CaptureRecord, PlatformError, FileSystem.FileSystem | HttpClient.HttpClient> =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem;
    const client = yield* HttpClient.HttpClient;
    const sourceDirectory = join(outDirectory, identity.source);
    yield* fs.makeDirectory(sourceDirectory);
    const request = { method: "GET", url, requestedAt: new Date().toISOString() } as const;
    let response: HttpClientResponse | undefined;
    const result = yield* Effect.gen(function* () {
      response = yield* client.get(url, {
        headers: { "user-agent": "hockey-stats/0.1 (personal hockey statistics; source capture)" },
      });
      const bytes = new Uint8Array(yield* response.arrayBuffer);
      return { response, bytes };
    }).pipe(
      Effect.provideService(FetchHttpClient.RequestInit, { redirect: "manual" }),
      Effect.timeout("30 seconds"),
      Effect.either,
    );

    const responseHeaders: CaptureMetadata["responseHeaders"] = {};
    if (response !== undefined) {
      for (const name of responseHeaderNames) {
        const value = response.headers[name];
        if (value !== undefined) responseHeaders[name] = value;
      }
    }
    const metadata: CaptureMetadata = { schemaVersion: 1, ...identity, request, responseHeaders };
    let record: CaptureRecord;
    if (Either.isRight(result)) {
      const { response: completeResponse, bytes } = result.right;
      yield* fs.writeFile(join(sourceDirectory, "body.bin"), bytes);
      record = {
        ...metadata,
        httpStatus: completeResponse.status,
        state: "captured",
        body: {
          path: "body.bin",
          representation: "http-client-body",
          bytes: bytes.byteLength,
          sha256: createHash("sha256").update(bytes).digest("hex"),
        },
        failure: null,
      };
    } else {
      const error = result.left;
      const kind = error._tag === "TimeoutException"
        ? "timeout"
        : error._tag === "ResponseError" ? "body-read" : "transport";
      const message = error._tag === "TimeoutException"
        ? "request and body read exceeded 30 seconds"
        : error.cause instanceof Error ? error.cause.message : error.message;
      record = {
        ...metadata,
        httpStatus: response?.status ?? null,
        state: "failed",
        body: null,
        failure: { kind, message },
      };
    }
    yield* fs.writeFileString(join(sourceDirectory, "capture.json"), `${JSON.stringify(record, null, 2)}\n`);
    return record;
  });
