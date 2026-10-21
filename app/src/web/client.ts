import * as Effect from "effect/Effect";
import * as Result from "effect/Result";
import * as FetchHttpClient from "effect/http/FetchHttpClient";
import * as HttpApiClient from "effect/http-api/HttpApiClient";
import * as Schema from "effect/Schema";
import { ApiError, ObservedApi } from "../shared/observed";

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
  if (Schema.is(ApiError)(error)) {
    const status = error._tag === "PlayerNotFound" || error._tag === "SeasonNotFound" ? 404 : error._tag === "ReadFailure" ? 500 : 400;
    throw new Response(JSON.stringify(error), { status, headers: { "content-type": "application/json" } });
  }
  throw new Response(JSON.stringify({ _tag: "ReadFailure", message: "results could not be loaded. please try again." }), {
    status: 500, headers: { "content-type": "application/json" },
  });
}

const selection = (query: URLSearchParams, key: string) => {
  const values = query.getAll(key);
  return values.length === 0 ? undefined : values.length === 1 ? values[0] : values;
};
export const loadLeague = (signal: AbortSignal, query: URLSearchParams) =>
  read(
    Effect.flatMap(client, (api) => api.observed.league({ query: {season:selection(query,"season"),spatial:selection(query,"spatial")} })),
    signal,
  );
export const loadPlayer = (playerId: string, signal: AbortSignal, query: URLSearchParams) =>
  read(
    Effect.flatMap(client, (api) =>
      api.observed.player({ params: { playerId }, query: {season:selection(query,"season")} }),
    ),
    signal,
  );
