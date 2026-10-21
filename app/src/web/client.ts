import * as Effect from "effect/Effect";
import * as Result from "effect/Result";
import * as FetchHttpClient from "effect/http/FetchHttpClient";
import * as HttpApiClient from "effect/http-api/HttpApiClient";
import { ObservedApi } from "../shared/observed";

const client = HttpApiClient.make(ObservedApi).pipe(
  Effect.provide(FetchHttpClient.layer),
);

async function read<A, E>(
  effect: Effect.Effect<A, E>,
  signal: AbortSignal,
): Promise<A> {
  const result = await Effect.runPromise(Effect.result(effect), { signal });
  if (Result.isSuccess(result)) return result.success;
  const error = result.failure;
  if (typeof error === "object" && error !== null && "_tag" in error) {
    if (error._tag === "PlayerNotFound")
      throw new Response("player not found", { status: 404 });
    if (error._tag === "InvalidSpatialSelection")
      throw new Response("invalid spatial selection", { status: 400 });
    if (error._tag === "InvalidPlayerId")
      throw new Response("invalid player id", { status: 400 });
  }
  throw new Response("results could not be loaded. please try again.", {
    status: 500,
  });
}

export const loadLeague = (signal: AbortSignal, spatialIds?: readonly string[]) =>
  read(
    Effect.flatMap(client, (api) => api.observed.league({ query: spatialIds?.length ? { spatial: spatialIds.join(",") } : {} })),
    signal,
  );
export const loadPlayer = (playerId: string, signal: AbortSignal) =>
  read(
    Effect.flatMap(client, (api) =>
      api.observed.player({ params: { playerId } }),
    ),
    signal,
  );
