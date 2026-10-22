import * as Schema from "effect/Schema";
import { HockeyId, Season, InvalidSeasonSelection, SeasonNotFound } from "./observed.js";

export class SelectionError extends Error {
  constructor(
    readonly status: 400 | 404,
    message: string,
  ) {
    super(message);
  }
}
const invalid = (message: string): never => {
  throw new SelectionError(400, message);
};
const one = (query: URLSearchParams, name: string, required = true): string | undefined => {
  const values = query.getAll(name);
  if (values.length > 1 || values[0] === "" || (required && values.length === 0))
    invalid(`select ${name} once`);
  return values[0];
};
const keys = (query: URLSearchParams, allowed: readonly string[]) => {
  for (const key of query.keys()) if (!allowed.includes(key)) invalid(`unknown selector: ${key}`);
};
const member = <T extends string>(
  value: string | undefined,
  values: readonly T[],
  label: string,
): T => {
  if (value === undefined || !values.includes(value as T)) invalid(`invalid ${label}`);
  return value as T;
};
const ids = (value: string | undefined): readonly string[] => {
  const selected = value?.split(",") ?? [];
  if (
    selected.length < 1 ||
    selected.length > 2 ||
    new Set(selected).size !== selected.length ||
    selected.some((id) => !Schema.is(HockeyId)(id))
  )
    invalid("select one or two distinct player ids");
  return selected;
};
export const selectSeason = (
  query: URLSearchParams,
  seasons: readonly Season[],
  required = false,
): Season => {
  const values = query.getAll("season");
  if (values.length === 0 && !required) return seasons[0];
  if (values.length !== 1 || !Schema.is(Season)(values[0]))
    throw {
      _tag: "InvalidSeasonSelection",
      message: "select one canonical season",
      available_seasons: seasons,
    } satisfies typeof InvalidSeasonSelection.Type;
  const selected = values[0];
  if (!seasons.includes(selected))
    throw {
      _tag: "SeasonNotFound",
      message: `season ${selected} is not published`,
      available_seasons: seasons,
    } satisfies typeof SeasonNotFound.Type;
  return selected;
};
export const parsePlayerSelection = (query: URLSearchParams, seasons: readonly Season[]) => {
  keys(query, ["season"]);
  return selectSeason(query, seasons);
};
const execution = ["5v5", "5v4", "5v3", "4v3", "4v5", "3v5", "3v4"] as const;
const spatial = [...execution, "pp", "pk"] as const;
const goalie = ["5v5", "4v4", "3v3", "5v4", "5v3", "4v3", "4v5", "3v5", "3v4", "ev", "pk"] as const;
const goalieEvidence = [...goalie, "covered_all"] as const;
const evidenceTypes = ["all", "wrist_snap", "slap", "tip", "backhand", "other"] as const;
const populations = [
  "recorded_all_attempts",
  "recorded_goals",
  "recorded_locatable_unblocked",
  "neutral_locatable_unblocked_value",
  "neutral_all_attempt_value",
] as const;
export const parseLeagueSelection = (query: URLSearchParams, seasons: readonly Season[]) => {
  keys(query, ["season", "kind", "family", "strength"]);
  const season = selectSeason(query, seasons);
  const kind = member(one(query, "kind", false) ?? "skater", ["skater", "goalie"] as const, "kind");
  const family = member(
    one(query, "family", false) ?? "overview",
    [
      "overview",
      "observed",
      "spatial",
      "execution",
      "shootiness",
      "penalties",
      "territory",
      "descriptive",
      "microstats",
      "goalie",
    ] as const,
    "family",
  );
  const raw = one(query, "strength", false);
  if (
    (kind === "goalie" && family !== "overview" && family !== "goalie") ||
    (kind === "skater" && family === "goalie")
  )
    invalid("family is incompatible with person kind");
  let strength: (typeof spatial)[number] | (typeof goalie)[number] | null = null;
  if (family === "observed") strength = member(raw, ["5v5"] as const, "strength");
  else if (family === "spatial") strength = member(raw, spatial, "strength");
  else if (family === "execution" || family === "shootiness")
    strength = member(raw, execution, "strength");
  else if (family === "goalie") strength = member(raw, goalie, "strength");
  else if (raw !== undefined) invalid("this family omits strength");
  return { season, kind, family, strength };
};
export const parseMapSelection = (query: URLSearchParams, seasons: readonly Season[]) => {
  keys(query, ["season", "players", "family", "strength", "view", "population", "type"]);
  const season = selectSeason(query, seasons, true),
    players = ids(one(query, "players"));
  const family = member(
    one(query, "family"),
    [
      "observed",
      "offense_attempts",
      "defense_attempts",
      "offense_xg",
      "defense_xg",
      "finishing",
      "setting",
      "ice_won",
      "ice_lost",
      "goalie_stopping",
      "goalie_evidence",
    ] as const,
    "map family",
  );
  const rawStrength = one(query, "strength"),
    rawView = one(query, "view");
  if (family === "goalie_evidence")
    return {
      season,
      players,
      family,
      strength: member(rawStrength, goalieEvidence, "strength"),
      view: member(rawView, ["evidence_mass", "evidence_ratio"] as const, "view"),
      population: member(one(query, "population"), ["unblocked", "on_net"] as const, "population"),
      type: member(one(query, "type"), evidenceTypes, "type"),
    };
  if (query.has("population") || query.has("type"))
    invalid("goalie evidence selectors require goalie_evidence");
  const strength = member(
    rawStrength,
    family === "observed" || family === "ice_won" || family === "ice_lost"
      ? ["5v5"]
      : family === "goalie_stopping"
        ? goalie
        : family === "finishing" || family === "setting"
          ? execution
          : spatial,
    "strength",
  );
  const view = member(
    rawView,
    family === "observed" || family.startsWith("offense_") || family.startsWith("defense_")
      ? (["effect", "complete"] as const)
      : (["effect"] as const),
    "view",
  );
  if (
    (family.startsWith("offense_") && ["4v5", "3v5", "3v4", "pk"].includes(strength)) ||
    (family.startsWith("defense_") && ["5v4", "5v3", "4v3", "pp"].includes(strength))
  )
    invalid("map role is incompatible with strength");
  return { season, players, family, strength, view, population: null, type: null };
};
export const parseEvidenceSelection = (
  query: URLSearchParams,
  seasons: readonly Season[],
  player_id: string,
) => {
  keys(query, [
    "season",
    "family",
    "strength",
    "population",
    "type",
    "outcome",
    "shot_type",
    "blocked_contacts",
  ]);
  const season = selectSeason(query, seasons, true);
  const family = member(
    one(query, "family"),
    [
      "personal_shots",
      "execution",
      "goalie",
      "goalie_evidence",
      "penalties",
      "territory",
      "microstats",
    ] as const,
    "evidence family",
  );
  const raw = one(query, "strength", false);
  if (family === "personal_shots") {
    if (query.has("population") || query.has("type")) invalid("unrelated evidence selector");
    return {
      season,
      player_id,
      family,
      strength: member(raw, ["5v5"] as const, "strength"),
      outcome: member(
        one(query, "outcome"),
        ["all_unblocked", "on_net", "goal", "save", "miss"] as const,
        "outcome",
      ),
      shot_type: one(query, "shot_type", false) ?? null,
      blocked_contacts:
        member(
          one(query, "blocked_contacts", false) ?? "false",
          ["true", "false"],
          "blocked_contacts",
        ) === "true",
      population: null,
      type: null,
    };
  }
  if (["outcome", "shot_type", "blocked_contacts"].some((key) => query.has(key)))
    invalid("personal shot selectors require personal_shots");
  if (family === "goalie_evidence")
    return {
      season,
      player_id,
      family,
      strength: member(raw, goalieEvidence, "strength"),
      population: member(one(query, "population"), ["unblocked", "on_net"] as const, "population"),
      type: member(one(query, "type"), evidenceTypes, "type"),
      outcome: null,
      shot_type: null,
      blocked_contacts: false,
    };
  if (query.has("population") || query.has("type"))
    invalid("goalie evidence selectors require goalie_evidence");
  if (!["execution", "goalie"].includes(family) && raw !== undefined)
    invalid("this family omits strength");
  return {
    season,
    player_id,
    family,
    strength:
      family === "execution"
        ? member(raw, execution, "strength")
        : family === "goalie"
          ? member(raw, goalie, "strength")
          : null,
    population: null,
    type: null,
    outcome: null,
    shot_type: null,
    blocked_contacts: false,
  };
};
export const parseContextSelection = (
  query: URLSearchParams,
  seasons: readonly Season[],
  player_id: string,
) => {
  keys(query, ["season", "mode", "population", "teammates"]);
  const season = selectSeason(query, seasons, true),
    mode = member(one(query, "mode"), ["on_off", "with_without"] as const, "mode");
  const population = member(one(query, "population"), populations, "population");
  if (mode === "on_off" && query.has("teammates")) invalid("on_off omits teammates");
  const teammates = mode === "with_without" ? ids(one(query, "teammates")) : [];
  if (teammates.includes(player_id)) invalid("teammates exclude the focal player");
  return { season, player_id, mode, population, teammates };
};
