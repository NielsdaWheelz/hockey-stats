import * as NodeFileSystem from "@effect/platform-node/NodeFileSystem";
import * as FetchHttpClient from "effect/http/FetchHttpClient";
import * as Effect from "effect/Effect";
import { parseArgs } from "node:util";
import { reportCaptureFailure } from "./capture-report.js";
import { captureSkating, type SkatingSelection } from "./skating-capture.js";

const usage = "use --source detail --season <20232024|20242025|20252026> --player <positive digit id> --out <new directory>; listing requires --season and no --player; glossary requires neither";

try {
  if (process.argv.slice(2).length === 1 && process.argv[2] === "--help") {
    console.log(usage);
  } else {
    const { values, tokens } = parseArgs({
      options: { source: { type: "string" }, season: { type: "string" }, player: { type: "string" }, out: { type: "string" } },
      tokens: true,
      allowPositionals: false,
    });
    const { source, season: seasonId, player: playerId, out: outDirectory } = values;
    if (
      outDirectory === undefined || outDirectory.trim().length === 0 ||
      tokens.some((token, index) => token.kind === "option" &&
        tokens.some((other, otherIndex) => otherIndex < index && other.kind === "option" && other.name === token.name)) ||
      (source !== "detail" && source !== "listing" && source !== "glossary") ||
      (source === "glossary" ? seasonId !== undefined :
        seasonId !== "20232024" && seasonId !== "20242025" && seasonId !== "20252026") ||
      (source === "detail" ? playerId === undefined || !/^\d*[1-9]\d*$/.test(playerId) : playerId !== undefined)
    ) {
      throw new Error("invalid skating capture arguments");
    }

    const selection: SkatingSelection = source === "detail"
      ? { source, seasonId: seasonId!, playerId: playerId! }
      : source === "listing" ? { source, seasonId: seasonId! } : { source };
    await Effect.runPromise(captureSkating(selection, outDirectory).pipe(
      Effect.provide(NodeFileSystem.layer),
      Effect.provide(FetchHttpClient.layer),
      Effect.match({
        onFailure: (error) => {
          process.exitCode = reportCaptureFailure(error, outDirectory);
        },
        onSuccess: (record) => {
          if (record.state === "failed") {
            console.log(`skating ${source} capture incomplete: ${record.failure.kind}, http ${record.httpStatus ?? "unavailable"}; ${record.failure.message}; no complete body saved`);
          } else {
            console.log(`captured skating ${source}: http ${record.httpStatus}, ${record.body.bytes} bytes; original response body preserved`);
          }
          console.log("usable sample: unverified; population: unestablished; capture alone establishes neither measurement validity nor a complete population");
          console.log(outDirectory);
          process.exitCode = record.state === "captured" && record.httpStatus >= 200 && record.httpStatus < 300 ? 0 : 1;
        },
      }),
    ));
  }
} catch {
  console.error(`skating capture failed: ${usage}; check the arguments and runtime`);
  process.exitCode = 1;
}
