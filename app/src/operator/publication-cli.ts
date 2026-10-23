import * as Effect from "effect/Effect";
import { createHash } from "node:crypto";
import { constants, createReadStream } from "node:fs";
import { copyFile, mkdir, rename, stat } from "node:fs/promises";
import { resolve, join } from "node:path";
import { parseArgs } from "node:util";
import { Publication, publicationLayer } from "../server/publication.js";

const fileIdentity = async (filename: string) => {
  const digest = createHash("sha256");
  let bytes = 0;
  for await (const chunk of createReadStream(filename)) {
    digest.update(chunk);
    bytes += chunk.length;
  }
  return { sha256: digest.digest("hex"), bytes };
};

const check = (filename: string) =>
  Effect.runPromise(
    Effect.gen(function* () {
      const publication = yield* Publication;
      const seasons = [];
      for (const evidence of publication.seasons) {
        const league = yield* publication.league({
          season: evidence.season,
          kind: "skater",
          family: "overview",
          strength: null,
        });
        const goalies = yield* publication.league({
          season: evidence.season,
          kind: "goalie",
          family: "overview",
          strength: null,
        });
        seasons.push({
          ...league.season,
          players: league.players.length + goalies.players.length,
          skaters: league.players.length,
          goalies: goalies.players.length,
        });
      }
      return {
        publication: publication.metadata,
        available_seasons: seasons.map((evidence) => evidence.season),
        seasons,
        path: filename,
      };
    }).pipe(Effect.provide(publicationLayer(filename))),
  );

try {
  const command = process.argv[2];
  const { values, tokens } = parseArgs({
    args: process.argv.slice(3),
    options: { candidate: { type: "string" }, directory: { type: "string" } },
    tokens: true,
    allowPositionals: false,
  });
  if (command !== "check" && command !== "activate" && command !== "restore")
    throw new Error("choose check, activate or restore");
  for (const option of ["candidate", "directory"] as const) {
    if (
      tokens.filter((token) => token.kind === "option" && token.name === option).length > 1 ||
      values[option] === ""
    )
      throw new Error(`supply --${option} once with a nonempty path`);
  }
  if (command === "check") {
    if (values.candidate === undefined || values.directory !== undefined)
      throw new Error("check requires --candidate only");
    console.log(JSON.stringify(await check(resolve(values.candidate)), null, 2));
  } else {
    if (
      values.directory === undefined ||
      (command === "activate" ? values.candidate === undefined : values.candidate !== undefined)
    )
      throw new Error(
        "activate requires --candidate and --directory; restore requires --directory only",
      );
    const directory = resolve(values.directory);
    const active = join(directory, "active.sqlite");
    const previous = join(directory, "previous.sqlite");
    const incoming = join(directory, "incoming.sqlite");
    const source = command === "activate" ? resolve(values.candidate!) : previous;
    const expectedIdentity = await fileIdentity(source);
    await mkdir(directory, { recursive: true });
    await copyFile(source, incoming, constants.COPYFILE_EXCL);
    const actualIdentity = await fileIdentity(incoming);
    if (
      actualIdentity.sha256 !== expectedIdentity.sha256 ||
      actualIdentity.bytes !== expectedIdentity.bytes
    )
      throw new Error("incoming publication digest differs from source");
    let checked;
    try {
      checked = await check(incoming);
    } catch (error) {
      if (command === "restore")
        console.error(
          "if the previous database uses another schema: stop the server, manually copy the previous database, rebuild its matching git revision, then restart; this reader accepts schema 7 only",
        );
      throw error;
    }
    let activeExists = true;
    try {
      await stat(active);
    } catch (error) {
      if (error instanceof Error && "code" in error && error.code === "ENOENT")
        activeExists = false;
      else throw error;
    }
    let predecessor: { sha256: string; bytes: number } | null = null;
    if (activeExists) {
      predecessor = await fileIdentity(active);
      await rename(active, previous);
    }
    await rename(incoming, active);
    console.log(
      JSON.stringify(
        {
          ...checked,
          path: active,
          action: command,
          predecessor,
          predecessor_validation:
            "preserved as opaque bytes; validate cross-schema predecessors with their matching git build",
          next: "restart the local server and reload the page",
        },
        null,
        2,
      ),
    );
  }
} catch (error) {
  console.error(
    "publication command failed; active/previous are unchanged unless rotation began; inspect any incoming.sqlite before retrying",
    error,
  );
  process.exitCode = 1;
}
