import * as Effect from "effect/Effect";
import { createHash } from "node:crypto";
import { constants } from "node:fs";
import { copyFile, mkdir, readFile, rename, stat } from "node:fs/promises";
import { resolve, join } from "node:path";
import { parseArgs } from "node:util";
import { Publication, publicationLayer } from "../server/publication.js";

const check = (filename: string) => Effect.runPromise(Effect.gen(function* () {
  const publication = yield* Publication;
  return { publication: publication.metadata, coverage: publication.coverage, path: filename };
}).pipe(Effect.provide(publicationLayer(filename))));

try {
  const command = process.argv[2];
  const { values, tokens } = parseArgs({
    args: process.argv.slice(3), options: { candidate: { type: "string" }, directory: { type: "string" } },
    tokens: true, allowPositionals: false,
  });
  if (command !== "check" && command !== "activate" && command !== "restore") throw new Error("choose check, activate or restore");
  for (const option of ["candidate", "directory"] as const) {
    if (tokens.filter((token) => token.kind === "option" && token.name === option).length > 1 || values[option] === "") throw new Error(`supply --${option} once with a nonempty path`);
  }
  if (command === "check") {
    if (values.candidate === undefined || values.directory !== undefined) throw new Error("check requires --candidate only");
    console.log(JSON.stringify(await check(resolve(values.candidate)), null, 2));
  } else {
    if (values.directory === undefined || (command === "activate" ? values.candidate === undefined : values.candidate !== undefined)) throw new Error("activate requires --candidate and --directory; restore requires --directory only");
    const directory = resolve(values.directory);
    const active = join(directory, "active.sqlite");
    const previous = join(directory, "previous.sqlite");
    const incoming = join(directory, "incoming.sqlite");
    const source = command === "activate" ? resolve(values.candidate!) : previous;
    const expectedDigest = createHash("sha256").update(await readFile(source)).digest("hex");
    await mkdir(directory, { recursive: true });
    await copyFile(source, incoming, constants.COPYFILE_EXCL);
    const actualDigest = createHash("sha256").update(await readFile(incoming)).digest("hex");
    if (actualDigest !== expectedDigest) throw new Error("incoming publication digest differs from source");
    const checked = await check(incoming);
    let activeExists = true;
    try { await stat(active); } catch (error) {
      if (error instanceof Error && "code" in error && error.code === "ENOENT") activeExists = false;
      else throw error;
    }
    if (activeExists) {
      await check(active);
      await rename(active, previous);
    }
    await rename(incoming, active);
    console.log(JSON.stringify({ ...checked, path: active, action: command, next: "restart the local server and reload the page" }, null, 2));
  }
} catch (error) {
  console.error("publication command failed; active/previous are unchanged unless rotation began; inspect any incoming.sqlite before retrying", error);
  process.exitCode = 1;
}
