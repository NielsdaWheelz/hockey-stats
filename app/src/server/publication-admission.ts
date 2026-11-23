import * as SqliteClient from "@effect/sql-sqlite-node/SqliteClient";
import * as Cause from "effect/Cause";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Schema from "effect/Schema";
import * as Reactivity from "effect/reactivity/Reactivity";
import { createHash, randomUUID } from "node:crypto";
import type { BigIntStats } from "node:fs";
import { lstat, open, readdir, readFile, rename, rm } from "node:fs/promises";
import { join, relative } from "node:path";
import { performance } from "node:perf_hooks";
import { fileURLToPath } from "node:url";
import { isDeepStrictEqual } from "node:util";
import { AvailableSeasons, Count, Timestamp } from "../shared/observed.js";
import * as A from "../shared/player-analysis.js";
import {
  decode,
  readAnalysisIndexes,
  validateAnalysis,
  validateDatabaseHeader,
  validatePhysical,
} from "./analysis-publication.js";
import { validateObserved } from "./observed-publication.js";
import { makePublication, Publication, readPublicationMetadata } from "./publication.js";
import { strictJson } from "./sql-rows.js";

const ValidationReceipt = Schema.Struct({
  schema_version: Schema.Literal(1),
  validation_contract: Schema.Literal("publication-admission-v1"),
  database: Schema.Struct({
    sha256: A.Digest,
    bytes: Count.check(Schema.isGreaterThan(0)),
    publication_id: A.Publication.fields.publication_id,
    schema_version: A.Publication.fields.schema_version,
    purpose: A.Purpose,
    available_seasons: AvailableSeasons,
  }),
  validator: Schema.Struct({
    sha256: A.Digest,
    node_version: A.Text,
    lockfile_sha256: A.Digest,
  }),
  checked_at: Timestamp,
});

export const validationFilename = (filename: string) => `${filename}.validation.json`;

const validatorIdentity = async () => {
  const backend = fileURLToPath(new URL("../", import.meta.url));
  const compiled: string[] = [];
  for (const group of ["server", "shared"]) {
    const entries = await readdir(join(backend, group), { recursive: true, withFileTypes: true });
    const files = entries
      .filter((entry) => entry.isFile() && entry.name.endsWith(".js"))
      .map((entry) => relative(backend, join(entry.parentPath, entry.name)));
    if (files.length === 0) throw new Error(`compiled validator files missing in ${group}`);
    compiled.push(...files);
  }
  const digest = createHash("sha256");
  for (const file of compiled.sort()) {
    const name = Buffer.from(file);
    const contents = await readFile(join(backend, file));
    const lengths = Buffer.alloc(16);
    lengths.writeBigUInt64BE(BigInt(name.length), 0);
    lengths.writeBigUInt64BE(BigInt(contents.length), 8);
    digest.update(lengths).update(name).update(contents);
  }
  const lockfile = await readFile(new URL("../../../package-lock.json", import.meta.url));
  return {
    sha256: digest.digest("hex"),
    node_version: process.version,
    lockfile_sha256: createHash("sha256").update(lockfile).digest("hex"),
  };
};

export const assertNoSqliteCompanions = async (filename: string) => {
  for (const suffix of ["-journal", "-wal", "-shm"]) {
    try {
      await lstat(filename + suffix);
    } catch (error) {
      if (error instanceof Error && "code" in error && error.code === "ENOENT") continue;
      throw error;
    }
    throw new Error(`publication has an unfinished sqlite companion ${filename + suffix}`);
  }
};

const sameFile = (a: BigIntStats, b: BigIntStats) =>
  a.dev === b.dev && a.ino === b.ino && a.size === b.size &&
  a.mtimeNs === b.mtimeNs && a.ctimeNs === b.ctimeNs;

const assertNamedFile = async (filename: string, identity: BigIntStats) => {
  await assertNoSqliteCompanions(filename);
  if (!sameFile(identity, await lstat(filename, { bigint: true })))
    throw new Error(`publication file changed at ${filename}`);
};

const fileIdentity = async (filename: string) => {
  await assertNoSqliteCompanions(filename);
  // Check before open as well; special files may block an ordinary read open.
  if (!(await lstat(filename)).isFile())
    throw new Error(`publication must be a standalone regular file: ${filename}`);
  const handle = await open(filename, "r");
  try {
    const attributes = await handle.stat({ bigint: true });
    if (!attributes.isFile() || attributes.size <= 0n || attributes.size > BigInt(Number.MAX_SAFE_INTEGER))
      throw new Error(`publication has invalid file type or size: ${filename}`);
    const digest = createHash("sha256");
    let bytes = 0;
    for await (const chunk of handle.createReadStream({ autoClose: false })) {
      digest.update(chunk);
      bytes += chunk.length;
    }
    if (BigInt(bytes) !== attributes.size || !sameFile(attributes, await handle.stat({ bigint: true })))
      throw new Error(`publication changed during hashing: ${filename}`);
    await assertNamedFile(filename, attributes);
    return { database: { sha256: digest.digest("hex"), bytes }, attributes };
  } finally {
    await handle.close();
  }
};

const openReadOnly = (filename: string) =>
  SqliteClient.make({ filename, readonly: true, disableWAL: true }).pipe(
    Effect.provide(Reactivity.layer),
  );

const receiptMetadata = (
  { publication_id, schema_version, purpose }: A.Publication,
  available_seasons: readonly string[],
) => ({ publication_id, schema_version, purpose, available_seasons });

export const checkPublication = async (filename: string) => {
  const started = performance.now();
  const validator = await validatorIdentity();
  const before = await fileIdentity(filename);
  const beforeCheck = performance.now();
  const checked = await Effect.runPromise(Effect.scoped(Effect.gen(function* () {
    const sql = yield* openReadOnly(filename);
    yield* validatePhysical(sql);
    const header = yield* readPublicationMetadata(sql);
    const indexes = yield* readAnalysisIndexes(sql, header.catalogs);
    yield* validateAnalysis(sql, header.catalogs, indexes, header.prepared);
    yield* validateObserved(sql, header.seasons, header.metadata.purpose);
    const publication = makePublication(sql, header, indexes);
    const seasons = [];
    for (const evidence of publication.seasons) {
      const selection = { season: evidence.season, family: "overview", strength: null } as const;
      const skater = yield* publication.league({ ...selection, kind: "skater" });
      const goalie = yield* publication.league({ ...selection, kind: "goalie" });
      seasons.push({
        ...skater.season,
        players: skater.players.length + goalie.players.length,
        skaters: skater.players.length,
        goalies: goalie.players.length,
      });
    }
    return { publication: publication.metadata, available_seasons: header.available_seasons, seasons };
  })));
  const afterCheck = performance.now();
  const after = await fileIdentity(filename);
  if (!isDeepStrictEqual(before.database, after.database) || !sameFile(before.attributes, after.attributes))
    throw new Error("publication database changed during full validation");
  if (!isDeepStrictEqual(validator, await validatorIdentity()))
    throw new Error("validator code, runtime or lockfile changed during full validation");
  const receipt = decode(ValidationReceipt, {
    schema_version: 1,
    validation_contract: "publication-admission-v1",
    database: { ...after.database, ...receiptMetadata(checked.publication, checked.available_seasons) },
    validator,
    checked_at: new Date().toISOString(),
  });
  const sidecar = validationFilename(filename);
  const temporary = `${sidecar}.${randomUUID()}.tmp`;
  const file = await open(temporary, "wx");
  try {
    try {
      await file.writeFile(JSON.stringify(receipt, null, 2) + "\n");
    } finally {
      await file.close();
    }
    await rename(temporary, sidecar);
  } catch (error) {
    await rm(temporary, { force: true });
    throw error;
  }
  return {
    ...checked,
    path: filename,
    receipt,
    timings_ms: {
      precheck: beforeCheck - started,
      full_checks: afterCheck - beforeCheck,
      total: performance.now() - started,
    },
  };
};

const readAdmitted = (filename: string) =>
  Effect.gen(function* () {
    const { receipt, identity, hash_ms } = yield* Effect.tryPromise(async () => {
      const sidecar = validationFilename(filename);
      let receipt;
      try {
        receipt = decode(ValidationReceipt, strictJson(await readFile(sidecar, "utf8")));
      } catch (cause) {
        throw new Error(`validation receipt could not be read or is incompatible: ${sidecar}`, { cause });
      }
      const validator = await validatorIdentity();
      if (receipt.validator.sha256 !== validator.sha256)
        throw new Error("validation receipt validator code digest differs");
      if (receipt.validator.node_version !== validator.node_version)
        throw new Error("validation receipt node runtime differs");
      if (receipt.validator.lockfile_sha256 !== validator.lockfile_sha256)
        throw new Error("validation receipt lockfile digest differs");
      const start = performance.now();
      const identity = await fileIdentity(filename);
      if (identity.database.sha256 !== receipt.database.sha256 ||
          identity.database.bytes !== receipt.database.bytes)
        throw new Error("validation receipt database digest or byte count differs");
      return { receipt, identity, hash_ms: performance.now() - start };
    });
    const start = performance.now();
    yield* Effect.tryPromise(() => assertNamedFile(filename, identity.attributes));
    const sql = yield* openReadOnly(filename);
    yield* Effect.tryPromise(() => assertNamedFile(filename, identity.attributes));
    yield* validateDatabaseHeader(sql);
    const header = yield* readPublicationMetadata(sql);
    const database = { ...identity.database, ...receiptMetadata(header.metadata, header.available_seasons) };
    if (!isDeepStrictEqual(receipt.database, database))
      return yield* Effect.fail(new Error("validation receipt database metadata differs"));
    const indexes = yield* readAnalysisIndexes(sql, header.catalogs);
    const reader = makePublication(sql, header, indexes);
    yield* Effect.tryPromise(() => assertNamedFile(filename, identity.attributes));
    return { reader, receipt, timings_ms: { hash: hash_ms, initialize: performance.now() - start } };
  }).pipe(
    Effect.mapError((error) => {
      const cause = Cause.isUnknownError(error) && error.cause instanceof Error
        ? error.cause : error;
      return new Error(
        `publication cannot open: ${cause.message}. run publication check with the compatible build for ${filename}`,
        { cause },
      );
    }),
  );

export const admittedPublicationLayer = (filename: string) =>
  Layer.effect(Publication, readAdmitted(filename).pipe(
    Effect.map(({ reader, timings_ms }) => {
      console.error(JSON.stringify({ publication_id: reader.metadata.publication_id, timings_ms }));
      return reader;
    }),
  ));

export const verifyAdmittedPublication = (filename: string) =>
  Effect.runPromise(Effect.scoped(readAdmitted(filename).pipe(
    Effect.map(({ reader, receipt, timings_ms }) => ({ publication: reader.metadata, receipt, timings_ms })),
  )));
