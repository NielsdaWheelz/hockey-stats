import * as NodeFileSystem from "@effect/platform-node/NodeFileSystem";
import * as FetchHttpClient from "@effect/platform/FetchHttpClient";
import * as Effect from "effect/Effect";
import { parseArgs } from "node:util";
import { captureSeason } from "./capture-season.js";
import { reportCaptureFailure, reportCaptures } from "./capture-report.js";

try {
  if (process.argv.slice(2).length === 1 && process.argv[2] === "--help") {
    console.log("use --season <eight-digit consecutive years> --out <new directory with existing parent>");
  } else {
    const { values, tokens } = parseArgs({
      options: { season: { type: "string" }, out: { type: "string" } },
      tokens: true,
      allowPositionals: false,
    });
    const seasonId = values.season;
    const outDirectory = values.out;
    if (
      seasonId === undefined || !/^\d{8}$/.test(seasonId) ||
      Number(seasonId.slice(4)) !== Number(seasonId.slice(0, 4)) + 1 ||
      outDirectory === undefined || outDirectory.length === 0 ||
      tokens.filter((token) => token.kind === "option" && token.name === "season").length !== 1 ||
      tokens.filter((token) => token.kind === "option" && token.name === "out").length !== 1
    ) {
      throw new Error("invalid season capture arguments");
    }

    await Effect.runPromise(captureSeason({ seasonId, outDirectory }).pipe(
      Effect.provide(NodeFileSystem.layer),
      Effect.provide(FetchHttpClient.layer),
      Effect.match({
        onFailure: (error) => {
          process.exitCode = reportCaptureFailure(error, outDirectory);
        },
        onSuccess: (records) => {
          process.exitCode = reportCaptures(records, { seasonId }, outDirectory);
        },
      }),
    ));
  }
} catch {
  console.error("season capture failed: use --season <eight-digit consecutive years> --out <new directory>; check the arguments and runtime");
  process.exitCode = 1;
}
