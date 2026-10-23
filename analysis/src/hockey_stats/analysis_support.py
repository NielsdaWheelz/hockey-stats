"""matched ordinary-attempt support, separate from retained observed/research masks."""

from collections import Counter

from .feature_data import ATTEMPT_KINDS, _links
from .reconstruct import (
    MEMBERSHIP_FIELDS, REPORT_CODES, lineup_classification, membership_interval_link,
    membership_segments, report_membership, roster_identities,
)

ATTEMPT_CODES = {REPORT_CODES[kind] for kind in ATTEMPT_KINDS}
# source ceremony/challenge rows are non-attempts even without api counterparts.
# an absent or unrecognized code remains a potential attempt.
NON_ATTEMPT_REPORT_CODES = (set(REPORT_CODES.values()) - ATTEMPT_CODES) | {
    "PGSTR", "PGEND", "ANTHEM", "CHL", "GOFF", "GON",
}


def _state(membership):
    return tuple(len(membership[field]) for field in MEMBERSHIP_FIELDS)


def _touching(segments, period, clock):
    if clock is None:
        return []
    return [row["segment_index"] for row in segments
            if row["period_number"] == period
            and row["start_seconds"] <= clock <= row["end_seconds"]]


def prepare_support(document, reconstruction, input_ref):
    """retain source associations and save one union mask for new rate consumers.

    reported membership is checked independently of physical action and credits.
    the native rows and old observed masks remain separate source projections.
    """
    link = _links(input_ref)
    issues = []
    native_intervals = reconstruction["intervals"]
    segments = None if native_intervals is None else [
        {"segment_index": index, "native_interval_indices": row["interval_indices"],
         "period_number": row["period_number"], "start_seconds": row["start_seconds"],
         "end_seconds": row["end_seconds"],
         "membership": {key: row[key] for key in MEMBERSHIP_FIELDS}, "issue_indices": []}
        for index, row in enumerate(membership_segments(native_intervals))
    ]
    segment_rows = segments or []
    interval_segments = {native_index: row["segment_index"] for row in segment_rows
                         for native_index in row["native_interval_indices"]}
    source_events, report_rows = document["events"], document["report_rows"]
    natives = {row["source_index"]: row for row in reconstruction["events"] or []}
    reports = {row["source_index"]: row for row in report_rows or []}
    identities = roster_identities(document["roster_records"])
    checked_reports = {}
    for index, report in reports.items():
        member_issues = []
        membership, invalid = report_membership(report, document["game"], identities, member_issues)
        checked_reports[index] = membership if not invalid and lineup_classification(membership) != "unresolved" else None
    reasons = []
    segment_reasons = {row["segment_index"]: [] for row in segment_rows}

    def reason(code, affected, evidence, *, period=None, events=(), reports=(), scope="segment"):
        affected = sorted(set(affected))
        index = len(reasons)
        reasons.append({"code": code, "scope": scope, "period_number": period,
                        "event_source_indices": sorted(set(events)),
                        "report_source_indices": sorted(set(reports)),
                        "affected_segment_indices": affected, "evidence": list(evidence)})
        issue_index = len(issues)
        locator = evidence[0]
        issues.append({"code": code, "source": locator["source"], "path": locator["path"],
                       "message": "ordinary-attempt rate support: " + code.replace("_", " "),
                       "evidence": list(evidence)})
        for segment_index in affected:
            segment_reasons[segment_index].append(index)
            segment_rows[segment_index]["issue_indices"].append(issue_index)
        return index, issue_index

    def affected_at(period, clock, membership):
        if clock is None or period is None:
            affected = [row["segment_index"] for row in segment_rows
                        if period is None or row["period_number"] == period]
            return affected, "game" if period is None else "period"
        touching = _touching(segment_rows, period, clock)
        return [i for i in touching if segment_rows[i]["start_seconds"] < clock < segment_rows[i]["end_seconds"]
                or membership is None or _state(segment_rows[i]["membership"]) == _state(membership)], "segment"

    all_segments = list(segment_reasons)
    for source, collection, path in (("play-by-play", source_events, "/plays"),
                                     ("play-report", report_rows, "/rows")):
        if collection is None:
            reason("source_unavailable", all_segments, [link(source, path)], scope="game")
    for index, check in enumerate(document["checks"]):
        if check["name"] in ("timed_goals", "timed_shots") and check["status"] == "mismatch":
            reason("count_accounting_conflict", all_segments,
                   [link("interpreted", f"/checks/{index}")], scope="game")
    for period_index, period in enumerate(reconstruction["periods"] or []):
        if period["status"] != "supported":
            reason("horizon_unavailable", [], [link("reconstruction", f"/periods/{period_index}")],
                   period=period["period_number"], scope="period")
    game = document["game"]
    for segment in segment_rows:
        missing = []
        for field, members in segment["membership"].items():
            side, role = field.split("_")
            team_id = game[side + "_team_id"] if game is not None else None
            for member in members:
                identity = identities.get(member)
                position = identity["reported_position"] if identity else None
                if (identity is None or identity["team_id"] != team_id
                        or role == "goalies" and position != "G"
                        or role == "skaters" and position not in {"C", "L", "R", "D", "F"}):
                    missing.append(member)
        if missing:
            reason("membership_unavailable", [segment["segment_index"]],
                   [link("play-by-play", "/rosterSpots")], period=segment["period_number"])

    associations = None if source_events is None else []
    event_support = None if source_events is None else []
    used_reports = Counter(row["report_source_index"] for row in natives.values()
                           if row["match_status"] == "matched" and row["report_source_index"] is not None)
    for event in source_events or []:
        index, period, clock = event["source_index"], event["period_number"], event["elapsed_seconds"]
        native = natives.get(index)
        report_index = native["report_source_index"] if native is not None else None
        report = reports.get(report_index)
        membership = checked_reports[report_index] if report_index in checked_reports else None
        touching = _touching(segment_rows, period, clock)
        temporal_case = ("interior" if any(segment_rows[i]["start_seconds"] < clock < segment_rows[i]["end_seconds"]
                                           for i in touching) else "boundary" if touching else "unavailable")
        matched = (native is not None and native["match_status"] == "matched"
                   and report is not None and used_reports[report_index] == 1)
        relation, indices = "unavailable", []
        if membership is not None and event["timed_period"] is True:
            # resolved native rows already own their exact before/after links.
            # otherwise the same primitive can expose membership despite bad credits.
            if native is not None and native["classification"] in ("five_on_five", "other"):
                relation, indices = native["shift_relation"], native["interval_indices"]
            else:
                relation, indices = membership_interval_link(
                    membership, period, clock, native_intervals, reconstruction["periods"])
        matching = sorted({interval_segments[i] for i in indices if i in interval_segments})
        association = {"source_index": index, "native": native,
                       "touching_segment_indices": touching, "matching_segment_indices": matching,
                       "temporal_case": temporal_case, "issue_indices": []}
        associations.append(association)
        row = {"source_index": index, "disposition": "not_applicable", "segment_index": None,
               "chunk_index": None, "reason_indices": []}
        event_support.append(row)
        potential = event["type_key"] in ATTEMPT_KINDS or not event["kind_valid"]
        modifier = native["goal_modifier_evidence"] if native is not None else None
        outside = (event["timed_period"] is False or report is not None and report["penalty_shot"] is True
                   or modifier is not None and modifier["status"] == "reported"
                   and modifier["reported_value"] == "penalty-shot")
        if not potential or outside:
            continue
        row["disposition"] = "unresolved"
        evidence = [link("play-by-play", f"/plays/{index}")]
        if report is not None:
            evidence.append(link("play-report", f"/rows/{report_index}[{report['row_id']}]") )
        corroborated = (event["kind_valid"] and event["type_key"] in ATTEMPT_KINDS
                        and event["timed_period"] is True and period is not None and clock is not None
                        and matched and report["penalty_shot"] is False and membership is not None)
        if matched and membership is not None and len(matching) == 1 and relation in ("before", "after", "both"):
            row["segment_index"] = matching[0]
            if corroborated:
                row["disposition"] = "included"
        local_reasons = []
        if corroborated and temporal_case == "interior":
            for segment_index in touching:
                current = segment_rows[segment_index]
                if (current["start_seconds"] < clock < current["end_seconds"]
                        and current["membership"] != membership):
                    code = "strength_conflict" if _state(current["membership"]) != _state(membership) else "identity_conflict"
                    local_reasons.append(reason(code, [segment_index], evidence, period=period,
                                                events=[index], reports=[report_index]))
        if corroborated and temporal_case == "boundary" and row["segment_index"] is None:
            other_state = False
            for segment_index in touching:
                current = segment_rows[segment_index]["membership"]
                if current != membership:
                    same_state = _state(current) == _state(membership)
                    if same_state:
                        local_reasons.append(reason("identity_conflict", [segment_index], evidence,
                                                    period=period, events=[index], reports=[report_index]))
                    elif not other_state:
                        local_reasons.append(reason("strength_conflict", [], evidence,
                                                    period=period, events=[index], reports=[report_index]))
                        other_state = True
        if (not corroborated or row["segment_index"] is None) and not local_reasons:
            affected, scope = affected_at(period, clock, membership)
            if event["timed_period"] is not True or period is None or clock is None:
                code = "clock_unavailable"
            elif corroborated and relation == "unavailable":
                horizon = next(((i, p) for i, p in enumerate(reconstruction["periods"] or [])
                                if p["period_number"] == period), None)
                if horizon is None or horizon[1]["status"] != "supported":
                    code, scope = "horizon_unavailable", "period"
                    evidence.append(link("reconstruction", f"/periods/{horizon[0]}" if horizon else "/periods"))
                else:
                    code = "membership_unavailable"
                    evidence.append(link("reconstruction", "/intervals"))
            else:
                code = "ambiguous_assignment" if corroborated else "event_evidence_unresolved"
            local_reasons.append(reason(code, affected, evidence, period=period, events=[index],
                                        reports=[] if report_index is None else [report_index], scope=scope))
        for reason_index, issue_index in local_reasons:
            row["reason_indices"].append(reason_index)
            association["issue_indices"].append(issue_index)

    report_only = None if report_rows is None else []
    for report in report_rows or []:
        index = report["source_index"]
        if used_reports[index] or report["event_code"] in NON_ATTEMPT_REPORT_CODES:
            continue
        record = {"report_source_index": index, "affected_segment_indices": [], "reason_indices": []}
        report_only.append(record)
        if report["period_number"] == 5 or report["penalty_shot"] is True:
            continue
        membership = checked_reports[index]
        affected, scope = affected_at(report["period_number"], report["elapsed_seconds"], membership)
        reason_index, _ = reason("unmatched_report_attempt", affected,
                                  [link("play-report", f"/rows/{index}[{report['row_id']}]")],
                                  period=report["period_number"], reports=[index], scope=scope)
        record["affected_segment_indices"], record["reason_indices"] = affected, [reason_index]

    for row in event_support or []:
        if row["disposition"] == "not_applicable":
            continue
        if row["segment_index"] is not None:
            row["reason_indices"] = sorted(set(row["reason_indices"] + segment_reasons[row["segment_index"]]))
        else:
            row["reason_indices"] = sorted(set(row["reason_indices"] + [i for i, value in enumerate(reasons)
                if value["scope"] == "game" or row["source_index"] in value["event_source_indices"]]))
        if row["reason_indices"] and (row["segment_index"] is not None
                                       or any(reasons[i]["affected_segment_indices"] for i in row["reason_indices"])):
            row["disposition"] = "excluded"
    support = {"segments": None if segments is None else [
        {"segment_index": index, "disposition": "excluded" if indices else "included", "reason_indices": indices}
        for index, indices in segment_reasons.items()],
        "events": event_support, "report_only": report_only, "reasons": reasons}
    return {"segments": segments, "associations": associations, "ordinary_attempt_support": support, "issues": issues}


def assign_support_chunks(prepared, chunks, events):
    """choose following child at an internal boundary, final child at run end."""
    clocks = {row["source_index"]: row["elapsed_seconds"] for row in events or []}
    for row in prepared["ordinary_attempt_support"]["events"] or []:
        if row["segment_index"] is None:
            continue
        children = [child for child in chunks or [] if child["segment_index"] == row["segment_index"]]
        clock = clocks[row["source_index"]]
        matching = [child for child in children if child["start_seconds"] <= clock < child["end_seconds"]]
        if not matching and children and clock == children[-1]["end_seconds"]:
            matching = [children[-1]]
        if len(matching) != 1:
            raise ValueError(f"event {row['source_index']}: assigned segment has no unique child")
        row["chunk_index"] = matching[0]["chunk_index"]


def validate_support(game):
    """check saved decisions with the same source owner, using retained records only.

    no original capture is opened. this replay validates publication semantics;
    consumers still read the saved mask rather than defining another population.
    """
    import json

    from .corpus_inputs import require

    source = game["game"]
    support = game["ordinary_attempt_support"]
    if source["ledger"]["status"] != "reconstructed":
        require(all(game[field] is None for field in (
                    "events", "associations", "segments", "chunks", "player_shifts",
                    "episodes", "people", "attempts", "credits"))
                and all(support[field] is None for field in ("segments", "events", "report_only"))
                and not support["reasons"]
                and any(issue["code"] == "source_unavailable" and issue["evidence"]
                        for issue in game["issues"]),
                "game/support", "unavailable ledger game needs located unavailable product collections")
        return
    require(source["identity"] is not None, "game/support", "reconstructed game identity unavailable")
    for prepared, original, label in (
        (support["segments"], game["segments"], "segments"),
        (support["events"], game["events"], "events"),
        (support["report_only"], source["report_rows"], "report_only"),
        (game["segments"], source["native_intervals"], "native intervals"),
    ):
        require((prepared is None) == (original is None), "game/support/" + label,
                "source availability differs; null is not a checked empty collection")

    events = [row["source"] for row in game["events"] or []]
    require(sorted(row["source_index"] for row in events) == list(range(len(events))),
            "game/support/events", "original source indexes must be complete and consecutive")
    reports = source["report_rows"]
    require(reports is None or [row["source_index"] for row in reports] == list(range(len(reports))),
            "game/support/report_only", "original report indexes must be complete and consecutive")
    for interval in source["native_intervals"] or []:
        membership = {field: interval[field] for field in MEMBERSHIP_FIELDS}
        require(interval["classification"] == "unresolved"
                or interval["classification"] == lineup_classification(membership) != "unresolved",
                "game/support/segments", "resolved native interval has unsupported membership")
    # null-player roster rows cannot establish an identity. all usable rows,
    # including duplicates/conflicts, survive in their person's dated roster.
    roster = [row for person in (game["people"] or {}).values() for row in person["roster"]]
    document = {
        "game": source["identity"], "events": None if game["events"] is None else events,
        "report_rows": reports, "roster_records": roster, "checks": source["checks"],
    }
    reconstruction = {
        "intervals": source["native_intervals"], "periods": source["periods"],
        "events": None if game["associations"] is None else [
            row["native"] for row in game["associations"] if row["native"] is not None],
        "issues": source["native_issues"],
    }
    expected = prepare_support(document, reconstruction,
                               {"path": "/retained-prepared-source", "sha256": "0" * 64})
    actual_segments = game["segments"]
    segment_fields = ("segment_index", "native_interval_indices", "period_number",
                      "start_seconds", "end_seconds", "membership")
    require(actual_segments is None or [
        {field: row[field] for field in segment_fields} for row in actual_segments
    ] == [
        {field: row[field] for field in segment_fields} for row in expected["segments"]
    ], "game/support/segments", "maximal resolved native partition differs")
    try:
        assign_support_chunks(expected, game["chunks"], events)
    except ValueError as error:
        require(False, "game/support/chunks", str(error))

    def reason_key(row):
        require(bool(row["evidence"]), "game/support/reasons", "reason needs source evidence")
        return json.dumps({
            **{field: value for field, value in row.items() if field != "evidence"},
            "evidence": [{"source": ref["source"], "path": ref["path"]}
                         for ref in row["evidence"]],
        }, sort_keys=True)

    actual_keys = [reason_key(row) for row in support["reasons"]]
    expected_keys = [reason_key(row) for row in expected["ordinary_attempt_support"]["reasons"]]
    require(len(actual_keys) == len(set(actual_keys))
            and len(expected_keys) == len(set(expected_keys))
            and set(actual_keys) == set(expected_keys),
            "game/support/reasons", "saved source witnesses, scope or exclusion policy differs")
    expected_index = {key: index for index, key in enumerate(expected_keys)}
    reason_indices = {index: expected_index[key] for index, key in enumerate(actual_keys)}
    for kind, key in (("segments", "segment_index"), ("events", "source_index"),
                      ("report_only", "report_source_index")):
        rows, required_rows = support[kind], expected["ordinary_attempt_support"][kind]
        if rows is None:
            continue
        require(len({row[key] for row in rows}) == len(rows),
                "game/support/" + kind, "duplicate support record")
        remapped = {}
        for row in rows:
            require(all(index in reason_indices for index in row["reason_indices"]),
                    "game/support/" + kind, "broken reason reference")
            remapped[row[key]] = {**row, "reason_indices": sorted(
                reason_indices[index] for index in row["reason_indices"])}
        require(remapped == {row[key]: {**row, "reason_indices": sorted(row["reason_indices"])}
                             for row in required_rows},
                "game/support/" + kind, "saved population, assignments or exclusion union differs")

    def issue_signatures(owner, indices):
        return {(owner[index]["code"], owner[index]["source"], owner[index]["path"])
                for index in indices}

    required_associations = {row["source_index"]: row for row in expected["associations"] or []}
    for row in game["associations"] or []:
        required = required_associations[row["source_index"]]
        require(all(row[field] == required[field] for field in (
            "touching_segment_indices", "matching_segment_indices", "temporal_case")),
            "game/associations", "source-supported temporal or native membership association differs")
        require(issue_signatures(expected["issues"], required["issue_indices"])
                <= issue_signatures(game["issues"], row["issue_indices"]),
                "game/associations", "located support issue witness missing")
    for row, required in zip(actual_segments or [], expected["segments"] or []):
        require(issue_signatures(expected["issues"], required["issue_indices"])
                <= issue_signatures(game["issues"], row["issue_indices"]),
                "game/segments", "located support issue witness missing")
