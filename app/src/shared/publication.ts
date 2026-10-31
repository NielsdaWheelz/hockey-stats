import * as Schema from "effect/Schema";

export const HockeyId = Schema.String.check(
  Schema.isPattern(/^[1-9]\d*$/),
  Schema.makeFilter((value) => BigInt(value) <= BigInt(Number.MAX_SAFE_INTEGER)),
);
export const GameId = Schema.String.check(Schema.isPattern(/^[1-9]\d{9}$/));
export const Season = Schema.String.check(
  Schema.isPattern(/^[1-9]\d{7}$/),
  Schema.makeFilter((value) => Number(value.slice(4)) === Number(value.slice(0, 4)) + 1),
);
export type Season = typeof Season.Type;
export const Count = Schema.Finite.check(
  Schema.isInt(),
  Schema.isGreaterThanOrEqualTo(0),
  Schema.isLessThanOrEqualTo(Number.MAX_SAFE_INTEGER),
);
export const Rate = Schema.Finite.check(Schema.isGreaterThanOrEqualTo(0));
export const DateString = Schema.String.check(
  Schema.isPattern(/^\d{4}-\d{2}-\d{2}$/),
  Schema.makeFilter(
    (value) =>
      !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value,
  ),
);
export const Timestamp = Schema.String.check(
  Schema.isPattern(/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/),
  Schema.makeFilter(
    (value) =>
      !Number.isNaN(Date.parse(value)) &&
      new Date(value).toISOString().slice(0, 19) === value.slice(0, 19),
  ),
);
export const GitCommit = Schema.NullOr(Schema.String.check(Schema.isPattern(/^[a-f0-9]{40}$/)));

export const Text = Schema.String.check(
  Schema.isMinLength(1),
  Schema.makeFilter((value) => value.trim().length > 0),
);
export const Digest = Schema.String.check(Schema.isPattern(/^[a-f0-9]{64}$/));
export const Id = HockeyId;
export const Purpose = Schema.Literals(["real", "fixture"]);
export const Family = Schema.Literals([
  "descriptive",
  "microstats",
  "spatial",
  "execution",
  "shootiness",
  "penalties",
  "territory",
  "goalie",
  "ledger",
  "evidence",
]);
export type Family = typeof Family.Type;
export const FamilyAvailability = Schema.Struct({
  season: Season,
  family: Family,
  availability: Schema.Literals(["provided", "not_computed"]),
  explanation: Schema.NullOr(Text),
}).check(
  Schema.makeFilter(
    (value) => (value.availability === "not_computed") === (value.explanation !== null),
  ),
);
export const Publication = Schema.Struct({
  publication_id: Schema.String.check(Schema.isUUID()),
  kind: Schema.Literal("player_analysis"),
  schema_version: Schema.Literal(8),
  purpose: Purpose,
  generated_at: Timestamp,
  population_version: Schema.Literal("matched_attempts_v2"),
  personal_population_version: Schema.Literal("matched_personal_credits_v2"),
  spatial_population_version: Schema.Literal("matched_unblocked_locations_v2"),
  spatial_display_version: Schema.Literal("rect5_gaussian10_v1"),
  git_commit: GitCommit,
  families: Schema.Array(FamilyAvailability).check(
    Schema.makeFilter((rows) => {
      const keys = rows.map((row) => `${row.season}:${row.family}`);
      if (rows.length === 0 || new Set(keys).size !== rows.length) return false;
      return [...new Set(rows.map((row) => row.season))].every((season) =>
        Family.literals.every((family) =>
          rows.some((row) => row.season === season && row.family === family),
        ),
      );
    }),
  ),
});
export type Publication = typeof Publication.Type;
