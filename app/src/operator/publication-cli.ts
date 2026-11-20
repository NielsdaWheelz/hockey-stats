import { constants } from "node:fs";
import { copyFile, lstat, mkdir, rename, rm } from "node:fs/promises";
import { resolve, join } from "node:path";
import { isDeepStrictEqual, parseArgs } from "node:util";
import {
  assertNoSqliteCompanions,
  checkPublication,
  validationFilename,
  verifyAdmittedPublication,
} from "../server/publication-admission.js";

const stage = async (source: string, directory: string) => {
  const { receipt } = await verifyAdmittedPublication(source);
  await mkdir(directory, { recursive: true });
  const incoming = join(directory, "incoming.sqlite");
  const sidecar = validationFilename(incoming);
  await copyFile(source, incoming, constants.COPYFILE_EXCL);
  let copiedReceipt = false;
  try {
    await copyFile(validationFilename(source), sidecar, constants.COPYFILE_EXCL);
    copiedReceipt = true;
    const checked = await verifyAdmittedPublication(incoming);
    if (!isDeepStrictEqual(receipt, checked.receipt))
      throw new Error("staged receipt differs from the verified source");
    return { ...checked, path: incoming };
  } catch (error) {
    if (copiedReceipt) await rm(sidecar);
    await rm(incoming);
    throw error;
  }
};

const present = async (filename: string) => {
  try {
    if (!(await lstat(filename)).isFile()) throw new Error(`expected a regular file: ${filename}`);
    return true;
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") return false;
    throw error;
  }
};

const activate = async (directory: string) => {
  const incoming = join(directory, "incoming.sqlite");
  const checked = await verifyAdmittedPublication(incoming);
  const active = join(directory, "active.sqlite");
  const previous = join(directory, "previous.sqlite");
  await assertNoSqliteCompanions(active);
  await assertNoSqliteCompanions(previous);
  const hasActive = await present(active);
  const hasReceipt = await present(validationFilename(active));
  await present(previous);
  await present(validationFilename(previous));
  if (hasActive) {
    await rename(active, previous);
    if (hasReceipt) await rename(validationFilename(active), validationFilename(previous));
    else await rm(validationFilename(previous), { force: true });
  }
  await rename(incoming, active);
  await rename(validationFilename(incoming), validationFilename(active));
  return {
    ...checked,
    path: active,
    predecessor: hasActive ? previous : null,
    next: "restart the local server and reload the page",
  };
};

try {
  const command = process.argv[2];
  const { values, tokens } = parseArgs({
    args: process.argv.slice(3),
    options: { candidate: { type: "string" }, directory: { type: "string" } },
    tokens: true,
    allowPositionals: false,
  });
  if (command !== "check" && command !== "stage" && command !== "activate" && command !== "restore")
    throw new Error("choose check, stage, activate or restore");
  for (const option of ["candidate", "directory"] as const) {
    if (
      tokens.filter((token) => token.kind === "option" && token.name === option).length > 1 ||
      values[option] === ""
    )
      throw new Error(`supply --${option} once with a nonempty path`);
  }
  const { candidate, directory } = values;
  let report;
  if (command === "check") {
    if (candidate === undefined || directory !== undefined)
      throw new Error("check requires --candidate only");
    report = await checkPublication(resolve(candidate));
  } else if (command === "stage") {
    if (candidate === undefined || directory === undefined)
      throw new Error("stage requires --candidate and --directory");
    report = await stage(resolve(candidate), resolve(directory));
  } else {
    if (candidate !== undefined || directory === undefined)
      throw new Error(`${command} requires --directory only`);
    if (command === "restore") {
      try {
        await stage(join(resolve(directory), "previous.sqlite"), resolve(directory));
      } catch (error) {
        console.error(
          "to restore a previous database from another schema, use the documented manual rollback with its matching build",
        );
        throw error;
      }
    }
    report = await activate(resolve(directory));
  }
  console.log(JSON.stringify({ ...report, action: command }, null, 2));
} catch (error) {
  console.error(
    "publication command failed. inspect any staged files before retrying. if rotation began, repair the database and receipt pairs before restarting",
    error,
  );
  process.exitCode = 1;
}
