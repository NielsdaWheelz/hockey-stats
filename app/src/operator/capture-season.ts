import type { PlatformError } from "@effect/platform/Error";
import * as FileSystem from "@effect/platform/FileSystem";
import * as HttpClient from "@effect/platform/HttpClient";
import * as Effect from "effect/Effect";
import { captureResponse, type CaptureRecord } from "./capture.js";

// the cli validates consecutive season years; creating the destination prevents overwrite.
export const captureSeason = ({ seasonId, outDirectory }: {
  readonly seasonId: string;
  readonly outDirectory: string;
}): Effect.Effect<CaptureRecord[], PlatformError, FileSystem.FileSystem | HttpClient.HttpClient> =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem;
    yield* fs.makeDirectory(outDirectory);
    const sources = [
      { source: "season-summary", url: `https://api.nhle.com/stats/rest/en/season?cayenneExp=id%3D${seasonId}&limit=-1` },
      { source: "season-games", url: `https://api.nhle.com/stats/rest/en/game?cayenneExp=season%3D${seasonId}%20and%20gameType%3D2&limit=-1` },
      { source: "skater-bios", url: `https://api.nhle.com/stats/rest/en/skater/bios?isAggregate=false&isGame=false&cayenneExp=seasonId%3D${seasonId}%20and%20gameTypeId%3D2&limit=-1` },
      { source: "goalie-bios", url: `https://api.nhle.com/stats/rest/en/goalie/bios?isAggregate=false&isGame=false&cayenneExp=seasonId%3D${seasonId}%20and%20gameTypeId%3D2&limit=-1` },
    ] as const;
    const records: CaptureRecord[] = [];
    for (const { source, url } of sources) {
      records.push(yield* captureResponse({ identity: { seasonId, source }, url, outDirectory }));
    }
    return records;
  });
