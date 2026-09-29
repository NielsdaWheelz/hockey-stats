import * as NodeFileSystem from "@effect/platform-node/NodeFileSystem";
import * as FetchHttpClient from "@effect/platform/FetchHttpClient";
import * as Effect from "effect/Effect";
import { parseArgs } from "node:util";
import { captureGame } from "./capture.js";

try {
  const { values, tokens } = parseArgs({
    options: { game: { type: "string" }, out: { type: "string" } },
    tokens: true,
    allowPositionals: false,
  });
  const gameId = values.game;
  const outDirectory = values.out;
  if (
    gameId === undefined || !/^\d{10}$/.test(gameId) ||
    outDirectory === undefined || outDirectory.length === 0 ||
    tokens.filter((token) => token.kind === "option" && token.name === "game").length !== 1 ||
    tokens.filter((token) => token.kind === "option" && token.name === "out").length !== 1
  ) {
    throw new Error("invalid capture arguments");
  }

  await Effect.runPromise(captureGame({ gameId, outDirectory }).pipe(
    Effect.provide(NodeFileSystem.layer),
    Effect.provide(FetchHttpClient.layer),
    Effect.match({
      onFailure: (error) => {
        const path = error._tag === "SystemError" ? error.pathOrDescriptor ?? outDirectory : outDirectory;
        const action = error._tag === "SystemError" && error.reason === "AlreadyExists"
          ? "choose a new --out directory"
          : "check the parent directory, path permissions and disk space; retry with a new --out directory";
        console.error(`local capture failure at ${path}: ${error.description ?? error.message}; ${action}`);
        process.exitCode = 1;
      },
      onSuccess: (records) => {
        let captured2xx = 0;
        let capturedNon2xx = 0;
        let incomplete = 0;
        for (const record of records) {
          if (record.state === "failed") {
            incomplete++;
            console.log(`capture incomplete for ${record.source}, game ${gameId}: ${record.failure.message}; no complete body saved`);
          } else {
            const ok = record.httpStatus >= 200 && record.httpStatus < 300;
            if (ok) captured2xx++;
            else capturedNon2xx++;
            const suffix = ok ? "" : record.httpStatus >= 300 && record.httpStatus < 400
              ? "; redirect response; body preserved"
              : "; source error response; body preserved";
            console.log(`captured ${record.source} for game ${gameId}: http ${record.httpStatus}, ${record.body.bytes} bytes${suffix}`);
          }
        }
        console.log(`${captured2xx} captured 2xx responses; ${capturedNon2xx} captured non-2xx responses; ${incomplete} incomplete requests`);
        console.log(outDirectory);
        process.exitCode = captured2xx === 4 ? 0 : 1;
      },
    }),
  ));
} catch {
  console.error("capture failed: use --game <ten-digit game id> --out <new directory>; check the arguments and runtime");
  process.exitCode = 1;
}
