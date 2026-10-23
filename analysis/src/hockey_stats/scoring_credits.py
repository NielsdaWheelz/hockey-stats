"""located personal scoring credits from the envelope's bound original captures."""

from collections import Counter
import hashlib
from pathlib import Path

from .captures import read_capture, strict_json
from .corpus_inputs import IDENTITY_FIELDS, require
from .interpret import game_identity, clock_seconds
from .reconstruct import goal_identity_status


def _positive(value):
    return value if type(value) is int and value > 0 else None


def actor_issue(event, identities, role_teams, membership=None):
    """check recorded actor identities against explicit team/member contracts.

    callers own population, association and interval exclusions. optional
    assists deliberately do not enter this actor-only check.
    """
    actors = []
    for role, team in role_teams.items():
        player = event["roles"].get(role)
        identity = identities.get(player)
        if _positive(player) is None or identity is None:
            return role + "_identity_unavailable"
        if team is None or identity["team_id"] != team:
            return role + "_team_conflict"
        if membership is not None and player not in membership.get(team, ()):
            return role + "_membership_conflict"
        actors.append(player)
    if len(set(actors)) != len(actors):
        return "actor_identity_conflict"
    return None


def _bound_sources(document, consumed):
    bodies, references = {}, {}
    for source in ("play-by-play", "landing"):
        bound = next(row for row in document["inputs"] if row["source"] == source)
        path = Path(bound["capture_path"])
        require(path.name == "capture.json" and path.parent.name == source, path, "contradictory capture locator")
        capture = read_capture(path.parent.parent, source)
        require(capture.capture_path == path.resolve(), path, "capture locator differs")
        require((capture.requested_at, capture.http_status, capture.body_sha256)
                == (bound["requested_at"], bound["http_status"], bound["body_sha256"]),
                path, "capture differs from frozen input")
        promised = bound["requested_at"] is not None or bound["body_sha256"] is not None or bound["status"] == "parsed"
        require(not promised or path.is_file(), path, "promised capture receipt is missing")
        require(capture.requested_game_id in (None, document["game"]["game_id"]), path, "capture game identity differs")
        if path.is_file():
            consumed.append(dict(kind="scoring-credit-capture", path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        if capture.body_sha256 is not None:
            consumed.append(dict(kind="scoring-credit-body", path=str(path.parent / "body.bin"), sha256=capture.body_sha256))
        references[source] = dict(source=source, capture_path=str(path), body_sha256=capture.body_sha256)
        if bound["status"] != "parsed":
            continue
        require(capture.body is not None, path, "parsed source body unavailable")
        try:
            body = strict_json(capture.body)
        except (ValueError, UnicodeDecodeError) as error:
            require(False, path, f"parsed source no longer decodes: {error}")
        require(type(body) is dict, path, "parsed source is not an object")
        identity, reason = game_identity(body, document["game"]["game_id"])
        require(identity is not None and all(identity[key] == document["game"][key] for key in IDENTITY_FIELDS),
                path, f"parsed source game identity differs: {reason}")
        bodies[source] = body
    return bodies, references


def scoring_credits(document, selected, identities, consumed, *, factual=False):
    """return one credit disposition per already included scored/saved event.

    derived/raw drift is an input error; conflicting source observations are
    unresolved credit. callers own event strength, segment assignment and masks.
    """
    bodies, references = _bound_sources(document, consumed)
    plays = bodies.get("play-by-play", {}).get("plays")
    require(not selected or type(plays) is list, "scoring credits", "included events lack parsed plays")
    event_ids = Counter(row.get("eventId") for row in plays or [] if type(row) is dict and _positive(row.get("eventId")) is not None)
    landing = {}
    raw_goals = {}
    landing_body = bodies.get("landing")
    require(factual and document["landing_goals"] is None
            or (document["landing_goals"] is not None) == (landing_body is not None),
            "landing", "derived goal collection availability differs from bound source")
    if document["landing_goals"] is not None:
        summary = landing_body.get("summary") if landing_body is not None else None
        scoring = summary.get("scoring") if type(summary) is dict else None
        require(type(scoring) is list and all(type(period) is dict and type(period.get("goals")) is list for period in scoring),
                "landing", "derived goal collection lacks raw scoring collection")
        expected_paths = {f"/summary/scoring/{p}/goals/{g}" for p, period in enumerate(scoring) for g in range(len(period["goals"]))}
        require({goal["source_path"] for goal in document["landing_goals"]} == expected_paths
                and len(document["landing_goals"]) == len(expected_paths), "landing", "derived goal collection differs from raw scoring collection")
    for goal in document["landing_goals"] or []:
        path = goal["source_path"]
        parts = path.split("/")
        require(len(parts) == 6 and parts[:3] == ["", "summary", "scoring"] and parts[4] == "goals"
                and parts[3].isdigit() and parts[5].isdigit(), path, "invalid derived goal locator")
        body = bodies.get("landing")
        require(body is not None, path, "derived landing goal lacks parsed bound source")
        scoring = body.get("summary", {}).get("scoring") if type(body.get("summary")) is dict else None
        require(type(scoring) is list and int(parts[3]) < len(scoring), path, "derived goal period locator differs")
        period = scoring[int(parts[3])]
        require(type(period) is dict and type(period.get("goals")) is list and int(parts[5]) < len(period["goals"]), path, "derived goal locator differs")
        raw = period["goals"][int(parts[5])]
        raw = raw if type(raw) is dict else {}
        descriptor = period.get("periodDescriptor")
        descriptor = descriptor if type(descriptor) is dict else {}
        home = raw.get("isHome")
        team = document["game"]["home_team_id"] if home is True else document["game"]["away_team_id"] if home is False else None
        expected = dict(event_id=_positive(raw.get("eventId")), period_number=_positive(descriptor.get("number")),
                        period_type=descriptor.get("periodType") if type(descriptor.get("periodType")) is str else None,
                        time_in_period=raw.get("timeInPeriod") if type(raw.get("timeInPeriod")) is str else None,
                        team_id=team, credited_scorer_id=_positive(raw.get("playerId")))
        require(all(type(goal[key]) is type(value) and goal[key] == value for key, value in expected.items()), path, "derived goal identity differs from raw fields")
        elapsed = clock_seconds(expected["time_in_period"], "landing", path + "/timeInPeriod", [])
        length = 1200 if expected["period_type"] == "REG" and expected["period_number"] in (1, 2, 3) else 300 if expected["period_type"] == "OT" and expected["period_number"] == 4 else None
        expected_elapsed = elapsed if elapsed is not None and length is not None and elapsed <= length else None
        require(goal["elapsed_seconds"] == expected_elapsed, path, "derived goal clock differs from raw fields")
        require(path not in raw_goals, path, "duplicate derived goal locator")
        raw_goals[path] = raw
        if goal["event_id"] is not None:
            landing.setdefault(goal["event_id"], []).append(goal)
    records = []
    for event in selected:
        index = event["source_index"]
        path = f"/plays/{index}"
        require(index < len(plays) and type(plays[index]) is dict, path, "derived event locator differs")
        raw = plays[index]
        details = raw.get("details")
        require(factual or type(details) is dict, path, "included event lacks raw details")
        details = details if type(details) is dict else {}
        descriptor = raw.get("periodDescriptor")
        require(factual or type(descriptor) is dict, path, "included event lacks raw period descriptor")
        descriptor = descriptor if type(descriptor) is dict else {}
        expected = dict(event_id=raw.get("eventId"), type_code=raw.get("typeCode"), type_key=raw.get("typeDescKey"),
                        period_number=descriptor.get("number"), period_type=descriptor.get("periodType"),
                        time_in_period=raw.get("timeInPeriod"),
                        time_remaining=raw.get("timeRemaining") if type(raw.get("timeRemaining")) is str else None,
                        situation_code=raw.get("situationCode") if type(raw.get("situationCode")) is str else None, owner_team_id=_positive(details.get("eventOwnerTeamId")))
        if factual:
            expected.update(event_id=_positive(raw.get("eventId")),
                            period_number=_positive(descriptor.get("number")),
                            period_type=descriptor.get("periodType") if type(descriptor.get("periodType")) is str else None,
                            time_in_period=raw.get("timeInPeriod") if type(raw.get("timeInPeriod")) is str else None)
        require(all(type(event[key]) is type(value) and event[key] == value for key, value in expected.items()),
                path, "derived event identity differs from raw fields")
        expected_clock = None if factual and event["timed_period"] is False else clock_seconds(event["time_in_period"], "play-by-play", path + "/timeInPeriod", [])
        require(event["elapsed_seconds"] == expected_clock,
                path, "derived event clock differs from raw fields")
        role = "scorer" if event["type_key"] == "goal" else "shooter"
        role_fields = {role: "scoringPlayerId" if role == "scorer" else "shootingPlayerId", "assist1": "assist1PlayerId", "assist2": "assist2PlayerId"}
        for name, field in role_fields.items():
            require((name in event["roles"]) == (field in details) and event["roles"].get(name) == _positive(details.get(field)),
                    path + "/details/" + field, "derived role differs from raw field")
        scorer = event["roles"].get(role)
        team_matches = scorer not in identities or identities[scorer]["team_id"] == event["shooting_team_id"]
        require(factual or team_matches, path, "derived scorer/shooter team differs from roster")
        refs = [dict(**references["play-by-play"], field=path + field) for field in (
            "/eventId", "/typeDescKey", "/typeCode", "/periodDescriptor", "/timeInPeriod", "/details/" + role_fields[role])]
        record = dict(source_index=index, status="credited", scorer_or_shooter_id=scorer,
                      primary_assister_id=None, evidence_refs=refs, reason=None)
        records.append(record)
        if scorer not in identities or not team_matches:
            record.update(status="unresolved", reason="scorer_or_shooter_identity_unavailable" if team_matches else "scorer_or_shooter_team_conflict")
            continue
        if role != "scorer":
            continue
        matches = landing.get(event["event_id"], [])
        refs.extend(dict(**references["play-by-play"], field=path + "/details/" + field) for field in ("assist1PlayerId", "assist2PlayerId"))
        if event_ids[event["event_id"]] != 1 or len(matches) != 1:
            record.update(status="unresolved", reason="goal_identity_unavailable")
            refs.append(dict(**references["landing"], field="/summary/scoring"))
            continue
        goal = matches[0]
        goal_path = goal["source_path"]
        refs.extend(dict(**references["landing"], field=field) for field in (
            goal_path + "/eventId", goal_path + "/playerId", goal_path + "/isHome", goal_path + "/timeInPeriod",
            goal_path.rsplit("/goals/", 1)[0] + "/periodDescriptor", goal_path + "/assists"))
        identity_status = goal_identity_status(event, goal, document["issues"])
        if identity_status != "matched":
            record.update(status="unresolved", reason="goal_identity_" + identity_status)
            continue
        raw_goal = raw_goals[goal_path]
        # an explicitly supplied abbreviation must corroborate the scoring team.
        if "teamAbbrev" in raw_goal:
            abbreviation = raw_goal["teamAbbrev"]
            expected_abbreviation = document["game"]["home_team_abbrev" if raw_goal.get("isHome") is True else "away_team_abbrev"]
            if type(abbreviation) is not dict or type(abbreviation.get("default")) is not str or expected_abbreviation is None or abbreviation["default"] != expected_abbreviation:
                record.update(status="unresolved", reason="goal_identity_conflict")
                continue
        play_assists = [details[field] for field in ("assist1PlayerId", "assist2PlayerId") if field in details]
        landing_assists = raw_goal.get("assists")
        valid = (not ("assist2PlayerId" in details and "assist1PlayerId" not in details)
                 and type(landing_assists) is list and len(landing_assists) <= 2
                 and all(type(row) is dict for row in landing_assists or []))
        landing_ids = [row.get("playerId") for row in landing_assists] if valid else []
        for ids in (play_assists, landing_ids):
            valid = valid and len(ids) <= 2 and all(_positive(pid) is not None and pid != scorer
                and pid in identities and identities[pid]["team_id"] == event["shooting_team_id"] for pid in ids)
            valid = valid and len(ids) == len(set(pid for pid in ids if type(pid) is int))
        if factual:
            primary_valid = (not ("assist2PlayerId" in details and "assist1PlayerId" not in details)
                             and type(landing_assists) is list)
            primary_landing = ([landing_assists[0].get("playerId") if type(landing_assists[0]) is dict else None]
                               if primary_valid and landing_assists else [])
            primary_play = [details["assist1PlayerId"]] if "assist1PlayerId" in details else []
            for ids in (primary_play, primary_landing):
                primary_valid = primary_valid and all(_positive(pid) is not None and pid != scorer
                    and pid in identities and identities[pid]["team_id"] == event["shooting_team_id"] for pid in ids)
            if not primary_valid:
                record.update(status="unresolved", reason="malformed_primary_assist")
            elif primary_play != primary_landing:
                record.update(status="unresolved", reason="primary_assist_conflict")
            else:
                record["primary_assister_id"] = primary_play[0] if primary_play else None
                if not valid:
                    record["reason"] = "secondary_assist_unresolved"
                elif play_assists[1:] != landing_ids[1:]:
                    record["reason"] = "secondary_assist_disagreement"
        elif not valid:
            record.update(status="unresolved", reason="malformed_assists")
        elif (play_assists[:1] != landing_ids[:1]):
            record.update(status="unresolved", reason="primary_assist_conflict")
        else:
            record["primary_assister_id"] = play_assists[0] if play_assists else None
            if play_assists[1:] != landing_ids[1:]:
                record["reason"] = "secondary_assist_disagreement"
    return records
