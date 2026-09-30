import * as NodeFileSystem from "@effect/platform-node/NodeFileSystem";
import * as FetchHttpClient from "@effect/platform/FetchHttpClient";
import * as Effect from "effect/Effect";
import { parseArgs } from "node:util";
import { captureGame, captureLanding } from "./capture.js";
import { reportCaptureFailure, reportCaptures } from "./capture-report.js";

try {
  const { values, tokens } = parseArgs({
    options: { game: { type: "string" }, out: { type: "string" }, source: { type: "string" } },
    tokens: true,
    allowPositionals: false,
  });
  const gameId = values.game;
  const outDirectory = values.out;
  const source = values.source;
  if (
    gameId === undefined || !/^\d{10}$/.test(gameId) ||
    outDirectory === undefined || outDirectory.length === 0 ||
    tokens.filter((token) => token.kind === "option" && token.name === "game").length !== 1 ||
    tokens.filter((token) => token.kind === "option" && token.name === "out").length !== 1 ||
    (source !== undefined && source !== "landing") ||
    tokens.filter((token) => token.kind === "option" && token.name === "source").length > 1
  ) {
    throw new Error("invalid capture arguments");
  }

  const capture = source === "landing" ? captureLanding : captureGame;
  await Effect.runPromise(capture({ gameId, outDirectory }).pipe(
    Effect.provide(NodeFileSystem.layer),
    Effect.provide(FetchHttpClient.layer),
    Effect.match({
      onFailure: (error) => {
        process.exitCode = reportCaptureFailure(error, outDirectory, source);
      },
      onSuccess: (records) => {
        process.exitCode = reportCaptures(records, { gameId }, outDirectory, source);
      },
    }),
  ));
} catch {
  console.error("capture failed: use --game <ten-digit game id> --out <new directory>, or --source landing --out <existing game directory>; check the arguments and runtime");
  process.exitCode = 1;
}
