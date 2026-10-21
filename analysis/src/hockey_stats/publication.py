"""one checked sqlite publication from authoritative observed results."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import resource
import sqlite3
import sys
import time
import uuid

from .artifacts import implementation_identity, require, write_json
from .observed import PERSONAL_REASON_CODES, aggregate


_METRICS = """
    included_seconds INTEGER NOT NULL CHECK(included_seconds BETWEEN 0 AND 9007199254740991),
    known_excluded_seconds INTEGER NOT NULL CHECK(known_excluded_seconds BETWEEN 0 AND 9007199254740991),
    attempts_for INTEGER CHECK(attempts_for BETWEEN 0 AND 9007199254740991),
    attempts_against INTEGER CHECK(attempts_against BETWEEN 0 AND 9007199254740991),
    for_per60 REAL CHECK(for_per60 BETWEEN 0 AND 1.7976931348623157e308),
    against_per60 REAL CHECK(against_per60 BETWEEN 0 AND 1.7976931348623157e308),
    coverage_status TEXT NOT NULL CHECK(coverage_status IN ('complete','partial','unavailable')),
    reason_codes_json TEXT NOT NULL CHECK(json_valid(reason_codes_json) AND json_type(reason_codes_json)='array'),
    personal_included_seconds INTEGER NOT NULL CHECK(personal_included_seconds BETWEEN 0 AND included_seconds),
    personal_known_excluded_seconds INTEGER NOT NULL CHECK(personal_known_excluded_seconds BETWEEN known_excluded_seconds AND 9007199254740991),
    personal_shots_on_goal INTEGER CHECK(personal_shots_on_goal BETWEEN 0 AND 9007199254740991),
    personal_goals INTEGER CHECK(personal_goals BETWEEN 0 AND personal_shots_on_goal),
    personal_primary_assists INTEGER CHECK(personal_primary_assists BETWEEN 0 AND 9007199254740991),
    personal_shots_on_goal_per60 REAL CHECK(personal_shots_on_goal_per60 BETWEEN 0 AND 1.7976931348623157e308),
    personal_goals_per60 REAL CHECK(personal_goals_per60 BETWEEN 0 AND 1.7976931348623157e308),
    personal_primary_assists_per60 REAL CHECK(personal_primary_assists_per60 BETWEEN 0 AND 1.7976931348623157e308),
    personal_coverage_status TEXT NOT NULL CHECK(personal_coverage_status IN ('complete','partial','unavailable')),
    personal_reason_codes_json TEXT NOT NULL CHECK(json_valid(personal_reason_codes_json) AND json_type(personal_reason_codes_json)='array'),
    CHECK((included_seconds > 0 AND attempts_for IS NOT NULL AND attempts_against IS NOT NULL
            AND for_per60 IS NOT NULL AND against_per60 IS NOT NULL AND coverage_status IN ('complete','partial'))
       OR (included_seconds = 0 AND attempts_for IS 0 AND attempts_against IS 0
            AND for_per60 IS NULL AND against_per60 IS NULL AND coverage_status = 'complete')
       OR (included_seconds = 0 AND attempts_for IS NULL AND attempts_against IS NULL
            AND for_per60 IS NULL AND against_per60 IS NULL AND coverage_status = 'unavailable')),
    CHECK(coverage_status != 'complete' OR known_excluded_seconds = 0),
    CHECK((personal_included_seconds > 0 AND personal_shots_on_goal IS NOT NULL AND personal_goals IS NOT NULL
            AND personal_primary_assists IS NOT NULL AND personal_shots_on_goal_per60 IS NOT NULL
            AND personal_goals_per60 IS NOT NULL AND personal_primary_assists_per60 IS NOT NULL
            AND personal_coverage_status IN ('complete','partial'))
       OR (personal_included_seconds = 0 AND personal_shots_on_goal IS 0 AND personal_goals IS 0
            AND personal_primary_assists IS NOT NULL AND personal_shots_on_goal_per60 IS NULL
            AND personal_goals_per60 IS NULL AND personal_primary_assists_per60 IS NULL
            AND (personal_coverage_status='complete' OR (personal_coverage_status='partial' AND personal_primary_assists>0)))
       OR (personal_included_seconds = 0 AND personal_shots_on_goal IS NULL AND personal_goals IS NULL
            AND personal_primary_assists IS NULL AND personal_shots_on_goal_per60 IS NULL
            AND personal_goals_per60 IS NULL AND personal_primary_assists_per60 IS NULL AND personal_coverage_status='unavailable')),
    CHECK(personal_known_excluded_seconds - known_excluded_seconds = included_seconds - personal_included_seconds),
    CHECK(personal_coverage_status != 'complete' OR personal_known_excluded_seconds = 0)
"""

_SCHEMA = """
CREATE TABLE publication (
    id INTEGER PRIMARY KEY CHECK(id=1),
    schema_version INTEGER NOT NULL CHECK(schema_version=2),
    kind TEXT NOT NULL CHECK(kind='observed_5v5'),
    publication_id TEXT NOT NULL,
    purpose TEXT NOT NULL CHECK(purpose IN ('real','fixture')),
    season TEXT NOT NULL CHECK(length(season)=8 AND season NOT GLOB '*[^0-9]*'),
    game_type INTEGER NOT NULL CHECK(game_type=2),
    generated_at TEXT NOT NULL,
    source_requested_min TEXT,
    source_requested_max TEXT,
    undated_sources INTEGER NOT NULL CHECK(undated_sources BETWEEN 0 AND 9007199254740991),
    population_version TEXT NOT NULL CHECK(population_version='matched_attempts_v1'),
    personal_population_version TEXT NOT NULL CHECK(personal_population_version='matched_personal_credits_v1'),
    corpus_sha256 TEXT NOT NULL CHECK(length(corpus_sha256)=64 AND corpus_sha256 NOT GLOB '*[^0-9a-f]*'),
    producer_json TEXT NOT NULL CHECK(json_valid(producer_json) AND json_type(producer_json)='object'),
    coverage_json TEXT NOT NULL CHECK(json_valid(coverage_json) AND json_type(coverage_json)='object')
) STRICT;
CREATE TABLE player (
    player_id TEXT PRIMARY KEY CHECK(player_id GLOB '[1-9]*' AND player_id NOT GLOB '*[^0-9]*'),
    display_name TEXT,
    reported_position TEXT NOT NULL CHECK(reported_position IN ('C','L','R','D','F')),
    name_source_json TEXT CHECK(name_source_json IS NULL OR (json_valid(name_source_json) AND json_type(name_source_json)='object')),
    position_source_json TEXT NOT NULL CHECK(json_valid(position_source_json) AND json_type(position_source_json)='object')
) STRICT;
CREATE TABLE game (
    game_id TEXT PRIMARY KEY CHECK(length(game_id)=10 AND game_id GLOB '[1-9]*' AND game_id NOT GLOB '*[^0-9]*'),
    game_date TEXT NOT NULL,
    away_team_id TEXT NOT NULL CHECK(away_team_id GLOB '[1-9]*' AND away_team_id NOT GLOB '*[^0-9]*'),
    home_team_id TEXT NOT NULL CHECK(home_team_id GLOB '[1-9]*' AND home_team_id NOT GLOB '*[^0-9]*'),
    away_abbreviation TEXT,
    home_abbreviation TEXT,
    included_seconds INTEGER NOT NULL CHECK(included_seconds BETWEEN 0 AND 9007199254740991),
    known_excluded_seconds INTEGER NOT NULL CHECK(known_excluded_seconds BETWEEN 0 AND 9007199254740991),
    personal_included_seconds INTEGER NOT NULL CHECK(personal_included_seconds BETWEEN 0 AND included_seconds),
    personal_known_excluded_seconds INTEGER NOT NULL CHECK(personal_known_excluded_seconds BETWEEN known_excluded_seconds AND 9007199254740991),
    known_unresolved_seconds INTEGER NOT NULL CHECK(known_unresolved_seconds BETWEEN 0 AND 9007199254740991),
    horizon_unavailable INTEGER NOT NULL CHECK(horizon_unavailable IN (0,1)),
    away_attempts INTEGER CHECK(away_attempts BETWEEN 0 AND 9007199254740991),
    home_attempts INTEGER CHECK(home_attempts BETWEEN 0 AND 9007199254740991),
    coverage_status TEXT NOT NULL CHECK(coverage_status IN ('complete','partial','unavailable')),
    reason_codes_json TEXT NOT NULL CHECK(json_valid(reason_codes_json) AND json_type(reason_codes_json)='array'),
    CHECK(away_team_id != home_team_id),
    CHECK(personal_known_excluded_seconds - known_excluded_seconds = included_seconds - personal_included_seconds),
    CHECK((included_seconds > 0 AND away_attempts IS NOT NULL AND home_attempts IS NOT NULL AND coverage_status IN ('complete','partial'))
       OR (included_seconds = 0 AND away_attempts IS 0 AND home_attempts IS 0 AND coverage_status='complete')
       OR (included_seconds = 0 AND away_attempts IS NULL AND home_attempts IS NULL AND coverage_status='unavailable'))
) STRICT;
CREATE TABLE player_game (
    player_id TEXT NOT NULL REFERENCES player(player_id),
    game_id TEXT NOT NULL REFERENCES game(game_id),
    team_id TEXT NOT NULL CHECK(team_id GLOB '[1-9]*' AND team_id NOT GLOB '*[^0-9]*'),
""" + _METRICS + """,
    PRIMARY KEY(player_id,game_id)
) STRICT;
CREATE TABLE player_season (
    player_id TEXT PRIMARY KEY REFERENCES player(player_id),
    teams_json TEXT NOT NULL CHECK(json_valid(teams_json) AND json_type(teams_json)='array'),
    listed_games INTEGER NOT NULL CHECK(listed_games BETWEEN 1 AND 9007199254740991),
    games_with_included_time INTEGER NOT NULL CHECK(games_with_included_time BETWEEN 0 AND listed_games),
    partial_games INTEGER NOT NULL CHECK(partial_games BETWEEN 0 AND listed_games),
    unavailable_games INTEGER NOT NULL CHECK(unavailable_games BETWEEN 0 AND listed_games),
""" + _METRICS + """
) STRICT;
"""


def _validate_personal(metrics, on_ice, loc):
    """check the personal null/status contract before writing its flattened columns."""
    seconds = metrics["included_seconds"]
    excluded = metrics["known_excluded_seconds"]
    reasons = metrics["reason_codes"]
    counts = [metrics[key] for key in ("shots_on_goal", "goals", "primary_assists")]
    rates = [metrics[key] for key in ("shots_on_goal_per60", "goals_per60", "primary_assists_per60")]
    require(list(reasons) == sorted(set(reasons)) and set(reasons) <= PERSONAL_REASON_CODES, f"{loc}: invalid personal reasons")
    require(all(type(value) is int and 0 <= value <= 9007199254740991 for value in (seconds, excluded)),
            f"{loc}: invalid personal seconds")
    require(seconds <= on_ice["included_seconds"] and excluded == on_ice["known_excluded_seconds"] + on_ice["included_seconds"] - seconds,
            f"{loc}: personal support exceeds on-ice support")
    require(all(value is None or type(value) is int and 0 <= value <= 9007199254740991 for value in counts),
            f"{loc}: invalid personal counts")
    require(all(value is None or type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in rates),
            f"{loc}: invalid personal rates")
    require(set(on_ice["reason_codes"]) - {"no_5v5_exposure"} <= set(reasons), f"{loc}: personal reasons omit inherited gaps")
    gaps = set(reasons) - {"no_personal_5v5_exposure"}
    status = metrics["coverage_status"]
    if counts[0] is not None and counts[1] is not None:
        require(counts[1] <= counts[0], f"{loc}: goals exceed shots on goal")
    if seconds:
        valid = (all(value is not None for value in counts + rates)
                 and "no_personal_5v5_exposure" not in reasons
                 and status == ("partial" if gaps else "complete")
                 and all(rate == 3600 * count / seconds for count, rate in zip(counts, rates)))
    elif all(value is None for value in counts):
        valid = status == "unavailable" and bool(gaps) and not any(value is not None for value in rates) and "no_personal_5v5_exposure" in reasons
    else:
        valid = (counts[0] == counts[1] == 0 and counts[2] is not None
                 and (counts[2] > 0 or not gaps) and all(value is None for value in rates)
                 and "no_personal_5v5_exposure" in reasons and status == ("partial" if gaps else "complete"))
    require(valid and (status != "complete" or excluded == 0), f"{loc}: inconsistent personal null/status/rate contract")


def build_publication(corpus_path: Path, purpose: str, output: Path) -> dict:
    """finalize only after source checks, independent read-back and receipt writing."""
    started = time.monotonic()
    corpus_path = corpus_path.resolve(strict=True)
    output = output.absolute()
    require(not output.exists() and not output.is_symlink(), f"{output}: output already exists")
    parent = output.parent.resolve(strict=True)
    require(parent.is_dir(), f"{parent}: output parent must be a directory")
    output = parent / output.name
    require(not output.is_relative_to(corpus_path.parent), "output must be outside the input corpus directory")
    output.mkdir()
    result = aggregate(corpus_path, purpose)
    producer = implementation_identity() | {
        "sqlite_version": sqlite3.sqlite_version,
        "source_implementations": list(result.source_implementations),
    }
    publication_id = str(uuid.uuid4())
    metadata = {
        "id": 1, "schema_version": 2, "kind": "observed_5v5",
        "publication_id": publication_id, "purpose": purpose, "season": result.season,
        "game_type": 2, "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_requested_min": result.source_requested_min,
        "source_requested_max": result.source_requested_max,
        "undated_sources": result.undated_sources, "population_version": "matched_attempts_v1",
        "personal_population_version": "matched_personal_credits_v1",
        "corpus_sha256": result.corpus_sha256,
        "producer_json": json.dumps(producer, allow_nan=False, sort_keys=True, separators=(",", ":")),
        "coverage_json": json.dumps(result.coverage, allow_nan=False, sort_keys=True, separators=(",", ":")),
    }
    tables = {"publication": [metadata]}
    for name, rows in (("player", result.players), ("game", result.games),
                       ("player_game", result.player_games), ("player_season", result.player_seasons)):
        stored = []
        for row in rows:
            fields = asdict(row)
            if "personal" in fields:
                personal = fields.pop("personal")
                _validate_personal(personal, fields, name)
                fields.update({"personal_" + key: value for key, value in personal.items()})
            for field in ("name_source", "position_source", "teams", "reason_codes", "personal_reason_codes"):
                if field in fields:
                    value = fields.pop(field)
                    fields[field + "_json"] = None if value is None else json.dumps(
                        value, allow_nan=False, sort_keys=True, separators=(",", ":"))
            if "horizon_unavailable" in fields:
                fields["horizon_unavailable"] = int(fields["horizon_unavailable"])
            for field, value in fields.items():
                if type(value) is int:
                    require(0 <= value <= 9007199254740991, f"{name}.{field}: unsafe integer")
                elif type(value) is float:
                    require(math.isfinite(value), f"{name}.{field}: nonfinite number")
            stored.append(fields)
        tables[name] = stored
    incomplete = output / "observed.sqlite.incomplete"
    connection = sqlite3.connect(incomplete)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.executescript("BEGIN;\n" + _SCHEMA)
        connection.execute("PRAGMA user_version=2")
        with connection:
            for table, rows in tables.items():
                for row in rows:
                    columns = ",".join(row)
                    placeholders = ",".join("?" for _ in row)
                    connection.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(row.values()))
    finally:
        connection.close()

    connection = sqlite3.connect(incomplete.as_uri() + "?mode=ro", uri=True)
    try:
        require(connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "sqlite integrity check failed")
        require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "sqlite foreign key check failed")
        require(connection.execute("PRAGMA journal_mode").fetchone() == ("delete",), "publication requires delete journal mode")
        require(connection.execute("PRAGMA user_version").fetchone() == (2,), "publication requires schema 2")
        connection.row_factory = sqlite3.Row
        for table, expected in tables.items():
            actual = [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            require(actual == expected, f"{table}: read-back differs from authoritative observed rows")
        connection.row_factory = None
        require(connection.execute("SELECT count(*) FROM player").fetchone()
                == connection.execute("SELECT count(*) FROM player_season").fetchone(), "player/season rows differ")
        require(not connection.execute("""SELECT 1 FROM player_game p JOIN game g USING(game_id)
            WHERE p.team_id NOT IN(g.away_team_id,g.home_team_id) LIMIT 1""").fetchall(), "player game team absent from game")
        seconds = connection.execute("SELECT coalesce(sum(included_seconds),0) FROM game").fetchone()[0]
        exposure = connection.execute("SELECT coalesce(sum(included_seconds),0) FROM player_game").fetchone()[0]
        require(exposure == 10 * seconds, "player exposure does not conserve physical time")
        attempts = connection.execute("SELECT coalesce(sum(away_attempts+home_attempts),0) FROM game").fetchone()[0]
        counts = connection.execute("SELECT coalesce(sum(attempts_for),0),coalesce(sum(attempts_against),0) FROM player_game").fetchone()
        require(counts == (5 * attempts, 5 * attempts), "player attempts do not conserve physical attempts")
        for row in connection.execute("""SELECT g.game_id,g.included_seconds,
                coalesce(g.away_attempts,0)+coalesce(g.home_attempts,0),
                coalesce(sum(p.included_seconds),0),coalesce(sum(p.attempts_for),0),coalesce(sum(p.attempts_against),0)
            FROM game g LEFT JOIN player_game p USING(game_id) GROUP BY g.game_id"""):
            gid, physical_seconds, physical_attempts, player_seconds, for_count, against_count = row
            require(player_seconds == 10 * physical_seconds
                    and for_count == against_count == 5 * physical_attempts, f"{gid}: stored game conservation failed")
        for row in connection.execute("""SELECT s.player_id,s.included_seconds,s.known_excluded_seconds,
                s.attempts_for,s.attempts_against,s.listed_games,s.games_with_included_time,s.partial_games,s.unavailable_games,
                sum(p.included_seconds),sum(p.known_excluded_seconds),coalesce(sum(p.attempts_for),0),
                coalesce(sum(p.attempts_against),0),count(*),sum(p.included_seconds>0),
                sum(p.coverage_status='partial'),sum(p.coverage_status='unavailable')
            FROM player_season s JOIN player_game p USING(player_id) GROUP BY s.player_id"""):
            pid, *values = row
            seconds_value, excluded_value, for_value, against_value, *frequencies = values[:8]
            reduced_seconds, reduced_excluded, reduced_for, reduced_against, *reduced_frequencies = values[8:]
            require(seconds_value == reduced_seconds and excluded_value == reduced_excluded
                    and (for_value is None or for_value == reduced_for)
                    and (against_value is None or against_value == reduced_against)
                    and frequencies == reduced_frequencies, f"{pid}: stored season reduction failed")
        personal_seconds = connection.execute("SELECT coalesce(sum(personal_included_seconds),0) FROM game").fetchone()[0]
        personal_exposure = connection.execute("SELECT coalesce(sum(personal_included_seconds),0) FROM player_game").fetchone()[0]
        require(personal_exposure == 10 * personal_seconds, "personal player exposure does not conserve physical time")
        for gid, physical, player in connection.execute("""SELECT g.game_id,g.personal_included_seconds,
                coalesce(sum(p.personal_included_seconds),0)
            FROM game g LEFT JOIN player_game p USING(game_id) GROUP BY g.game_id"""):
            require(player == 10 * physical, f"{gid}: personal stored game conservation failed")
        connection.row_factory = sqlite3.Row
        for season in connection.execute("SELECT * FROM player_season"):
            rows = connection.execute("SELECT * FROM player_game WHERE player_id=?", (season["player_id"],)).fetchall()
            reasons = set().union(*(json.loads(row["personal_reason_codes_json"]) for row in rows))
            if result.coverage["games_with_unassigned_player_associations"]:
                reasons.add("unassigned_player_games")
            reasons.discard("no_personal_5v5_exposure")
            for field in ("personal_included_seconds", "personal_known_excluded_seconds", "personal_shots_on_goal",
                          "personal_goals", "personal_primary_assists"):
                reduced = sum(row[field] or 0 for row in rows)
                require(season[field] is None or season[field] == reduced,
                        f"{season['player_id']}: personal {field} season reduction failed")
            if season["personal_included_seconds"] == 0:
                reasons.add("no_personal_5v5_exposure")
            require(json.loads(season["personal_reason_codes_json"]) == sorted(reasons),
                    f"{season['player_id']}: personal season reasons differ")
        require(purpose != "real" or seconds > 0, "real publication needs supported positive exposure")
    finally:
        connection.close()

    database_sha256 = hashlib.sha256(incomplete.read_bytes()).hexdigest()
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    verification = {
        "schema_version": 1, "kind": "observed_publication_verification", "publication_id": publication_id,
        "purpose": purpose, "season": result.season, "producer": producer,
        **result.receipt,
        "coverage": result.coverage,
        "database": {"path": str(output / "observed.sqlite"), "sha256": database_sha256},
        "checks": {"integrity": "passed", "foreign_keys": "passed", "read_back": "passed",
                   "physical_seconds": seconds, "player_seconds": exposure, "physical_attempts": attempts,
                   "player_attempts_for": counts[0], "player_attempts_against": counts[1],
                   "personal_physical_seconds": personal_seconds, "personal_player_seconds": personal_exposure},
        "cost": {"wall_seconds": time.monotonic() - started,
                 "peak_rss_bytes": rss if sys.platform == "darwin" else rss * 1024,
                 "consumed_bytes": sum(Path(row["path"]).stat().st_size for row in result.receipt.get("consumed", [])),
                 "database_bytes": incomplete.stat().st_size},
        "cost_scope": "through independent read-back; receipt writing and final rename excluded",
        "scientific_admission": "not_performed",
    }
    write_json(output / "verification.json", verification)
    incomplete.rename(output / "observed.sqlite")
    return verification
