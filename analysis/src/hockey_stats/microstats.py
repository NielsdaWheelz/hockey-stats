"""source-matched personal counts, fixed microstat fields and honest gaps."""

from collections import Counter
from collections.abc import Iterable
from typing import TYPE_CHECKING, Literal, TypedDict

from . import analysis_records
from .analysis_publication import MICROSTATS
from .analysis_support import NON_ATTEMPT_REPORT_CODES
from .corpus_inputs import require
from .reconstruct import MEMBERSHIP_FIELDS, REPORT_CODES, roster_identities
from .scoring_credits import actor_issue
from .observed import ObservedResult

if TYPE_CHECKING:
    from .descriptive import ObservedGameReceipt, PersonIdentity, SourceIds


class ReasonCount(TypedDict):
    code: str
    count: int


class FamilyMetric(TypedDict):
    seconds: int | float
    excluded_seconds: int | float
    count: int
    opportunities: int
    reasons: list[ReasonCount]
    unquantified_gap: bool
    has_support: bool


class FamilyReduction(TypedDict):
    players: dict[str, FamilyMetric]
    issues: list[dict]
    event_dispositions: list[dict]
    inherited_reasons: list[analysis_records.SupportReason]
    masks: list[dict]


class GameReduction(TypedDict):
    season: str
    game_id: str
    families: dict[Literal["u", "h", "b"], FamilyReduction]


def _five(segment):
    members = segment["membership"]
    return all(members[key] is not None and len(members[key]) == size
               for key, size in zip(MEMBERSHIP_FIELDS, (5, 5, 1, 1)))


def reduce_game(prepared_game: analysis_records.PreparedGame,
                observed_game_receipt: "ObservedGameReceipt") -> GameReduction:
    """retain three independent matched populations and located exclusions."""
    from .descriptive import project_support

    projection = project_support(prepared_game, observed_game_receipt)
    game = prepared_game["game"]
    identity = game["identity"] or game["inventory"]
    teams = (identity["away_team_id"], identity["home_team_id"])
    identities = projection["actor_identities"]
    roster = roster_identities([row for person in (prepared_game["people"] or {}).values()
                                for row in person["roster"]])
    segments = {row["segment_index"]: row for row in prepared_game["segments"] or [] if _five(row)}
    associations = {row["source_index"]: row for row in prepared_game["associations"] or []}
    events = {row["source"]["source_index"]: row["source"] for row in prepared_game["events"] or []}
    attempts = {row["source_index"]: row["details"] for row in prepared_game["attempts"] or []}
    reports = {row["source_index"]: row for row in game["report_rows"] or []}
    ordinary = prepared_game["ordinary_attempt_support"]
    support = {row["segment_index"]: row for row in ordinary["segments"] or []}
    event_support = {row["source_index"]: row for row in ordinary["events"] or []}
    reasons = {family: {} for family in ("u", "h", "b")}
    issues = {family: [] for family in reasons}
    candidates = {family: [] for family in reasons}

    def exclude(family, code, source, index, period=None, clock=None, target=None):
        affected = ([target] if target in segments else
                    [i for i, row in segments.items()
                     if (period is None or row["period_number"] == period)
                     and (clock is None or row["start_seconds"] <= clock <= row["end_seconds"])])
        record = dict(code=code, source=source, source_index=index,
                      period_number=period, elapsed_seconds=clock,
                      scope="game" if period is None else "period" if clock is None else "segment",
                      segment_indices=sorted(affected))
        issues[family].append(record)
        for segment_index in affected:
            reasons[family].setdefault(segment_index, set()).add(code)

    # u/b inherit the saved ordinary-attempt population, never personal assists
    # or geometry. h owns only membership and usable hit collections.
    for index, segment in segments.items():
        row = support.get(index)
        if row is None or row["disposition"] != "included":
            codes = {ordinary["reasons"][i]["code"] for i in row["reason_indices"]} if row else {"source_unavailable"}
            for family in ("u", "b"):
                reasons[family][index] = set(codes) or {"event_evidence_unresolved"}
        invalid_members = []
        for side, team in zip(("away", "home"), teams):
            for role in ("skaters", "goalies"):
                invalid_members.extend(pid for pid in segment["membership"][side + "_" + role]
                                       if pid not in identities or identities[pid]["team_id"] != team
                                       or (identities[pid]["reported_position"] == "G") != (role == "goalies"))
        if invalid_members:
            for family in reasons:
                exclude(family, "membership_unavailable", "prepared-identity", None,
                        segment["period_number"], target=index)
                issues[family][-1]["player_ids"] = sorted(set(invalid_members))
    if prepared_game["events"] is None or game["report_rows"] is None:
        exclude("h", "source_unavailable", "play-by-play" if prepared_game["events"] is None else "play-report", None)

    report_uses = Counter(row["native"]["report_source_index"] for row in associations.values()
                          if row["native"] is not None and row["native"]["match_status"] == "matched")

    for index, event in events.items():
        association = associations.get(index)
        native = association["native"] if association is not None else None
        matching = association["matching_segment_indices"] if association is not None else []
        target = matching[0] if len(matching) == 1 and matching[0] in segments else None
        report_index = native["report_source_index"] if native is not None else None
        report = reports.get(report_index)
        member_map = None if target is None else {
            team: segments[target]["membership"][side + "_skaters"] + segments[target]["membership"][side + "_goalies"]
            for side, team in zip(("away", "home"), teams)}
        period = event["period_number"] if event["period_number"] in (1, 2, 3, 4) else None
        clock = event["elapsed_seconds"] if period is not None else None
        ordinary_row = event_support.get(index)
        if event["type_key"] in ("goal", "shot-on-goal", "missed-shot", "blocked-shot"):
            if ordinary_row is not None and ordinary_row["disposition"] == "included" and ordinary_row["segment_index"] in segments:
                target = ordinary_row["segment_index"]
                member_map = {team: segments[target]["membership"][side + "_skaters"] + segments[target]["membership"][side + "_goalies"]
                              for side, team in zip(("away", "home"), teams)}
                team = event["shooting_team_id"]
                role = "scorer" if event["type_key"] == "goal" else "shooter"
                if event["type_key"] != "blocked-shot":
                    details = attempts[index]["values"] if index in attempts else {}
                    if details.get("physical_status") == "outside_population":
                        issues["u"].append(dict(code="not_applicable", source="play-by-play", source_index=index,
                            period_number=period, elapsed_seconds=clock, scope="segment", segment_indices=[],
                            reason="recorded own/awarded outcome is not a physical unblocked attempt"))
                        continue
                    issue = actor_issue(event, identities, {role: team}, member_map)
                    if event["owner_team_id"] is not None and event["owner_team_id"] != team:
                        issue = "owner_team_conflict"
                    if issue is None and (details.get("physical_status") != "ordinary"
                            or details.get("physical_shooter_id") != event["roles"][role]
                            or details.get("shooting_team_id") != team):
                        issue = "physical_shooter_unresolved"
                    if issue is None:
                        candidates["u"].append((index, target, event["roles"][role], team))
                    else:
                        exclude("u", "identity_conflict", "play-by-play", index, period, clock, target)
                        issues["u"][-1]["actor_reason"] = issue
                else:
                    opponent = teams[1] if team == teams[0] else teams[0] if team == teams[1] else None
                    issue = actor_issue(event, identities, {"shooter": team, "blocker": opponent}, member_map)
                    if event["owner_team_id"] is not None and event["owner_team_id"] != team:
                        issue = "owner_team_conflict"
                    if issue is None:
                        candidates["b"].append((index, target, event["roles"]["blocker"], team))
                    else:
                        exclude("b", "identity_conflict", "play-by-play", index, period, clock, target)
                        issues["b"][-1]["actor_reason"] = issue
            if event["kind_valid"]:
                continue
        if event["kind_valid"] and event["type_key"] != "hit" or event["timed_period"] is False:
            continue
        if native is not None and native["classification"] == "other" and native["shift_relation"] in ("before", "after", "both"):
            continue
        valid = (event["kind_valid"] and event["type_key"] == "hit" and event["timed_period"] is True
                 and period is not None and clock is not None
                 and native is not None and native["classification"] == "five_on_five"
                 and native["match_status"] == "matched" and native["shift_relation"] in ("before", "after", "both")
                 and report is not None and report["event_code"] == "HIT" and report_uses[report_index] == 1
                 and target is not None)
        issue = None
        if valid:
            team = event["owner_team_id"]
            opponent = teams[1] if team == teams[0] else teams[0] if team == teams[1] else None
            issue = actor_issue(event, identities, {"hitter": team, "hit_player": opponent}, member_map)
            if issue is None:
                candidates["h"].append((index, target, event["roles"]["hitter"], team))
                continue
        exclude("h", "identity_conflict" if issue else "event_evidence_unresolved", "play-by-play", index,
                period, clock, target if valid else None)
        if issue:
            issues["h"][-1]["actor_reason"] = issue

    known_codes = set(REPORT_CODES.values()) | NON_ATTEMPT_REPORT_CODES
    for index, report in reports.items():
        if report["event_code"] != "HIT" and report["event_code"] in known_codes:
            continue
        if report["period_number"] == 5:
            continue
        if report["event_code"] == "HIT" and report_uses[index] == 1:
            continue
        period = report["period_number"] if report["period_number"] in (1, 2, 3, 4) else None
        exclude("h", "event_evidence_unresolved", "play-report", index,
                period, report["elapsed_seconds"] if period is not None else None)

    families = {}
    for family in reasons:
        listed = {str(pid) for pid, person in roster.items()
                  if person["reported_position"] in ("C", "L", "R", "D", "F")}
        listed.update(pid for pid, person in (prepared_game["people"] or {}).items()
                      if person["people"]["values"]["reported_position"] in ("C", "L", "R", "D", "F"))
        players = {pid: dict(seconds=0, excluded_seconds=0, count=0, opportunities=0,
                             reasons=[], unquantified_gap=False, has_support=False) for pid in sorted(listed)}
        player_reasons = {pid: Counter() for pid in players}
        for index, segment in segments.items():
            seconds = segment["end_seconds"] - segment["start_seconds"]
            for pid in segment["membership"]["away_skaters"] + segment["membership"]["home_skaters"]:
                require(str(pid) in players, "microstats", "supported segment lacks resolved skater")
                metric = players[str(pid)]
                metric["excluded_seconds" if index in reasons[family] else "seconds"] += seconds
                player_reasons[str(pid)].update(reasons[family].get(index, ()))
        dispositions = []
        for index, target, pid, team in candidates[family]:
            included = target not in reasons[family]
            dispositions.append(dict(source_index=index, segment_index=target, player_id=str(pid),
                                     status="included" if included else "masked"))
            if included and str(pid) in players:
                players[str(pid)]["count"] += 1
        if family == "b":
            for index, row in event_support.items():
                target = row["segment_index"]
                if row["disposition"] != "included" or target not in segments or target in reasons[family]:
                    continue
                event = events[index]
                side = "home" if event["shooting_team_id"] == teams[0] else "away"
                for pid in segments[target]["membership"][side + "_skaters"]:
                    players[str(pid)]["opportunities"] += 1
        periods = game["periods"]
        gap = (periods is None or any(row["status"] != "supported" for row in periods)
               or game["native_intervals"] is None
               or any(row["classification"] == "unresolved" for row in game["native_intervals"] or [])
               or any(row["name"] == "shift_collection" and row["observed"] == 0 for row in game["checks"]))
        collections_available = (prepared_game["events"] is not None and game["report_rows"] is not None
                                 and (family == "h" or ordinary["segments"] is not None))
        for pid, metric in players.items():
            metric["reasons"] = [dict(code=code, count=count) for code, count in sorted(player_reasons[pid].items())]
            metric["unquantified_gap"] = gap or int(pid) not in identities
            metric["has_support"] = (metric["seconds"] > 0 or collections_available
                                     and not metric["unquantified_gap"] and metric["excluded_seconds"] == 0)
            require(family != "b" or metric["count"] <= metric["opportunities"], "microstats", "blocks exceed matched opportunities")
        families[family] = dict(players=players, issues=issues[family], event_dispositions=dispositions,
                                inherited_reasons=ordinary["reasons"] if family in ("u", "b") else [],
                                masks=[dict(segment_index=i, reason_codes=sorted(codes)) for i, codes in sorted(reasons[family].items())])
    return dict(season=prepared_game["season"], game_id=prepared_game["game_id"], families=families)


def _support(seconds=None, count=None, excluded=None, gap=False, reasons=()):
    return dict(included_seconds=seconds, events=count, eligible_weight=None,
                known_excluded_seconds=excluded, unquantified_gap=gap,
                reason_counts=list(reasons), inferred_inputs=[], current_season_information=bool(seconds or count),
                prior_only=False, prior_seasons=[])


def _fact(value, numerator, denominator, source_id, support, *, unit="per60", denominator_kind="included_seconds",
          reason="no_exposure", explanation="no matched positive denominator", construction="recorded", method=False):
    provenance = dict(kind="method" if method else "source", id=source_id)
    return dict(value=value, unavailable_reason=None if value is not None else reason,
                reason_detail=None if value is not None else dict(explanation=explanation, evidence=[provenance]),
                uncertainty=dict(kind="not_estimated"), support=support, unit=unit,
                numerator=numerator, denominator=denominator, denominator_kind=denominator_kind,
                construction=construction, provenance=provenance)


def summarize_season(people: list["PersonIdentity"], game_reductions: Iterable[GameReduction],
                     observed_result: ObservedResult, source_ids: "SourceIds",
                     pending_method_id: str) -> list[dict]:
    """emit every fixed field, with exact old personal scoring and own support."""
    totals = {family: {} for family in ("u", "h", "b")}
    for game in game_reductions:
        require(game["season"] == observed_result.season, "microstats", "mixed season reductions")
        for family, reduced in game["families"].items():
            for pid, metric in reduced["players"].items():
                total = totals[family].setdefault(pid, dict(seconds=0, excluded_seconds=0, count=0,
                    opportunities=0, unquantified_gap=False, has_support=False, reasons=Counter()))
                for key in ("seconds", "excluded_seconds", "count", "opportunities"):
                    total[key] += metric[key]
                total["unquantified_gap"] |= metric["unquantified_gap"]
                total["unquantified_gap"] |= not metric["has_support"] and metric["excluded_seconds"] == 0
                total["has_support"] |= metric["has_support"]
                total["reasons"].update({r["code"]: r["count"] for r in metric["reasons"]})
    personal = {row.player_id: row.personal for row in observed_result.player_seasons}
    rows = []
    for person in people:
        if person["kind"] != "skater":
            continue
        pid = person["player_id"]
        payload = {}
        old = personal.get(pid)
        for key, count_name in (("goals_per60", "goals"), ("primary_assists_per60", "primary_assists")):
            support = _support(old.included_seconds, getattr(old, count_name), old.known_excluded_seconds,
                               bool(set(old.reason_codes) & {"required_source_unavailable", "elapsed_membership_unresolved",
                                   "period_horizon_unavailable", "roster_identity_unresolved", "unassigned_player_games",
                                   "shift_source_empty", "player_toi_conflict"}),
                               [dict(code=code, count=1) for code in old.reason_codes]) if old else _support(gap=True, reasons=[dict(code="source_unavailable", count=1)])
            payload[key] = _fact(getattr(old, key) if old else None, getattr(old, count_name) if old else None,
                old.included_seconds if old else None, source_ids["p"], support,
                reason="no_exposure" if old else "missing_source",
                explanation="existing observed personal-credit support has no positive exposure" if old else "no existing observed personal row; absence does not establish zero exposure")
        for family, key in (("u", "unblocked_attempts_per60"), ("h", "hits_per60"), ("b", "blocked_attempt_share")):
            metric = totals[family].get(pid)
            seconds = metric["seconds"] if metric else None
            supported = metric is not None and metric["has_support"]
            count = metric["count"] if supported else None
            denominator = (metric["opportunities"] if supported else None) if family == "b" else seconds
            value = (count / denominator if family == "b" else 3600 * count / denominator) if denominator else None
            support = _support(seconds, count, metric["excluded_seconds"], metric["unquantified_gap"],
                [dict(code=code, count=n) for code, n in sorted(metric["reasons"].items())]) if metric else _support(gap=True, reasons=[dict(code="source_unavailable", count=1)])
            payload[key] = _fact(value, count, denominator, source_ids[family], support,
                unit="fraction" if family == "b" else "per60", denominator_kind="opponent_attempts" if family == "b" else "included_seconds",
                reason="no_exposure" if supported else "missing_source",
                explanation="no matched positive denominator" if supported else "no checked family count population; source, actor or elapsed support is unavailable")
        for key in MICROSTATS:
            if key in payload:
                continue
            if key == "reference_xg_per60":
                payload[key] = _fact(None, None, None, pending_method_id, _support(), reason="not_computed",
                    explanation="neutral all-attempt reference probabilities await v1-05/06", construction="model_valued", method=True)
                continue
            skating = key.startswith("skating_")
            source = source_ids["skating" if skating else "tracking"]
            description = ("source maximum sustained speed in mph" if key == "skating_max_speed_mph" else
                           "source 20+ mph burst count" if skating else {
                               "primary_pass_xg_per60": "observed primary-pass links, recipient probabilities and matching tracked windows",
                               "puck_management_xga_saved_per100_plays": "source model, comparison reference and eligible puck plays",
                               "entry_denial_fraction": "denied entries and all tracked entry attempts defended",
                               "possession_entry_denial_fraction": "denied controlled entries and all tracked entry attempts defended",
                           }.get(key, key.removesuffix("_per60").replace("_", " ") + " credits and matching tracked windows"))
            unit, denominator = (("mph", "none") if key == "skating_max_speed_mph" else ("count", "none") if skating else
                ("fraction", "tracked_plays") if key.endswith("_fraction") else
                ("xga_saved_per100_plays", "tracked_plays") if key == "puck_management_xga_saved_per100_plays" else ("per60", "included_seconds"))
            payload[key] = _fact(None, None, None, source, _support(gap=True, reasons=[dict(code="source_unavailable", count=1)]),
                unit=unit, denominator_kind=denominator, reason="missing_source",
                explanation=(description + ": skating acquisition deferred; no admitted measurements, player-season context or checked census under v1-04" if skating else description + " are not acquired; public definitions supply no observation stream"),
                construction="source_modeled" if key == "puck_management_xga_saved_per100_plays" else "recorded")
            if key == "primary_pass_xg_per60":
                payload[key]["construction"] = "model_valued"
                payload[key]["provenance"] = dict(kind="method", id=pending_method_id)
                payload[key]["reason_detail"]["evidence"].append(payload[key]["provenance"])
        rows.append(dict(season=observed_result.season, player_id=pid,
            result=dict(availability="provided", explanation=None, data=payload)))
    return rows
