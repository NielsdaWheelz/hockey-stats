import type { PlatformError } from "effect/PlatformError";
import * as FileSystem from "effect/FileSystem";
import * as HttpClient from "effect/http/HttpClient";
import * as Effect from "effect/Effect";
import { captureResponse, type CaptureIdentity, type CaptureRecord } from "./capture.js";

export type SkatingSelection =
  | { readonly source: "detail"; readonly seasonId: string; readonly playerId: string }
  | { readonly source: "listing"; readonly seasonId: string }
  | { readonly source: "glossary" };

// one explicit request; the fresh root prevents overwriting any previous attempt.
export const captureSkating = (
  selection: SkatingSelection,
  outDirectory: string,
): Effect.Effect<CaptureRecord, PlatformError | Error, FileSystem.FileSystem | HttpClient.HttpClient> =>
  Effect.gen(function* () {
    const seasonId = "seasonId" in selection ? selection.seasonId : undefined;
    const playerId = "playerId" in selection ? selection.playerId : undefined;
    if (
      outDirectory.trim().length === 0 ||
      (selection.source !== "detail" && selection.source !== "listing" && selection.source !== "glossary") ||
      (selection.source === "glossary" ? seasonId !== undefined :
        seasonId !== "20232024" && seasonId !== "20242025" && seasonId !== "20252026") ||
      (selection.source === "detail" ? playerId === undefined || !/^\d*[1-9]\d*$/.test(playerId) : playerId !== undefined)
    ) {
      return yield* Effect.fail(new Error("invalid skating selection or output directory"));
    }

    let identity: CaptureIdentity;
    let url: string;
    if (selection.source === "detail") {
      identity = { source: "edge-skating-detail", seasonId: selection.seasonId, playerId: selection.playerId, gameTypeId: 2 };
      url = `https://api-web.nhle.com/v1/edge/skater-skating-speed-detail/${selection.playerId}/${selection.seasonId}/2`;
    } else if (selection.source === "listing") {
      identity = { source: "edge-skating-listing", seasonId: selection.seasonId, gameTypeId: 2 };
      url = `https://www.nhl.com/nhl-edge/skaters/${selection.seasonId}/2/skating-speed/all`;
    } else {
      identity = { source: "edge-skating-glossary" };
      url = "https://www.nhl.com/nhl-edge/glossary";
    }

    const fs = yield* FileSystem.FileSystem;
    yield* fs.makeDirectory(outDirectory);
    return yield* captureResponse({ identity, url, outDirectory });
  });
