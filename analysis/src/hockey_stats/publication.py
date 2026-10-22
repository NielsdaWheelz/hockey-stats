"""one checked sqlite publication from authoritative observed results."""

from contextlib import closing
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import resource
import sqlite3
import sys
import time
import uuid

from .artifacts import implementation_identity, linked_path, require, write_json
from .captures import strict_json
from .observed import PERSONAL_REASON_CODES, SPATIAL_REASON_CODES, _metrics, aggregate
from .observed_spatial import POPULATION_VERSION, DISPLAY_VERSION


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
    spatial_included_seconds INTEGER NOT NULL CHECK(spatial_included_seconds BETWEEN 0 AND included_seconds),
    spatial_known_excluded_seconds INTEGER NOT NULL CHECK(spatial_known_excluded_seconds BETWEEN known_excluded_seconds AND 9007199254740991),
    spatial_unblocked_for INTEGER CHECK(spatial_unblocked_for BETWEEN 0 AND 9007199254740991),
    spatial_unblocked_against INTEGER CHECK(spatial_unblocked_against BETWEEN 0 AND 9007199254740991),
    spatial_for_per60 REAL CHECK(spatial_for_per60 BETWEEN 0 AND 1.7976931348623157e308),
    spatial_against_per60 REAL CHECK(spatial_against_per60 BETWEEN 0 AND 1.7976931348623157e308),
    spatial_coverage_status TEXT NOT NULL CHECK(spatial_coverage_status IN ('complete','partial','unavailable')),
    spatial_reason_codes_json TEXT NOT NULL CHECK(json_valid(spatial_reason_codes_json) AND json_type(spatial_reason_codes_json)='array'),
    CHECK(spatial_known_excluded_seconds - known_excluded_seconds = included_seconds - spatial_included_seconds),
    CHECK(spatial_coverage_status != 'complete' OR spatial_known_excluded_seconds = 0),
    CHECK((spatial_included_seconds>0 AND spatial_unblocked_for IS NOT NULL AND spatial_unblocked_against IS NOT NULL
            AND spatial_for_per60 IS NOT NULL AND spatial_against_per60 IS NOT NULL AND spatial_coverage_status IN ('complete','partial'))
       OR (spatial_included_seconds=0 AND spatial_unblocked_for IS 0 AND spatial_unblocked_against IS 0
            AND spatial_for_per60 IS NULL AND spatial_against_per60 IS NULL AND spatial_coverage_status='complete')
       OR (spatial_included_seconds=0 AND spatial_unblocked_for IS NULL AND spatial_unblocked_against IS NULL
            AND spatial_for_per60 IS NULL AND spatial_against_per60 IS NULL AND spatial_coverage_status='unavailable')),
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
    schema_version INTEGER NOT NULL CHECK(schema_version=5),
    kind TEXT NOT NULL CHECK(kind='observed_5v5'),
    publication_id TEXT NOT NULL,
    purpose TEXT NOT NULL CHECK(purpose IN ('real','fixture')),
    game_type INTEGER NOT NULL CHECK(game_type=2),
    generated_at TEXT NOT NULL,
    population_version TEXT NOT NULL CHECK(population_version='matched_attempts_v2'),
    personal_population_version TEXT NOT NULL CHECK(personal_population_version='matched_personal_credits_v2'),
    producer_json TEXT NOT NULL CHECK(json_valid(producer_json) AND json_type(producer_json)='object'),
    spatial_population_version TEXT NOT NULL CHECK(spatial_population_version='matched_unblocked_locations_v2'),
    spatial_display_version TEXT NOT NULL CHECK(spatial_display_version='rect5_gaussian10_v1')
) STRICT;
CREATE TABLE season (
    season TEXT NOT NULL PRIMARY KEY CHECK(length(season)=8 AND season NOT GLOB '*[^0-9]*'
        AND substr(season,1,1)!='0' AND CAST(substr(season,5,4) AS INTEGER)=CAST(substr(season,1,4) AS INTEGER)+1),
    corpus_sha256 TEXT NOT NULL CHECK(length(corpus_sha256)=64 AND corpus_sha256 NOT GLOB '*[^0-9a-f]*'),
    source_requested_min TEXT,
    source_requested_max TEXT,
    undated_sources INTEGER NOT NULL CHECK(undated_sources BETWEEN 0 AND 9007199254740991),
    coverage_json TEXT NOT NULL CHECK(json_valid(coverage_json) AND json_type(coverage_json)='object'),
    source_implementations_json TEXT NOT NULL CHECK(json_valid(source_implementations_json) AND json_type(source_implementations_json)='array'),
    spatial_coverage_json TEXT NOT NULL CHECK(json_valid(spatial_coverage_json) AND json_type(spatial_coverage_json)='object')
) STRICT;
CREATE TABLE player (
    season TEXT NOT NULL REFERENCES season(season),
    player_id TEXT NOT NULL CHECK(player_id GLOB '[1-9]*' AND player_id NOT GLOB '*[^0-9]*'),
    display_name TEXT,
    reported_position TEXT NOT NULL CHECK(reported_position IN ('C','L','R','D','F')),
    name_source_json TEXT CHECK(name_source_json IS NULL OR (json_valid(name_source_json) AND json_type(name_source_json)='object')),
    position_source_json TEXT NOT NULL CHECK(json_valid(position_source_json) AND json_type(position_source_json)='object'),
    PRIMARY KEY(season,player_id)
) STRICT;
CREATE TABLE game (
    season TEXT NOT NULL REFERENCES season(season),
    game_id TEXT NOT NULL CHECK(length(game_id)=10 AND game_id GLOB '[1-9]*' AND game_id NOT GLOB '*[^0-9]*'
        AND substr(game_id,1,4)=substr(season,1,4) AND substr(game_id,5,2)='02'),
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
    spatial_included_seconds INTEGER NOT NULL CHECK(spatial_included_seconds BETWEEN 0 AND included_seconds),
    spatial_known_excluded_seconds INTEGER NOT NULL CHECK(spatial_known_excluded_seconds BETWEEN known_excluded_seconds AND 9007199254740991),
    spatial_away_unblocked INTEGER CHECK(spatial_away_unblocked BETWEEN 0 AND 9007199254740991),
    spatial_home_unblocked INTEGER CHECK(spatial_home_unblocked BETWEEN 0 AND 9007199254740991),
    spatial_coverage_status TEXT NOT NULL CHECK(spatial_coverage_status IN ('complete','partial','unavailable')),
    spatial_reason_codes_json TEXT NOT NULL CHECK(json_valid(spatial_reason_codes_json) AND json_type(spatial_reason_codes_json)='array'),
    CHECK(spatial_known_excluded_seconds - known_excluded_seconds = included_seconds - spatial_included_seconds),
    CHECK(spatial_coverage_status != 'complete' OR spatial_known_excluded_seconds = 0),
    CHECK((spatial_included_seconds>0 AND spatial_away_unblocked IS NOT NULL AND spatial_home_unblocked IS NOT NULL AND spatial_coverage_status IN ('complete','partial'))
       OR (spatial_included_seconds=0 AND spatial_away_unblocked IS 0 AND spatial_home_unblocked IS 0 AND spatial_coverage_status='complete')
       OR (spatial_included_seconds=0 AND spatial_away_unblocked IS NULL AND spatial_home_unblocked IS NULL AND spatial_coverage_status='unavailable')),
    PRIMARY KEY(season,game_id),
    CHECK(away_team_id != home_team_id),
    CHECK(personal_known_excluded_seconds - known_excluded_seconds = included_seconds - personal_included_seconds),
    CHECK((included_seconds > 0 AND away_attempts IS NOT NULL AND home_attempts IS NOT NULL AND coverage_status IN ('complete','partial'))
       OR (included_seconds = 0 AND away_attempts IS 0 AND home_attempts IS 0 AND coverage_status='complete')
       OR (included_seconds = 0 AND away_attempts IS NULL AND home_attempts IS NULL AND coverage_status='unavailable'))
) STRICT;
CREATE TABLE player_game (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    team_id TEXT NOT NULL CHECK(team_id GLOB '[1-9]*' AND team_id NOT GLOB '*[^0-9]*'),
""" + _METRICS + """,
    PRIMARY KEY(season,player_id,game_id),
    FOREIGN KEY(season,player_id) REFERENCES player(season,player_id),
    FOREIGN KEY(season,game_id) REFERENCES game(season,game_id)
) STRICT;
CREATE TABLE player_season (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    teams_json TEXT NOT NULL CHECK(json_valid(teams_json) AND json_type(teams_json)='array'),
    listed_games INTEGER NOT NULL CHECK(listed_games BETWEEN 1 AND 9007199254740991),
    games_with_included_time INTEGER NOT NULL CHECK(games_with_included_time BETWEEN 0 AND listed_games),
    partial_games INTEGER NOT NULL CHECK(partial_games BETWEEN 0 AND listed_games),
    unavailable_games INTEGER NOT NULL CHECK(unavailable_games BETWEEN 0 AND listed_games),
""" + _METRICS + """,
    PRIMARY KEY(season,player_id),
    FOREIGN KEY(season,player_id) REFERENCES player(season,player_id)
) STRICT;
"""


_SPATIAL_SCHEMA = """
CREATE TABLE spatial_cell (
    season TEXT NOT NULL REFERENCES season(season),
    cell_id INTEGER NOT NULL CHECK(cell_id BETWEEN 0 AND 679),
    x_min REAL NOT NULL CHECK(x_min BETWEEN -100 AND 100),
    x_max REAL NOT NULL CHECK(x_max BETWEEN -100 AND 100 AND x_max=x_min+5),
    y_min REAL NOT NULL CHECK(y_min BETWEEN -42.5 AND 42.5),
    y_max REAL NOT NULL CHECK(y_max BETWEEN -42.5 AND 42.5 AND y_max=y_min+5),
    center_x REAL NOT NULL CHECK(center_x BETWEEN x_min AND x_max),
    center_y REAL NOT NULL CHECK(center_y BETWEEN y_min AND y_max),
    area_sqft REAL NOT NULL CHECK(area_sqft>0 AND area_sqft<=25.0000000001),
    league_count INTEGER CHECK(league_count BETWEEN 0 AND 9007199254740991),
    league_raw_per60 REAL CHECK(league_raw_per60 BETWEEN 0 AND 1.7976931348623157e308),
    league_density REAL CHECK(league_density BETWEEN 0 AND 1.7976931348623157e308),
    PRIMARY KEY(season,cell_id),
    CHECK((league_count IS NULL AND league_raw_per60 IS NULL AND league_density IS NULL)
       OR (league_count IS NOT NULL AND ((league_raw_per60 IS NULL AND league_density IS NULL) OR (league_raw_per60 IS NOT NULL AND league_density IS NOT NULL))))
) STRICT;
CREATE TABLE player_game_spatial (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    cell_id INTEGER NOT NULL,
    for_count INTEGER NOT NULL CHECK(for_count BETWEEN 0 AND 9007199254740991),
    against_count INTEGER NOT NULL CHECK(against_count BETWEEN 0 AND 9007199254740991),
    PRIMARY KEY(season,player_id,game_id,cell_id),
    FOREIGN KEY(season,player_id,game_id) REFERENCES player_game(season,player_id,game_id),
    FOREIGN KEY(season,cell_id) REFERENCES spatial_cell(season,cell_id),
    CHECK(for_count>0 OR against_count>0)
) STRICT;
CREATE INDEX player_game_spatial_game ON player_game_spatial(season,game_id);
CREATE INDEX player_game_game ON player_game(season,game_id);
CREATE TABLE player_season_spatial (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    cell_id INTEGER NOT NULL,
    for_count INTEGER NOT NULL CHECK(for_count BETWEEN 0 AND 9007199254740991),
    against_count INTEGER NOT NULL CHECK(against_count BETWEEN 0 AND 9007199254740991),
    for_raw_per60 REAL NOT NULL CHECK(for_raw_per60 BETWEEN 0 AND 1.7976931348623157e308),
    against_raw_per60 REAL NOT NULL CHECK(against_raw_per60 BETWEEN 0 AND 1.7976931348623157e308),
    for_density REAL NOT NULL CHECK(for_density BETWEEN 0 AND 1.7976931348623157e308),
    against_density REAL NOT NULL CHECK(against_density BETWEEN 0 AND 1.7976931348623157e308),
    for_difference REAL NOT NULL CHECK(for_difference BETWEEN -1.7976931348623157e308 AND 1.7976931348623157e308),
    against_difference REAL NOT NULL CHECK(against_difference BETWEEN -1.7976931348623157e308 AND 1.7976931348623157e308),
    PRIMARY KEY(season,player_id,cell_id),
    FOREIGN KEY(season,player_id) REFERENCES player_season(season,player_id),
    FOREIGN KEY(season,cell_id) REFERENCES spatial_cell(season,cell_id)
) STRICT;
"""


def _validate_spatial(metrics, on_ice, loc):
    seconds, excluded = metrics["included_seconds"], metrics["known_excluded_seconds"]
    reasons = metrics["reason_codes"]
    counts = [metrics[k] for k in ("unblocked_for", "unblocked_against")]
    rates = [metrics[k] for k in ("for_per60", "against_per60")]
    require(list(reasons) == sorted(set(reasons)) and set(reasons) <= SPATIAL_REASON_CODES, f"{loc}: invalid spatial reasons")
    require(all(type(v) is int and 0 <= v <= 9007199254740991 for v in (seconds,excluded)), f"{loc}: invalid spatial seconds")
    require(seconds <= on_ice["included_seconds"] and excluded == on_ice["known_excluded_seconds"] + on_ice["included_seconds"] - seconds,
            f"{loc}: invalid spatial support")
    require(set(on_ice["reason_codes"]) - {"no_5v5_exposure"} <= set(reasons), f"{loc}: missing inherited spatial reasons")
    require(all(v is None or type(v) is int and 0 <= v <= 9007199254740991 for v in counts), f"{loc}: invalid spatial counts")
    require(all(v is None or type(v) in (int,float) and math.isfinite(v) and v >= 0 for v in rates), f"{loc}: invalid spatial rates")
    gaps = set(reasons) - {"no_spatial_5v5_exposure"}
    if seconds:
        valid = (all(v is not None for v in counts+rates) and "no_spatial_5v5_exposure" not in reasons
            and metrics["coverage_status"] == ("partial" if gaps else "complete")
            and all(rate == 3600*count/seconds for count,rate in zip(counts,rates)))
    elif gaps:
        valid = all(v is None for v in counts+rates) and metrics["coverage_status"] == "unavailable" and "no_spatial_5v5_exposure" not in reasons
    else:
        valid = counts == [0,0] and rates == [None,None] and metrics["coverage_status"] == "complete" and reasons == ("no_spatial_5v5_exposure",)
    require(valid and (metrics["coverage_status"] != "complete" or excluded == 0), f"{loc}: inconsistent spatial projection")


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


def _selection(selection_path):
    """decode the bounded publication selection, independently of research selections."""
    path = Path(selection_path).resolve(strict=True)
    data = path.read_bytes()
    value = strict_json(data)
    require(type(value) is dict and set(value) == {"schema_version", "purpose", "corpora"},
            "observed selection requires exactly schema_version, purpose and corpora")
    require(type(value["schema_version"]) is int and value["schema_version"] == 1,
            "observed selection requires schema 1")
    require(value["purpose"] in ("real", "fixture"), "observed selection requires real or fixture purpose")
    corpora = value["corpora"]
    require(type(corpora) is list and 1 <= len(corpora) <= 3, "observed selection requires one to three corpora")
    seasons, paths = [], []
    for item in corpora:
        require(type(item) is dict and set(item) == {"season", "path", "sha256"},
                "observed corpus selection requires exactly season, path and sha256")
        season = item["season"]
        require(type(season) is str and re.fullmatch(r"[1-9][0-9]{7}", season)
                and int(season[4:]) == int(season[:4]) + 1
                and season in ("20232024", "20242025", "20252026"), "unsupported observed season")
        corpus_path = linked_path({"path": item["path"], "sha256": item["sha256"]})
        seasons.append(season)
        paths.append(corpus_path)
    require(seasons == sorted(set(seasons)), "observed seasons must be ascending and unique")
    require(len(set(paths)) == len(paths), "observed corpus paths must resolve to distinct files")
    if value["purpose"] == "real":
        require(seasons == ["20232024", "20242025", "20252026"], "real observed publication requires all three declared seasons")
    return path, data, value, paths


def _stored(row, season):
    fields = dict(row) if isinstance(row, dict) else asdict(row)
    if "attempts_for" in fields:
        expected = asdict(_metrics(fields["included_seconds"], fields["known_excluded_seconds"],
            fields["attempts_for"] or 0, fields["attempts_against"] or 0, fields["reason_codes"]))
        require(all(fields[key] == value for key, value in expected.items()), f"{season}: inconsistent on-ice metrics")
    for family, validate in (("spatial", _validate_spatial), ("personal", _validate_personal)):
        if family in fields:
            metrics = fields.pop(family)
            validate(metrics, fields, f"{season}: {family}")
            fields.update({family + "_" + key: value for key, value in metrics.items()})
    for field in ("name_source", "position_source", "teams", "reason_codes", "personal_reason_codes", "spatial_reason_codes"):
        if field in fields:
            value = fields.pop(field)
            fields[field + "_json"] = None if value is None else json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":"))
    if "horizon_unavailable" in fields:
        fields["horizon_unavailable"] = int(fields["horizon_unavailable"])
    for field, value in fields.items():
        if type(value) is int:
            require(abs(value) <= 9007199254740991, f"{season}.{field}: unsafe integer")
        elif type(value) is float:
            require(math.isfinite(value), f"{season}.{field}: nonfinite number")
    return {"season": season, **fields}


def _insert(connection, table, row):
    connection.execute(f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join('?' for _ in row)})", tuple(row.values()))


def _check_season(connection, result, purpose):
    """independently reduce stored facts within one season, one game/player at a time."""
    season = result.season
    connection.row_factory = sqlite3.Row
    require(connection.execute("SELECT count(*) FROM player WHERE season=?", (season,)).fetchone()[0]
            == connection.execute("SELECT count(*) FROM player_season WHERE season=?", (season,)).fetchone()[0],
            f"{season}: player/summary rows differ")
    require(not connection.execute("""SELECT 1 FROM player_game p JOIN game g USING(season,game_id)
        WHERE p.season=? AND p.team_id NOT IN(g.away_team_id,g.home_team_id) LIMIT 1""", (season,)).fetchall(),
        f"{season}: player team absent from game")
    seconds = exposure = attempts = for_count = against_count = personal_seconds = personal_exposure = 0
    league_counts = {}
    receipt_by_game = {row["game_id"]: row for row in result.receipt["games"]}
    for game in connection.execute("SELECT * FROM game WHERE season=? ORDER BY game_id", (season,)):
        gid = game["game_id"]
        rows = connection.execute("SELECT * FROM player_game WHERE season=? AND game_id=?", (season, gid)).fetchall()
        physical_attempts = (game["away_attempts"] or 0) + (game["home_attempts"] or 0)
        player_seconds = sum(r["included_seconds"] for r in rows)
        player_for = sum(r["attempts_for"] or 0 for r in rows)
        player_against = sum(r["attempts_against"] or 0 for r in rows)
        require(player_seconds == 10 * game["included_seconds"] and player_for == player_against == 5 * physical_attempts,
                f"{season}/{gid}: stored physical conservation failed")
        personal_player_seconds = sum(r["personal_included_seconds"] for r in rows)
        require(personal_player_seconds == 10 * game["personal_included_seconds"], f"{season}/{gid}: personal exposure differs")
        credits = receipt_by_game[gid].get("personal_identities", {}).get("skater_credits", {})
        for field in ("shots_on_goal", "goals", "primary_assists"):
            require(sum(r["personal_" + field] or 0 for r in rows) == credits.get(field, 0),
                    f"{season}/{gid}: stored personal {field} differs from source credit")
        sparse = connection.execute("SELECT * FROM player_game_spatial WHERE season=? AND game_id=?", (season, gid)).fetchall()
        physical_cells = {(r["team_id"], r["cell_id"]): r["count"] for r in receipt_by_game[gid].get("spatial_team_cells", [])}
        for (_, cell_id), count in physical_cells.items():
            league_counts[cell_id] = league_counts.get(cell_id, 0) + count
        for team, field in ((game["away_team_id"], "spatial_away_unblocked"), (game["home_team_id"], "spatial_home_unblocked")):
            require(sum(count for (team_id, _), count in physical_cells.items() if team_id == team) == (game[field] or 0),
                    f"{season}/{gid}: spatial physical team total differs")
        teams = {r["player_id"]: r["team_id"] for r in rows}
        team_cells = {}
        player_cells = {}
        for cell in sparse:
            key = (teams[cell["player_id"]], cell["cell_id"])
            totals = team_cells.setdefault(key, [0, 0])
            totals[0] += cell["for_count"]
            totals[1] += cell["against_count"]
            totals = player_cells.setdefault(cell["player_id"], [0, 0])
            totals[0] += cell["for_count"]
            totals[1] += cell["against_count"]
        opponents = {game["away_team_id"]: game["home_team_id"], game["home_team_id"]: game["away_team_id"]}
        for (team, cell_id), counts in team_cells.items():
            require(counts == [5 * physical_cells.get((team, cell_id), 0), 5 * physical_cells.get((opponents[team], cell_id), 0)],
                    f"{season}/{gid}: spatial team-cell conservation failed")
        require(sum(r["spatial_included_seconds"] for r in rows) == 10 * game["spatial_included_seconds"]
                and sum(c[0] for c in team_cells.values()) == sum(c[1] for c in team_cells.values()) == 5 * sum(physical_cells.values()),
                f"{season}/{gid}: spatial physical conservation failed")
        for row in rows:
            require(player_cells.get(row["player_id"], [0, 0]) == [row["spatial_unblocked_for"] or 0, row["spatial_unblocked_against"] or 0],
                    f"{season}/{gid}: sparse cells differ from player-game counts")
        seconds += game["included_seconds"]
        exposure += player_seconds
        attempts += physical_attempts
        for_count += player_for
        against_count += player_against
        personal_seconds += game["personal_included_seconds"]
        personal_exposure += personal_player_seconds
    references = {r["cell_id"]: r for r in connection.execute("SELECT * FROM spatial_cell WHERE season=? ORDER BY cell_id", (season,))}
    support = result.spatial_coverage
    require(len(references) == 668 and sum(r["league_count"] or 0 for r in references.values()) == (support["unblocked_attempts"] or 0),
            f"{season}: physical league spatial counts differ")
    league_mass = 0.0
    for cell in references.values():
        expected_count = league_counts.get(cell["cell_id"], 0) if support["included_seconds"] or support["coverage_status"] == "complete" else None
        require(cell["league_count"] == expected_count, f"{season}: league cell differs from physical game cells")
        if support["included_seconds"]:
            require(cell["league_raw_per60"] == 3600 * cell["league_count"] / (2 * support["included_seconds"]),
                    f"{season}: league cell rate differs")
            league_mass += cell["league_density"] * cell["area_sqft"] / 100
    require(math.isclose(league_mass, support["unblocked_per60"] or 0, rel_tol=1e-10, abs_tol=1e-10),
            f"{season}: league reference normalization differs")
    for summary in connection.execute("SELECT * FROM player_season WHERE season=? ORDER BY player_id", (season,)):
        pid = summary["player_id"]
        rows = connection.execute("SELECT * FROM player_game WHERE season=? AND player_id=?", (season, pid)).fetchall()
        require(rows and summary["listed_games"] == len(rows)
                and summary["games_with_included_time"] == sum(r["included_seconds"] > 0 for r in rows)
                and summary["partial_games"] == sum(r["coverage_status"] == "partial" for r in rows)
                and summary["unavailable_games"] == sum(r["coverage_status"] == "unavailable" for r in rows),
                f"{season}/{pid}: summary game frequencies differ")
        for prefix, names, no_exposure in (
            ("", ("attempts_for", "attempts_against"), "no_5v5_exposure"),
            ("personal_", ("shots_on_goal", "goals", "primary_assists"), "no_personal_5v5_exposure"),
            ("spatial_", ("unblocked_for", "unblocked_against"), "no_spatial_5v5_exposure"),
        ):
            for field in ("included_seconds", "known_excluded_seconds", *names):
                key = prefix + field
                require(summary[key] is None or summary[key] == sum(r[key] or 0 for r in rows),
                        f"{season}/{pid}: {key} reduction failed")
            reasons = set().union(*(json.loads(r[prefix + "reason_codes_json"]) for r in rows)) - {no_exposure}
            if result.coverage["games_with_unassigned_player_associations"]:
                reasons.add("unassigned_player_games")
            if summary[prefix + "included_seconds"] == 0 and (not reasons or prefix == "personal_"):
                reasons.add(no_exposure)
            require(json.loads(summary[prefix + "reason_codes_json"]) == sorted(reasons),
                    f"{season}/{pid}: {prefix}summary reasons differ")
        dense = connection.execute("SELECT * FROM player_season_spatial WHERE season=? AND player_id=? ORDER BY cell_id", (season, pid)).fetchall()
        require(len(dense) == (668 if summary["spatial_included_seconds"] else 0), f"{season}/{pid}: dense spatial support differs")
        sparse = {r["cell_id"]: (r["f"], r["a"]) for r in connection.execute("""SELECT cell_id,sum(for_count) f,sum(against_count) a
            FROM player_game_spatial WHERE season=? AND player_id=? GROUP BY cell_id""", (season, pid))}
        masses = [0.0, 0.0, 0.0, 0.0]
        for cell in dense:
            reference = references[cell["cell_id"]]
            require((cell["for_count"], cell["against_count"]) == sparse.get(cell["cell_id"], (0, 0)),
                    f"{season}/{pid}: dense/sparse count reduction differs")
            for side in ("for", "against"):
                require(cell[side + "_raw_per60"] == 3600 * cell[side + "_count"] / summary["spatial_included_seconds"]
                        and cell[side + "_difference"] == cell[side + "_density"] - reference["league_density"],
                        f"{season}/{pid}: spatial rate/reference differs")
            for i, field in enumerate(("for_density", "against_density", "for_difference", "against_difference")):
                masses[i] += cell[field] * reference["area_sqft"] / 100
        if dense:
            expected = [summary["spatial_for_per60"], summary["spatial_against_per60"],
                        summary["spatial_for_per60"] - result.spatial_coverage["unblocked_per60"],
                        summary["spatial_against_per60"] - result.spatial_coverage["unblocked_per60"]]
            require(all(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10) for a, b in zip(masses, expected)),
                    f"{season}/{pid}: spatial mass conservation failed")
    require(purpose != "real" or seconds > 0, f"{season}: real publication needs supported positive exposure")
    return dict(physical_seconds=seconds, player_seconds=exposure, physical_attempts=attempts,
                player_attempts_for=for_count, player_attempts_against=against_count,
                personal_physical_seconds=personal_seconds, personal_player_seconds=personal_exposure,
                read_back="passed", conservation="passed")


def build_publication(selection_path: Path, output: Path) -> dict:
    """finalize after each season's independent read-back and the complete database checks."""
    started = time.monotonic()
    selection_path, selection_bytes, selection, paths = _selection(selection_path)
    output = output.absolute()
    require(not output.exists() and not output.is_symlink(), f"{output}: output already exists")
    parent = output.parent.resolve(strict=True)
    require(parent.is_dir(), f"{parent}: output parent must be a directory")
    output = parent / output.name
    require(all(not output.is_relative_to(path.parent) for path in paths), "output must be outside every input corpus directory")
    output.mkdir()
    with (output / "selection.json").open("xb") as destination:
        destination.write(selection_bytes)
    producer = implementation_identity() | {
        "spatial_consumed_fields": ["interpreted.events.reported_x", "interpreted.events.reported_y", "interpreted.events.home_team_defending_side",
            "reconstruction.events.attacking_x", "reconstruction.events.attacking_y", "reconstruction.events.coordinate_status"],
        "sqlite_version": sqlite3.sqlite_version,
    }
    publication_id = str(uuid.uuid4())
    metadata = {
        "id": 1, "schema_version": 5, "kind": "observed_5v5", "publication_id": publication_id,
        "purpose": selection["purpose"], "game_type": 2,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "population_version": "matched_attempts_v2", "personal_population_version": "matched_personal_credits_v2",
        "spatial_population_version": POPULATION_VERSION, "spatial_display_version": DISPLAY_VERSION,
        "producer_json": json.dumps(producer, allow_nan=False, sort_keys=True, separators=(",", ":")),
    }
    incomplete = output / "observed.sqlite.incomplete"
    connection = sqlite3.connect(incomplete)
    season_receipts = []
    consumed_bytes = 0
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.executescript(_SCHEMA + _SPATIAL_SCHEMA)
        connection.execute("PRAGMA user_version=5")
        with connection:
            _insert(connection, "publication", metadata)
        for item, corpus_path in zip(selection["corpora"], paths):
            season_started = time.monotonic()
            result = aggregate(corpus_path, selection["purpose"], item["season"], item["sha256"])
            evidence = {"season": result.season, "corpus_sha256": result.corpus_sha256,
                "source_requested_min": result.source_requested_min, "source_requested_max": result.source_requested_max,
                "undated_sources": result.undated_sources,
                "coverage_json": json.dumps(result.coverage, allow_nan=False, sort_keys=True, separators=(",", ":")),
                "spatial_coverage_json": json.dumps(result.spatial_coverage, allow_nan=False, sort_keys=True, separators=(",", ":")),
                "source_implementations_json": json.dumps(result.source_implementations, allow_nan=False, sort_keys=True, separators=(",", ":"))}
            tables = (("player", result.players), ("game", result.games), ("player_game", result.player_games),
                ("player_season", result.player_seasons), ("spatial_cell", result.spatial_cells),
                ("player_game_spatial", result.player_game_spatial), ("player_season_spatial", result.player_season_spatial))
            with connection:
                _insert(connection, "season", evidence)
                for table, rows in tables:
                    for row in rows:
                        _insert(connection, table, _stored(row, result.season))
            with closing(sqlite3.connect(incomplete.as_uri() + "?mode=ro", uri=True)) as readback:
                readback.row_factory = sqlite3.Row
                require(dict(readback.execute("SELECT * FROM season WHERE season=?", (result.season,)).fetchone()) == evidence,
                        f"{result.season}: season evidence read-back differs")
                for table, rows in tables:
                    cursor = readback.execute(f"SELECT * FROM {table} WHERE season=? ORDER BY rowid", (result.season,))
                    for row in rows:
                        actual = cursor.fetchone()
                        require(actual is not None and dict(actual) == _stored(row, result.season), f"{result.season}/{table}: read-back differs")
                    require(cursor.fetchone() is None, f"{result.season}/{table}: extra stored rows")
                checks = _check_season(readback, result, selection["purpose"])
            season_output = output / "seasons" / result.season
            season_output.mkdir(parents=True)
            season_verification = {"schema_version": 1, "kind": "observed_season_verification",
                "publication_id": publication_id, "purpose": selection["purpose"], "season": result.season,
                "corpus_sha256": result.corpus_sha256, "producer": producer,
                "source_implementations": list(result.source_implementations), **result.receipt,
                "coverage": result.coverage, "spatial_coverage": result.spatial_coverage, "checks": checks,
                "wall_seconds": time.monotonic() - season_started, "scientific_admission": "not_performed"}
            receipt_path = season_output / "verification.json"
            write_json(receipt_path, season_verification)
            with receipt_path.open("rb") as source:
                receipt_digest = hashlib.file_digest(source, "sha256").hexdigest()
            season_receipts.append({"season": result.season, "receipt": {"path": str(receipt_path.relative_to(output)), "sha256": receipt_digest},
                "corpus_sha256": result.corpus_sha256,
                "coverage": {key: value for key, value in result.coverage.items() if key not in ("unassigned_games", "reason_game_counts")},
                "spatial_coverage": result.spatial_coverage, "checks": checks})
            consumed_bytes += sum(Path(row["path"]).stat().st_size for row in result.receipt["consumed"])
            del result, tables, rows, season_verification
        connection.close()
        connection = sqlite3.connect(incomplete.as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        require([tuple(r) for r in connection.execute("PRAGMA integrity_check")] == [("ok",)], "sqlite integrity check failed")
        require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "sqlite foreign key check failed")
        require(connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete", "publication requires delete journal mode")
        require(connection.execute("PRAGMA user_version").fetchone()[0] == 5, "publication requires schema 5")
        require(dict(connection.execute("SELECT * FROM publication").fetchone()) == metadata, "publication metadata read-back differs")
        require([r[0] for r in connection.execute("SELECT season FROM season ORDER BY season")] == [r["season"] for r in selection["corpora"]],
                "stored season catalog differs")
        require({r[1] for r in connection.execute("PRAGMA table_list") if r[2] == "table" and r[0] == "main" and not r[1].startswith("sqlite_")}
                == {"publication", "season", "player", "game", "player_game", "player_season", "spatial_cell", "player_game_spatial", "player_season_spatial"},
                "publication table structure differs")
    finally:
        connection.close()
    with incomplete.open("rb") as source:
        database_sha256 = hashlib.file_digest(source, "sha256").hexdigest()
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    verification = {"schema_version": 1, "kind": "observed_publication_verification", "publication_id": publication_id,
        "purpose": selection["purpose"], "producer": producer,
        "selection": {"path": str(selection_path), "sha256": hashlib.sha256(selection_bytes).hexdigest(),
            "bytes": len(selection_bytes), "copy": "selection.json", "document": selection},
        "seasons": season_receipts, "database": {"path": str(output / "observed.sqlite"), "sha256": database_sha256},
        "checks": {"integrity": "passed", "foreign_keys": "passed", "read_back": "passed", "per_season_conservation": "passed"},
        "cost": {"wall_seconds": time.monotonic() - started, "peak_rss_bytes": rss if sys.platform == "darwin" else rss * 1024,
            "consumed_bytes": consumed_bytes, "database_bytes": incomplete.stat().st_size},
        "cost_scope": "through independent read-back; top receipt writing and final rename excluded; peak rss is process high-water",
        "scientific_admission": "not_performed"}
    write_json(output / "verification.json", verification)
    incomplete.rename(output / "observed.sqlite")
    return verification
