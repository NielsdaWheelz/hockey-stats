import type { PlatformError } from "@effect/platform/Error";
import type { CaptureRecord } from "./capture.js";

const landingReplacement = "for a replacement, use an explicitly prepared new game-directory copy with no landing leaf; preserve the original directory and any landing leaf";

export const reportCaptureFailure = (error: PlatformError | Error, outDirectory: string, source?: "landing"): 1 => {
  const platformError = "_tag" in error ? error : undefined;
  const path = platformError?._tag === "SystemError" ? platformError.pathOrDescriptor ?? outDirectory : outDirectory;
  const action = source === "landing" ? `check the path and core receipt; ${landingReplacement}`
    : platformError?._tag === "SystemError" && platformError.reason === "AlreadyExists"
    ? "choose a new --out directory"
    : "check the parent directory, path permissions and disk space; retry with a new --out directory";
  console.error(`local capture failure at ${path}: ${platformError?.description ?? error.message}; ${action}`);
  return 1;
};

export const reportCaptures = (
  records: readonly CaptureRecord[],
  identity: { readonly gameId: string } | { readonly seasonId: string },
  outDirectory: string,
  source?: "landing",
): 0 | 1 => {
  const subject = "gameId" in identity ? `game ${identity.gameId}` : `season ${identity.seasonId}`;
  let captured2xx = 0;
  let capturedNon2xx = 0;
  let incomplete = 0;
  for (const record of records) {
    if (record.state === "failed") {
      incomplete++;
      console.log(`capture incomplete for ${record.source}, ${subject}: ${record.failure.kind}, http ${record.httpStatus ?? "unavailable"}; ${record.failure.message}; no complete body saved`);
    } else {
      const ok = record.httpStatus >= 200 && record.httpStatus < 300;
      if (ok) captured2xx++;
      else capturedNon2xx++;
      const suffix = ok ? "" : record.httpStatus >= 300 && record.httpStatus < 400
        ? "; redirect response; body preserved"
        : "; source error response; body preserved";
      console.log(`captured ${record.source} for ${subject}: http ${record.httpStatus}, ${record.body.bytes} bytes${suffix}`);
    }
  }
  console.log(`${captured2xx} captured 2xx responses; ${capturedNon2xx} captured non-2xx responses; ${incomplete} incomplete requests`);
  console.log(outDirectory);
  const succeeded = records.length > 0 && captured2xx === records.length;
  if (!succeeded && source === "landing") console.error(landingReplacement);
  return succeeded ? 0 : 1;
};
