"""strictly earlier-date history over explicitly admitted regular inventories."""

from bisect import bisect_left
from collections import defaultdict
from datetime import date, timedelta

from .feature_data import COUNTERS, fact

_GOALIE = {"starts", "relief_appearances", "saves", "shots_against", "goals_against"}


def _season_before(season, years):
    start = int(season[:4]) - years
    return str(start) + str(start + 1)


def _prefix(rows, summaries):
    """store date-indexed compact sums and missing counts once per season."""
    dates = sorted({row["game_date"] for row in rows})
    index = {day: i for i, day in enumerate(dates)}
    players = defaultdict(lambda: {
        "rows": [], "dates": [], "known": {field: [0] for field in COUNTERS},
        "missing": {field: [0] for field in COUNTERS},
        "appearances": [], "uncertain_appearances": [],
    })
    unknown = [0] * (len(dates) + 1)
    games = [[] for _ in dates]
    missing_games = [[] for _ in dates]
    for row in rows:
        summary = summaries.get(row["game_id"])
        position = index[row["game_date"]]
        games[position].append(row["game_id"])
        if summary is None or not summary["complete_roster"]:
            unknown[position + 1] += 1
            missing_games[position].append(row["game_id"])
        if summary is None:
            continue
        for player, values in summary["players"].items():
            players[player]["rows"].append((row["game_date"], row["game_id"], values,
                                             summary["input_ref"]))
    for i in range(len(dates)):
        unknown[i + 1] += unknown[i]
    for player, entry in players.items():
        entry["rows"].sort(key=lambda r: (r[0], r[1]))
        for day, game_id, values, input_ref in entry["rows"]:
            entry["dates"].append(day)
            participation = values["participation"]
            if participation is True:
                observation = {"game_id": game_id, "game_date": day,
                               "team_id": values["team_id"], "role": values["role"]}
                entry["appearances"].append((day, game_id, values, input_ref, observation))
            elif participation is None:
                entry["uncertain_appearances"].append(day)
            counters = values["counters"]
            for field in COUNTERS:
                value = counters["values"][field]
                known = counters["values"].get("known_" + field)
                problem = counters["problems"].get(field)
                entry["known"][field].append(entry["known"][field][-1] + (known if known is not None else 0))
                unavailable = value is None and not (problem and problem["status"] == "not_applicable")
                entry["missing"][field].append(entry["missing"][field][-1] + unavailable)
        entry["appearance_dates"] = [r[0] for r in entry["appearances"]]
    return {"dates": dates, "unknown": unknown, "games": games,
            "missing_games": missing_games, "players": dict(players),
            "inventory_evidence": {"input_ref": rows[0]["input_ref"], "source": "corpus",
                                   "path": "/reference/inventory", "season": rows[0]["season"]}}


def _bounds(index, start, cutoff):
    return bisect_left(index["dates"], start), bisect_left(index["dates"], cutoff)


def _window(scope, season_index, player, role, start, cutoff, missing_evidence):
    """a supported partial sum and a complete total are distinct values."""
    available = season_index is not None
    entry = season_index["players"].get(player) if available else None
    lo, hi = _bounds(season_index, start, cutoff) if available else (0, 0)
    unknown = season_index["unknown"][hi] - season_index["unknown"][lo] if available else 1
    plo = bisect_left(entry["dates"], start) if entry else 0
    phi = bisect_left(entry["dates"], cutoff) if entry else 0
    values, problems = {}, {}
    evidence = [season_index["inventory_evidence"] if available else missing_evidence]
    unavailable_games = set(game_id for ids in season_index["missing_games"][lo:hi] for game_id in ids) if available else set()
    if entry:
        for day, game_id, row, input_ref in entry["rows"][plo:phi]:
            evidence.extend(row["counters"]["evidence"])
            if row["participation"] is None or any(
                    field in row["counters"]["problems"] and row["counters"]["problems"][field]["status"] != "not_applicable"
                    for field in COUNTERS):
                unavailable_games.add(game_id)
    refs = list(range(len(evidence)))
    for field in COUNTERS:
        applicable = role == "G" or field not in _GOALIE
        known = entry["known"][field][phi] - entry["known"][field][plo] if entry else 0
        missing = entry["missing"][field][phi] - entry["missing"][field][plo] if entry else 0
        values["known_" + field] = known if available and applicable else None
        values[field] = known if available and applicable and not unknown and not missing else None
        if not applicable:
            problems[field] = {"status": "not_applicable" if role is not None else "unavailable", "reason": "goaltending counter for a reported skater" if role is not None else "reported role unavailable", "evidence_refs": refs}
            problems["known_" + field] = dict(problems[field])
        elif values[field] is None:
            problems[field] = {"status": "unavailable", "reason": "declared history inventory or attributed counter coverage incomplete", "evidence_refs": refs}
            if values["known_" + field] is None:
                problems["known_" + field] = dict(problems[field])
    result = {"values": values, "problems": problems, "evidence": evidence}
    result.update({
        "scope": scope, "start": start, "cutoff": cutoff,
        "complete": available and all(field not in problems or problems[field]["status"] == "not_applicable" for field in COUNTERS),
        "contributing_game_ids": [r[1] for r in entry["rows"][plo:phi] if r[2]["participation"] is True] if entry else [],
        "unavailable_game_ids": sorted(unavailable_games),
    })
    return result


def _previous_player(index, player, cutoff):
    if index is None:
        return None, True
    entry = index["players"].get(player)
    appearances = entry["appearances"] if entry else []
    appearance_dates = entry["appearance_dates"] if entry else []
    position = bisect_left(appearance_dates, cutoff)
    previous = appearances[position - 1] if position else None
    start = previous[0] if previous else "0001-01-01"
    lo, hi = _bounds(index, start, cutoff)
    unknown = index["unknown"][hi] - index["unknown"][lo] > 0
    if entry:
        uncertain = entry["uncertain_appearances"]
        unknown |= bisect_left(uncertain, cutoff) > bisect_left(uncertain, start)
    # two appearances on one prior date have no declared within-date order.
    ambiguous = previous is not None and position - bisect_left(appearance_dates, previous[0]) > 1
    return previous, unknown or ambiguous


def _player_rest(index, player, cutoff, windows, missing_evidence):
    previous, unknown = _previous_player(index, player, cutoff)
    current = date.fromisoformat(cutoff)
    prior_date = previous[0] if previous and not unknown else None
    values = {
        "prior_appearance_exists": True if previous else None if unknown else False,
        "prior_game_date": prior_date,
        "calendar_gap_days": (current - date.fromisoformat(prior_date)).days if prior_date else None,
        "prior_one_date": None, "prior_two_date": None,
        "games_days_7": windows["days_7"]["values"]["ice_appearances"],
        "games_days_14": windows["days_14"]["values"]["ice_appearances"],
    }
    entry = index["players"].get(player) if index else None
    for days, field in ((1, "prior_one_date"), (2, "prior_two_date")):
        day = (current - timedelta(days=days)).isoformat()
        following = (current - timedelta(days=days - 1)).isoformat()
        if index is not None:
            lo, hi = _bounds(index, day, following)
            unknown_day = index["unknown"][hi] > index["unknown"][lo]
            if entry:
                uncertain = entry["uncertain_appearances"]
                unknown_day |= bisect_left(uncertain, following) > bisect_left(uncertain, day)
            observed = bool(entry and bisect_left(entry["appearance_dates"], following) > bisect_left(entry["appearance_dates"], day))
            if observed or not unknown_day:
                values[field] = observed
    evidence = [index["inventory_evidence"] if index else missing_evidence]
    if previous:
        evidence.extend(previous[2]["counters"]["evidence"])
    result = fact(values, evidence, reason="player predecessor or calendar coverage left-censored")
    if not unknown and not previous:
        for field in ("prior_game_date", "calendar_gap_days"):
            result["problems"][field] = {"status": "not_applicable", "reason": "complete declared prefix has no positive-toi appearance", "evidence_refs": [0]}
    return result, previous, unknown


def _team_rest(index, cutoff, missing_evidence):
    admitted = index is not None
    stop = bisect_left(index["dates"], cutoff) if admitted else 0
    previous = index["rows"][stop - 1] if stop else None
    current = date.fromisoformat(cutoff)
    one, two = ((current - timedelta(days=days)).isoformat() for days in (1, 2))
    values = {
        "prior_game_exists": bool(previous) if admitted else None,
        "prior_game_date": previous["game_date"] if previous and admitted else None,
        "calendar_gap_days": (current - date.fromisoformat(previous["game_date"])).days if previous and admitted else None,
        "prior_one_date": bisect_left(index["dates"], cutoff) > bisect_left(index["dates"], one) if admitted else None,
        "prior_two_date": bisect_left(index["dates"], one) > bisect_left(index["dates"], two) if admitted else None,
        "games_days_7": stop - bisect_left(index["dates"], (current - timedelta(days=7)).isoformat()) if admitted else None,
        "games_days_14": stop - bisect_left(index["dates"], (current - timedelta(days=14)).isoformat()) if admitted else None,
    }
    evidence = [index["inventory_evidence"] if admitted else missing_evidence]
    if previous:
        evidence.append({"input_ref": previous["input_ref"], "source": "corpus",
                         "path": f"/reference/inventory/{previous.get('source_index', previous.get('inventory_source_index', 0))}",
                         "game_id": previous["game_id"]})
    result = fact(values, evidence,
                  reason="team regular-season inventory not admitted for history")
    if admitted and previous is None:
        for field in ("prior_game_date", "calendar_gap_days"):
            result["problems"][field] = {"status": "not_applicable", "reason": "complete declared prefix has no earlier team game", "evidence_refs": [0]}
    return result


def prepare_history(inventory_rows, summaries, target_game_ids):
    """date-prefix snapshots never consume another game on the focal date."""
    inventory = {row["game_id"]: row for row in inventory_rows}
    seasons = defaultdict(list)
    for row in inventory_rows:
        if row["history_admitted"]:
            seasons[row["season"]].append(row)
    indexes = {season: _prefix(rows, summaries) for season, rows in seasons.items()}
    teams = {}
    for season, rows in seasons.items():
        team_rows = defaultdict(list)
        for row in rows:
            for side in ("away", "home"):
                team_rows[row[side + "_team_id"]].append(row)
        for team, schedule in team_rows.items():
            schedule.sort(key=lambda r: (r["game_date"], r["game_id"]))
            teams[season, team] = {"rows": schedule, "dates": [r["game_date"] for r in schedule],
                                   "inventory_evidence": indexes[season]["inventory_evidence"]}
    prior_windows = {}
    games, players = {}, {}
    for game_id in target_game_ids:
        row = inventory[game_id]
        cutoff, season = row["game_date"], row["season"]
        current = date.fromisoformat(cutoff)
        index = indexes.get(season)
        missing_evidence = {"input_ref": row["selection_input_ref"], "source": "selection",
                            "path": "/history_corpora", "requested_season": season}
        start = index["dates"][0] if index else None
        games[game_id] = {"teams": {
            str(row[side + "_team_id"]): {"calendar_rest": _team_rest(teams.get((season, row[side + "_team_id"])), cutoff, missing_evidence)}
            for side in ("away", "home")
        }}
        summary = summaries.get(game_id)
        player_rows = {}
        for player, observation in summary["players"].items() if summary else []:
            role = observation["role"]
            windows = {
                "days_7": _window("days_7", index, player, role, max(start, (current - timedelta(days=7)).isoformat()) if index else None, cutoff, missing_evidence),
                "days_14": _window("days_14", index, player, role, max(start, (current - timedelta(days=14)).isoformat()) if index else None, cutoff, missing_evidence),
                "season_prefix": _window("season_prefix", index, player, role, start, cutoff, missing_evidence),
            }
            rest, previous, unknown = _player_rest(index, player, cutoff, windows, missing_evidence)
            if previous is not None and not unknown:
                prior_counter = previous[2]["counters"]
                previous_window = {
                    "values": dict(prior_counter["values"]),
                    "problems": dict(prior_counter["problems"]),
                    "evidence": list(prior_counter["evidence"]),
                    "scope": "previous_game", "start": previous[0], "cutoff": cutoff,
                    "complete": all(field not in prior_counter["problems"] or prior_counter["problems"][field]["status"] == "not_applicable" for field in COUNTERS),
                    "contributing_game_ids": [previous[1]], "unavailable_game_ids": [],
                }
            else:
                previous_window = _window("previous_game", None, player, role, start, cutoff, missing_evidence)
                if not unknown:
                    previous_window["evidence"] = [index["inventory_evidence"]]
                    for field in previous_window["values"]:
                        previous_window["problems"][field] = {"status": "not_applicable", "reason": "complete prefix has no previous appearance", "evidence_refs": [0]}
            windows["previous_game"] = previous_window
            history = {}
            for years in (1, 2):
                prior_season = _season_before(season, years)
                prior_index = indexes.get(prior_season)
                cache_key = (season, years, player, role)
                if cache_key not in prior_windows:
                    prerequisite = {**missing_evidence, "requested_season": prior_season}
                    prior_start = prior_index["dates"][0] if prior_index else None
                    prior_end = (date.fromisoformat(prior_index["dates"][-1]) + timedelta(days=1)).isoformat() if prior_index else None
                    prior_windows[cache_key] = _window(f"prior_season_{years}", prior_index, player, role, prior_start, prior_end, prerequisite)
                history[f"prior_season_{years}"] = prior_windows[cache_key]
            earlier = []
            unknown_earlier = False
            for historical_season in sorted(indexes):
                if historical_season > season:
                    continue
                historical_index = indexes[historical_season]
                historical_player = historical_index["players"].get(player)
                end = cutoff if historical_season == season else "9999-12-31"
                if historical_player:
                    earlier.extend(r for r in historical_player["appearances"] if r[0] < end)
                _, stop = _bounds(historical_index, "0001-01-01", end)
                unknown_earlier |= historical_index["unknown"][stop] > 0
            earlier.sort(key=lambda r: r[0])
            first = earlier[0] if earlier else None
            first_rows = [r for r in earlier if first and r[0] == first[0]]
            first_fact = fact({"game_date": first[0] if first else None,
                               "game_id": first[1] if len(first_rows) == 1 else None,
                               "game_ids": sorted(r[1] for r in first_rows)},
                              first[2]["counters"]["evidence"] if first else [missing_evidence])
            if not first:
                for field in ("game_date", "game_id"):
                    first_fact["problems"][field] = {"status": "not_applicable", "reason": "no earlier locally observed positive-toi appearance", "evidence_refs": [0]}
            elif len(first_rows) > 1:
                first_fact["problems"]["game_id"] = {"status": "unavailable", "reason": "same-date appearances have no declared within-date order", "evidence_refs": list(range(len(first_fact["evidence"])))}
            observed_dates = defaultdict(list)
            for appearance in earlier:
                observed_dates[appearance[0]].append(appearance)
            day_teams = [{r[2]["team_id"] for r in records} for records in observed_dates.values()]
            day_roles = [{r[2]["role"] for r in records} for records in observed_dates.values()]
            coherent_teams = index is not None and not unknown_earlier and all(len(group) == 1 for group in day_teams)
            coherent_roles = index is not None and not unknown_earlier and all(len(group) == 1 and None not in group for group in day_roles)
            team_sequence = [next(iter(group)) for group in day_teams if len(group) == 1]
            role_sequence = [next(iter(group)) for group in day_roles if len(group) == 1]
            identity_values = {
                "first_observed_appearance": first_fact,
                "first_observation_left_censored": unknown_earlier or _season_before(season, 2) not in indexes,
                "prior_teams": sorted({r[2]["team_id"] for r in earlier}),
                "prior_roles": sorted({r[2]["role"] for r in earlier if r[2]["role"] is not None}),
                "team_role_observations": [r[4] for r in earlier],
                "team_changes": sum(a != b for a, b in zip(team_sequence, team_sequence[1:])) if coherent_teams else None,
                "role_changes": sum(a != b for a, b in zip(role_sequence, role_sequence[1:])) if coherent_roles else None,
            }
            identity_evidence = [index["inventory_evidence"] if index else missing_evidence]
            for appearance in earlier:
                identity_evidence.extend(appearance[2]["counters"]["evidence"])
            history["identity"] = fact(identity_values, identity_evidence,
                                       reason="missing coverage, same-date team/role observations or unknown role prevent an ordered change count")
            player_rows[player] = {"workload": windows, "calendar_rest": rest, "history": history}
        players[game_id] = player_rows
    return {"games": games, "players": players}
