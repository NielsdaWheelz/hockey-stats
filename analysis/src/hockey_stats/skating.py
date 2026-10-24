"""offline skating feasibility: attributed missingness and checked census contracts.

the observed detail json exposes raw candidates and maximum-event witnesses,
but does not establish player-season aggregate context. no available primary
measurement adapter has been exercised; unrelated bodies stay unresolved.
"""

import argparse
from datetime import datetime
import hashlib
import math
import os
from pathlib import Path
import re
import sys

from .artifacts import implementation_identity, require, write_json
from .captures import InputContractError, read_reference_capture, read_skating_capture, skating_url, strict_json
from .references import BIO_SKATER_SOURCE_FIELDS

SEASONS = ("20232024", "20242025", "20252026")
KINDS = ("detail", "listing", "glossary")
MEASUREMENTS = ("skating_max_speed_mph", "skating_bursts_over20_count")
STATUSES = ("available", "source_null", "missing_field", "not_requested", "http_unavailable",
            "transport_failed", "schema_unresolved", "context_unresolved", "invalid_value", "conflict")
POSITION_GROUPS = {"C": "f", "L": "f", "R": "f", "F": "f", "D": "d"}


def _object(value, keys, name):
    require(isinstance(value, dict) and set(value) == set(keys.split()), f"{name}: expected exactly {keys}")


def _text(value, name):
    require(isinstance(value, str) and bool(value.strip()), f"{name}: expected nonblank text")


def _array(value, name):
    require(isinstance(value, list), f"{name}: expected array")
    return value


def _digest(value):
    require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None, "invalid sha256")


def _id(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9]+", value) is not None and int(value) > 0,
            "player id must be a positive digit string")


def _season(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9]{8}", value) is not None
            and int(value[4:]) == int(value[:4]) + 1, "invalid consecutive-year season")


def _timestamp(value):
    require(isinstance(value, str) and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})", value)
        is not None, "invalid iso timestamp")
    try:
        datetime.fromisoformat(value)
    except ValueError as error:
        raise InputContractError("invalid calendar timestamp") from error


def _json(path):
    try:
        return strict_json(path.read_bytes())
    except (ValueError, UnicodeError) as error:
        raise InputContractError(f"{path}: invalid finite unique-key json: {error}") from error


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _key(row):
    return row["kind"], row["season"], row["player_id"]


def _identity(row, seasons):
    require(row["kind"] in KINDS, "unknown skating source kind")
    if row["kind"] == "glossary":
        require(row["season"] is None and row["player_id"] is None, "glossary has no season/player identity")
    else:
        require(row["season"] in seasons, "request season outside selection")
        if row["kind"] == "detail":
            _id(row["player_id"])
        else:
            require(row["player_id"] is None, "listing has no player identity")


def _ids(values, name):
    _array(values, name)
    for value in values:
        _id(value)
    require(len(set(values)) == len(values), f"{name}: duplicate ids")
    return set(values)


def _selection(document):
    _object(document, "schema_version purpose seasons requests position_references", "selection")
    require(type(document["schema_version"]) is int and document["schema_version"] == 1, "unsupported selection schema")
    require(document["purpose"] in ("real", "fixture"), "invalid selection purpose")
    seasons = _array(document["seasons"], "seasons")
    for season in seasons:
        _season(season)
    require(bool(seasons) and len(set(seasons)) == len(seasons), "seasons must be nonempty and unique")
    if document["purpose"] == "real":
        require(seasons == list(SEASONS), "real selection requires the three displayed seasons in order")
    ids, keys = set(), set()
    requests = _array(document["requests"], "requests")
    for row in requests:
        _object(row, "request_id kind season player_id capture deferred_reason", "selected request")
        _text(row["request_id"], "request_id")
        _identity(row, seasons)
        require(row["request_id"] not in ids and _key(row) not in keys, "duplicate request id or identity")
        ids.add(row["request_id"])
        keys.add(_key(row))
        if row["capture"] is None:
            _text(row["deferred_reason"], "deferred reason")
        else:
            require(row["deferred_reason"] is None, "captured/failed attempt cannot be deferred")
            capture = row["capture"]
            _object(capture, "directory receipt_sha256 origin", "selected capture")
            _text(capture["directory"], "capture directory")
            _digest(capture["receipt_sha256"])
            require(capture["origin"] in ("primary", "synthetic"), "invalid capture origin")
            require(document["purpose"] != "real" or capture["origin"] == "primary", "real selection rejects synthetic inputs")
    if document["purpose"] == "real":
        fixed = {("detail", season, player) for season in SEASONS for player in ("8478402", "8480800")}
        fixed |= {("listing", season, None) for season in SEASONS} | {("glossary", None, None)}
        require(fixed <= keys and len(keys - fixed) <= 2 and all(key[0] == "detail" for key in keys - fixed),
                "real selection must reconcile ten fixed keys and at most two adaptive detail keys")
        require(sum(row["capture"] is not None for row in requests) <= 12, "request cap exceeded")
        require(all(row["capture"] is not None for row in requests if _key(row) in keys - fixed),
                "unused adaptive allowance is a count, not a deferred fabricated identity")
    seen = set()
    for row in _array(document["position_references"], "position references"):
        _object(row, "season directory receipt_sha256 body_sha256", "position reference")
        require(row["season"] in seasons and row["season"] not in seen, "duplicate/out-of-selection position reference")
        seen.add(row["season"])
        _text(row["directory"], "position reference directory")
        _digest(row["receipt_sha256"])
        _digest(row["body_sha256"])
    return document


def _witnesses(values, captures, references, *, season=None, player=None, measurement=False):
    for witness in _array(values, "evidence"):
        _object(witness, "source locator raw_value", "witness")
        source, locator = witness["source"], witness["locator"]
        require(isinstance(source, dict), "invalid witness source")
        if source.get("kind") == "request":
            _object(source, "kind request_id", "request witness")
            _text(source["request_id"], "witness request id")
            require(source["request_id"] in captures, "witness references an unselected request")
            capture = captures[source["request_id"]]
            require(capture["state"] == "captured" and 200 <= capture["http_status"] <= 299,
                    "semantic witness requires a successful captured body")
            if season is not None:
                require(capture["season"] == season, "witness season context mismatch")
            if player is not None and capture["kind"] == "detail":
                require(capture["player_id"] == player, "witness player context mismatch")
            if measurement:
                require(capture["kind"] in ("detail", "listing"), "glossary is not measurement evidence")
        else:
            _object(source, "kind season", "position witness")
            _season(source["season"])
            require(source["kind"] == "position_reference" and source["season"] in references,
                    "witness references an unselected position reference")
            require(not measurement and (season is None or season == source["season"]),
                    "position reference cannot supply measurement/context from another season")
        _object(locator, "kind value", "witness locator")
        require(locator["kind"] in ("json_pointer", "html_label"), "invalid witness locator kind")
        if locator["kind"] == "json_pointer":
            require(isinstance(locator["value"], str) and (locator["value"] == "" or locator["value"].startswith("/"))
                    and re.search(r"~(?![01])", locator["value"]) is None, "invalid json pointer")
        else:
            _text(locator["value"], "visible html label")


def _measurement(value, measurement_id, captures, references, season, player):
    _object(value, "value status reason evidence transformation", "measurement")
    require(value["status"] in STATUSES, "invalid measurement status")
    _witnesses(value["evidence"], captures, references, season=season, player=player, measurement=True)
    if value["status"] in ("available", "source_null"):
        require(all(captures[w["source"]["request_id"]]["origin"] == "synthetic" for w in value["evidence"]),
                "primary aggregate measurement interpretation requires an evidence-backed adapter amendment; only synthetic fixture arithmetic is supported")
    if value["status"] == "available":
        number = value["value"]
        require(type(number) in (int, float) and math.isfinite(number) and number >= 0, "invalid finite nonnegative measurement")
        if measurement_id == "skating_bursts_over20_count":
            require(type(number) is int, "burst count must be a nonnegative integer")
        require(value["reason"] is None and bool(value["evidence"]), "available value needs evidence and null reason")
        require(value["transformation"] in ("direct", "sum_disjoint"), "available value needs a transformation")
        if value["transformation"] == "direct":
            require(any(type(w["raw_value"]) in (int, float) and w["raw_value"] == number for w in value["evidence"]),
                    "direct measurement must retain its raw numeric value")
        else:
            require(measurement_id == "skating_bursts_over20_count" and len(value["evidence"]) == 2
                    and all(type(w["raw_value"]) is int and w["raw_value"] >= 0 for w in value["evidence"])
                    and sum(w["raw_value"] for w in value["evidence"]) == number
                    and value["evidence"][0]["locator"] != value["evidence"][1]["locator"],
                    "disjoint burst sum must retain two distinct nonnegative integer counters")
            require(value["evidence"][0]["source"] == value["evidence"][1]["source"], "disjoint counters must share one source snapshot")
    else:
        require(value["value"] is None and value["transformation"] is None, "unavailable measurement must have null value/transformation")
        _text(value["reason"], "unavailable measurement reason")
        if value["status"] == "source_null":
            require(bool(value["evidence"]) and any(w["raw_value"] is None for w in value["evidence"]),
                    "source-null requires a literal null witness")


def _validate(document, selection, expected_purpose):
    _object(document, "schema_version purpose implementation selection adapter_status captures source_contracts observations census", "skating")
    require(type(document["schema_version"]) is int and document["schema_version"] == 1, "unsupported skating schema")
    require(document["purpose"] == selection["purpose"] == expected_purpose, "artifact purpose mismatch")
    _object(document["implementation"], "git_commit git_dirty python_version", "implementation")
    implementation = document["implementation"]
    require(implementation["git_commit"] is None or isinstance(implementation["git_commit"], str)
            and re.fullmatch(r"[a-f0-9]{40}", implementation["git_commit"]) is not None, "invalid implementation commit")
    require(implementation["git_dirty"] is None or type(implementation["git_dirty"]) is bool, "invalid implementation dirty state")
    _text(implementation["python_version"], "python version")
    require(document["adapter_status"] == "not_observed", "a primary aggregate adapter requires an evidence-backed amendment; adapter_status must be not_observed")
    captures = {}
    require(len(_array(document["captures"], "captures")) == len(selection["requests"]), "capture/selection cardinality mismatch")
    selected = {row["request_id"]: row for row in selection["requests"]}
    references = {row["season"]: row for row in selection["position_references"]}
    for row in document["captures"]:
        _object(row, "request_id kind season player_id url requested_at http_status state receipt_path receipt_sha256 body_sha256 origin failure deferred_reason", "capture")
        request_id = row["request_id"]
        require(isinstance(request_id, str) and request_id in selected and request_id not in captures, "duplicate/unselected capture id")
        request = selected[request_id]
        require(_key(row) == _key(request) and row["url"] == skating_url(*_key(row)), "capture identity/url mismatch")
        capture = request["capture"]
        if capture is None:
            require(row["state"] == "deferred" and row["deferred_reason"] == request["deferred_reason"], "deferred selection mismatch")
            require(all(row[key] is None for key in ("requested_at", "http_status", "receipt_path", "receipt_sha256", "body_sha256", "origin", "failure")),
                    "deferred row cannot contain a receipt/status/body/timestamp/origin/failure")
        else:
            require(row["state"] in ("captured", "failed") and row["origin"] == capture["origin"]
                    and row["receipt_sha256"] == capture["receipt_sha256"] and row["deferred_reason"] is None,
                    "capture differs from selected receipt/origin")
            _timestamp(row["requested_at"])
            _text(row["receipt_path"], "receipt path")
            base = Path(document["selection"]["original_path"]).parent
            expected = Path(os.path.abspath(base / capture["directory"] / ("edge-skating-" + row["kind"]) / "capture.json"))
            require(Path(row["receipt_path"]) == expected, "capture receipt path differs from original selection base")
            require(row["http_status"] is None or type(row["http_status"]) is int and 100 <= row["http_status"] <= 599, "invalid http status")
            if row["state"] == "captured":
                require(row["http_status"] is not None and row["failure"] is None, "captured row needs status and null failure")
                _digest(row["body_sha256"])
            else:
                require(row["body_sha256"] is None, "failed capture has no promised body")
                _object(row["failure"], "kind message", "capture failure")
                require(row["failure"]["kind"] in ("transport", "body-read", "timeout") and isinstance(row["failure"]["message"], str), "invalid capture failure")
        captures[request_id] = row
    contracts = {}
    for row in _array(document["source_contracts"], "source contracts"):
        _object(row, "kind format identity_rules measurement_rules enumeration_rules shape_evidence definition_evidence limitations", "source contract")
        require(row["kind"] in KINDS and row["kind"] not in contracts, "duplicate/unknown source contract")
        require(row["format"] in (None, "json", "html"), "invalid source format")
        for field in ("identity_rules", "measurement_rules", "enumeration_rules", "limitations"):
            for text in _array(row[field], field):
                _text(text, field)
        _witnesses(row["shape_evidence"], captures, references)
        require(all(w["source"]["kind"] == "request" and captures[w["source"]["request_id"]]["kind"] == row["kind"]
                    for w in row["shape_evidence"]), "shape evidence must resolve its own source kind")
        for citation in _array(row["definition_evidence"], "definition evidence"):
            _object(citation, "url title", "definition citation")
            _text(citation["title"], "definition title")
            require(isinstance(citation["url"], str) and citation["url"].startswith("https://"), "invalid definition url")
        if row["format"] is None:
            require(not row["identity_rules"] and not row["measurement_rules"] and not row["enumeration_rules"]
                    and not row["shape_evidence"] and bool(row["limitations"]), "unobserved source must retain explicit limits and empty unverified rules")
        else:
            require(bool(row["shape_evidence"]) and (bool(row["identity_rules"]) or bool(row["limitations"])), "observed source format requires shape evidence and identity rules or explicit limitations")
        contracts[row["kind"]] = row
    require(set(contracts) == set(KINDS), "exactly three source contracts are required")
    observations = {}
    for row in _array(document["observations"], "observations"):
        _object(row, "season player_id reported_position position_group position_evidence context_evidence source_as_of skating_max_speed_mph skating_bursts_over20_count", "observation")
        _id(row["player_id"])
        key = row["season"], row["player_id"]
        require(row["season"] in selection["seasons"] and key not in observations, "duplicate/out-of-selection observation")
        require(row["reported_position"] is None or isinstance(row["reported_position"], str), "invalid reported position")
        require(row["position_group"] in (None, "f", "d"), "invalid position group")
        _witnesses(row["position_evidence"], captures, references, season=row["season"], player=row["player_id"])
        _witnesses(row["context_evidence"], captures, references, season=row["season"], player=row["player_id"], measurement=True)
        if row["source_as_of"] is not None:
            _timestamp(row["source_as_of"])
        if row["position_group"] is not None:
            require(POSITION_GROUPS.get(row["reported_position"]) == row["position_group"] and bool(row["position_evidence"]), "position group requires compatible reported position/evidence")
            reported = {w["raw_value"] for w in row["position_evidence"] if isinstance(w["raw_value"], str)}
            require(row["reported_position"] in reported and {POSITION_GROUPS.get(p) for p in reported} == {row["position_group"]}, "conflicting/unknown position witnesses cannot establish a group")
        for measurement_id in MEASUREMENTS:
            value = row[measurement_id]
            _measurement(value, measurement_id, captures, references, *key)
            if value["status"] == "available":
                require(bool(row["context_evidence"]), "available measurement requires validated context evidence")
                evidence_kinds = {captures[w["source"]["request_id"]]["kind"] for w in value["evidence"]}
                require(all(contracts[k]["format"] is not None and contracts[k]["measurement_rules"] for k in evidence_kinds), "available measurement requires exercised source contract")
                if value["transformation"] == "sum_disjoint":
                    require(all(contracts[k]["definition_evidence"] for k in evidence_kinds), "disjoint counters require source definition evidence")
            attempts = [c for c in captures.values() if c["kind"] == "detail" and (c["season"], c["player_id"]) == key]
            if attempts:
                attempt = attempts[0]
                expected = "not_requested" if attempt["state"] == "deferred" else "transport_failed" if attempt["state"] == "failed" else "http_unavailable" if not 200 <= attempt["http_status"] <= 299 else None
                if expected is not None:
                    require(value["status"] == expected or value["status"] == "available" and any(captures[w["source"]["request_id"]]["kind"] == "listing" for w in value["evidence"]), "measurement misrepresents selected detail attempt")
        observations[key] = row
    detail_keys = {(row["season"], row["player_id"]) for row in selected.values() if row["kind"] == "detail"}
    require(detail_keys <= observations.keys(), "every requested detail identity requires an observation")
    for key in observations.keys() - detail_keys:
        row = observations[key]
        require(any(captures[w["source"]["request_id"]]["kind"] == "listing" for measurement_id in MEASUREMENTS for w in row[measurement_id]["evidence"]), "additional observations require listing witnesses")
    if document["purpose"] == "real":
        initial = [c for c in captures.values() if c["kind"] == "detail" and c["player_id"] == "8478402"]
        attempted = sorted([c for c in initial if c["state"] != "deferred"], key=lambda c: datetime.fromisoformat(c["requested_at"]))
        stopped, failures = False, 0
        for capture in attempted:
            require(not stopped, "initial request occurred after a 429 or two consecutive transport failures")
            failures = failures + 1 if capture["state"] == "failed" else 0
            stopped = capture["http_status"] == 429 or failures == 2
        require(len(attempted) == 3 or stopped, "initial deferral requires a preceding 429 or two consecutive transport failures")
        require(all(c["state"] == "deferred" for c in captures.values() if c not in initial),
                "optional probes require usable initial aggregate evidence; no supported primary adapter is available")
    _census(document["census"], selection["seasons"], captures, references, observations, contracts)
    return document


def _literal_ids(value):
    """identity witnesses retain literal ids, never ids inferred from text."""
    if isinstance(value, str) and re.fullmatch(r"[0-9]+", value) and int(value) > 0:
        return {value}
    if type(value) is int and value > 0:
        return {str(value)}
    if isinstance(value, list):
        return {str(item) for item in value if type(item) is int and item > 0
                or isinstance(item, str) and re.fullmatch(r"[0-9]+", item) and int(item) > 0}
    return set()


def _census(rows, seasons, captures, references, observations, contracts):
    seen = set()
    for row in _array(rows, "census"):
        _object(row, "season enumeration inclusion_rule reported_total universe_ids observed_listed_ids enumeration_evidence measurements", "season census")
        season = row["season"]
        require(season in seasons and season not in seen, "duplicate/out-of-selection census season")
        seen.add(season)
        require(row["enumeration"] in ("unestablished", "partial", "checked_complete"), "invalid enumeration status")
        require(row["inclusion_rule"] is None or isinstance(row["inclusion_rule"], str) and bool(row["inclusion_rule"].strip()), "invalid inclusion rule")
        require(row["reported_total"] is None or type(row["reported_total"]) is int and row["reported_total"] >= 0, "invalid reported total")
        listed = _ids(row["observed_listed_ids"], "observed listed ids")
        _witnesses(row["enumeration_evidence"], captures, references, season=season, measurement=True)
        require(all(captures[w["source"]["request_id"]]["kind"] == "listing" for w in row["enumeration_evidence"]), "census enumeration requires listing evidence")
        witnessed_ids = {identity for w in row["enumeration_evidence"]
                         if not (type(w["raw_value"]) is int and w["raw_value"] == row["reported_total"])
                         for identity in _literal_ids(w["raw_value"])}
        require(listed <= witnessed_ids, "listed membership requires literal identity witnesses")
        if row["enumeration"] == "unestablished":
            require(row["universe_ids"] is None, "unestablished enumeration cannot assert a universe")
        else:
            require(bool(row["enumeration_evidence"]) and row["inclusion_rule"] is not None, "finite enumeration needs source/qualification evidence")
            require(bool(contracts["listing"]["enumeration_rules"]), "finite enumeration requires an exercised source enumeration rule")
            if row["enumeration"] == "partial":
                require(row["universe_ids"] is None, "incomplete enumeration cannot assert complete membership")
            else:
                universe = _ids(row["universe_ids"], "universe ids")
                require(universe == listed, "complete universe must equal observed unique membership")
                require(row["reported_total"] is None or row["reported_total"] == len(universe), "reported total disagrees with complete membership")
                require(row["reported_total"] is not None or any(w["raw_value"] is None or w["raw_value"] is False
                                                               for w in row["enumeration_evidence"]),
                        "complete enumeration requires reported total or terminal-page evidence")
        if listed:
            require(bool(row["enumeration_evidence"]), "listed membership requires source evidence")
        if row["reported_total"] is not None:
            require(any(w["raw_value"] == row["reported_total"] and type(w["raw_value"]) is int for w in row["enumeration_evidence"]), "reported total needs a literal source witness")
        measurement_ids = set()
        for measurement in _array(row["measurements"], "census measurements"):
            _object(measurement, "measurement_id acquisition eligible exclusions unresolved", "measurement census")
            measurement_id = measurement["measurement_id"]
            require(measurement_id in MEASUREMENTS and measurement_id not in measurement_ids, "duplicate/unknown census measurement")
            measurement_ids.add(measurement_id)
            require(measurement["acquisition"] in ("unestablished", "partial", "checked_complete"), "invalid acquisition status")
            _object(measurement["eligible"], "f d", "eligible groups")
            disposition = set()
            for group in ("f", "d"):
                ids = _ids(measurement["eligible"][group], "eligible ids")
                require(not disposition & ids, "census partitions overlap")
                disposition |= ids
                for player in ids:
                    observation = observations.get((season, player))
                    require(observation is not None and observation["position_group"] == group and observation[measurement_id]["status"] == "available", "eligible id needs available same-season measurement and evidenced position")
            for field in ("exclusions", "unresolved"):
                for entry in _array(measurement[field], field):
                    _object(entry, "player_id position_group reason", "census disposition")
                    _id(entry["player_id"])
                    require(entry["position_group"] in (None, "f", "d"), "invalid disposition position")
                    _text(entry["reason"], "disposition reason")
                    player = entry["player_id"]
                    require(player not in disposition, "duplicate/overlapping census disposition")
                    disposition.add(player)
                    observation = observations.get((season, player))
                    if observation is not None:
                        require(entry["position_group"] == observation["position_group"], "disposition position mismatch")
                    if field == "exclusions":
                        require(observation is not None and (observation[measurement_id]["status"] == "source_null"
                                or observation[measurement_id]["status"] == "available" and observation["position_group"] is None), "exclusion requires source-null or available measurement with unknown/conflicting position")
                    elif observation is not None:
                        require(observation[measurement_id]["status"] not in ("available", "source_null"), "available/null measurement cannot be unresolved acquisition")
            require(disposition == listed, "measurement partitions must exhaust exactly the source-listed subset")
            if measurement["acquisition"] == "checked_complete":
                require(row["enumeration"] == "checked_complete" and not measurement["unresolved"], "complete acquisition requires complete enumeration and no unresolved ids")
            if measurement["acquisition"] == "unestablished":
                require(row["enumeration"] == "unestablished", "finite enumeration has at least partial acquisition")
        require(measurement_ids == set(MEASUREMENTS), "census requires both measurement partitions")
    require(seen == set(seasons), "census requires every selected season")


def read_skating(path, expected_purpose):
    """validate compact facts and evidence links without opening original roots."""
    path = Path(path).resolve(strict=True)
    document = _json(path)
    require(isinstance(document, dict) and isinstance(document.get("selection"), dict), "missing compact selection")
    link = document["selection"]
    _object(link, "original_path sha256 copied_path", "selection link")
    require(isinstance(link["original_path"], str) and Path(link["original_path"]).is_absolute(), "selection original path must be absolute")
    require(link["copied_path"] == "selection.json", "invalid copied selection path")
    _digest(link["sha256"])
    copied = path.parent / "selection.json"
    require(_hash(copied) == link["sha256"], "copied selection hash mismatch")
    return _validate(document, _selection(_json(copied)), expected_purpose)


def _positions(selection, base):
    positions = {}
    require("positionCode" in BIO_SKATER_SOURCE_FIELDS, "reference owner no longer defines skater positionCode")
    for reference in selection["position_references"]:
        directory = base / reference["directory"]
        capture = read_reference_capture(directory, "skater-bios")
        require(_hash(capture.capture_path) == reference["receipt_sha256"] and capture.body_sha256 == reference["body_sha256"], "position reference digest mismatch")
        require(capture.requested_season == reference["season"] and capture.body is not None, "position reference season/unavailable mismatch")
        try:
            body = strict_json(capture.body)
        except (ValueError, UnicodeError) as error:
            raise InputContractError("invalid position-reference json") from error
        require(isinstance(body, dict) and isinstance(body.get("data"), list), "position reference needs a data array")
        for index, row in enumerate(body["data"]):
            require(isinstance(row, dict), "position reference row must be an object")
            player = row.get("playerId")
            if type(player) is not int or player <= 0:
                continue
            position = row.get("positionCode")
            if position is not None and not isinstance(position, str):
                position = None
            witness = dict(source=dict(kind="position_reference", season=reference["season"]),
                           locator=dict(kind="json_pointer", value=f"/data/{index}/positionCode"), raw_value=row.get("positionCode"))
            positions.setdefault((reference["season"], str(player)), []).append((position, witness))
    return positions


def _inspect_detail(body, request_id):
    """retain only literal paths exercised in the three original primary bodies.

    these event witnesses cannot establish player-season aggregate context.
    raw counters remain separate: no captured definition proves disjoint bins.
    """
    try:
        document = strict_json(body)
    except (ValueError, UnicodeError):
        return None
    if not isinstance(document, dict) or not isinstance(document.get("skatingSpeedDetails"), dict):
        return None
    details = document["skatingSpeedDetails"]
    if not isinstance(details.get("maxSkatingSpeed"), dict) or not isinstance(document.get("topSkatingSpeeds"), list):
        return None
    source = dict(kind="request", request_id=request_id)

    def witness(pointer, value):
        return dict(source=source.copy(), locator=dict(kind="json_pointer", value=pointer), raw_value=value)

    maximum = details["maxSkatingSpeed"]
    speed = [witness("/skatingSpeedDetails/maxSkatingSpeed/imperial", maximum["imperial"])] if "imperial" in maximum else []
    bursts = []
    for name in ("bursts20To22", "burstsOver22"):
        counter = details.get(name)
        if isinstance(counter, dict) and "value" in counter:
            bursts.append(witness(f"/skatingSpeedDetails/{name}/value", counter["value"]))
    context = []
    overlay = maximum.get("overlay")
    if isinstance(overlay, dict):
        for field in ("gameDate", "gameType", "player"):
            if field in overlay:
                context.append(witness("/skatingSpeedDetails/maxSkatingSpeed/overlay/" + field, overlay[field]))
    for index, event in enumerate(document["topSkatingSpeeds"]):
        if isinstance(event, dict):
            for field in ("gameCenterLink", "gameDate", "gameType"):
                if field in event:
                    context.append(witness(f"/topSkatingSpeeds/{index}/{field}", event[field]))
    if not speed and not bursts:
        return None
    return dict(speed=speed, bursts=bursts, context=context)


def bind_skating(selection_path, output):
    """validate original selected evidence, then write one exclusive compact result."""
    original = Path(selection_path).resolve(strict=True)
    original_bytes = original.read_bytes()
    selection = _selection(_json(original))
    base = original.parent
    output = Path(output).resolve()
    require(not output.exists(), "output directory is occupied")
    captures, inspected = [], {}
    for request in selection["requests"]:
        row = {key: request[key] for key in ("request_id", "kind", "season", "player_id")}
        row.update(url=skating_url(*_key(request)), requested_at=None, http_status=None, state="deferred",
                   receipt_path=None, receipt_sha256=None, body_sha256=None, origin=None,
                   failure=None, deferred_reason=request["deferred_reason"])
        selected = request["capture"]
        if selected is not None:
            capture = read_skating_capture(base / selected["directory"], request["kind"])
            require(_hash(capture.capture_path) == selected["receipt_sha256"], "selected skating receipt hash mismatch")
            metadata = _json(capture.capture_path)
            require(metadata.get("seasonId") == request["season"] and metadata.get("playerId") == request["player_id"], "selected skating receipt identity mismatch")
            row.update(requested_at=capture.requested_at, http_status=capture.http_status, state=metadata["state"],
                       receipt_path=str(capture.capture_path), receipt_sha256=selected["receipt_sha256"],
                       body_sha256=capture.body_sha256, origin=selected["origin"], failure=metadata["failure"])
            if request["kind"] == "detail" and capture.body is not None and 200 <= capture.http_status <= 299:
                inspection = _inspect_detail(capture.body, request["request_id"])
                if inspection is not None:
                    inspected[request["request_id"]] = inspection
        captures.append(row)
    positions = _positions(selection, base)
    observations = []
    for capture in captures:
        if capture["kind"] != "detail":
            continue
        state, status = capture["state"], capture["http_status"]
        if state == "deferred":
            measurement_status, reason = "not_requested", capture["deferred_reason"]
        elif state == "failed":
            measurement_status = "transport_failed"
            reason = f"{capture['failure']['kind']}: {capture['failure']['message']}"
        elif not 200 <= status <= 299:
            measurement_status, reason = "http_unavailable", f"http {status}; no usable primary measurement body"
        elif capture["request_id"] in inspected:
            measurement_status = "context_unresolved"
            reason = "recorded scalars and maximum-event witnesses do not establish aggregate player identity, full-season coverage or regular-season/all-situations scope"
        else:
            measurement_status, reason = "schema_unresolved", "no primary measurement shape has been exercised; this response is not interpreted"
        reports = positions.get((capture["season"], capture["player_id"]), [])
        reported = {position for position, witness in reports}
        position = next(iter(reported)) if len(reported) == 1 else None
        group = POSITION_GROUPS.get(position) if all(POSITION_GROUPS.get(p) is not None for p in reported) else None
        groups = {POSITION_GROUPS.get(p) for p in reported}
        if len(groups) != 1:
            group = None
        if position is None:
            group = None
        inspection = inspected.get(capture["request_id"])
        row = dict(season=capture["season"], player_id=capture["player_id"], reported_position=position,
                   position_group=group, position_evidence=[w for p, w in reports],
                   context_evidence=inspection["context"] if inspection else [], source_as_of=None)
        for measurement_id in MEASUREMENTS:
            evidence = inspection["speed" if measurement_id == "skating_max_speed_mph" else "bursts"] if inspection else []
            measurement_reason = reason + "; burst category definitions and disjointness are also unverified" if inspection and measurement_id == "skating_bursts_over20_count" else reason
            row[measurement_id] = dict(value=None, status=measurement_status, reason=measurement_reason, evidence=evidence, transformation=None)
        observations.append(row)
    contracts = [dict(kind=kind, format=None, identity_rules=[], measurement_rules=[], enumeration_rules=[],
                      shape_evidence=[], definition_evidence=[], limitations=["no usable primary measurement or census structure has been observed"])
                 for kind in KINDS]
    if inspected:
        contracts[0].update(format="json", shape_evidence=[w for inspection in inspected.values()
                            for field in ("speed", "bursts") for w in inspection[field]],
                            limitations=["literal scalar and maximum-event paths are observed; aggregate player id, season and regular-season/all-situations coverage are not established",
                                         "burst category definitions and disjointness are unverified; no counters are added",
                                         "no available primary measurement adapter is established"])
    census = [dict(season=season, enumeration="unestablished", inclusion_rule=None, reported_total=None,
                   universe_ids=None, observed_listed_ids=[], enumeration_evidence=[],
                   measurements=[dict(measurement_id=m, acquisition="unestablished", eligible=dict(f=[], d=[]),
                                      exclusions=[], unresolved=[]) for m in MEASUREMENTS]) for season in selection["seasons"]]
    document = dict(schema_version=1, purpose=selection["purpose"], implementation=implementation_identity(),
                    selection=dict(original_path=str(original), sha256=hashlib.sha256(original_bytes).hexdigest(), copied_path="selection.json"),
                    adapter_status="not_observed", captures=captures, source_contracts=contracts, observations=observations, census=census)
    _validate(document, selection, selection["purpose"])
    output.mkdir(parents=True, exist_ok=False)
    with (output / "selection.json").open("xb") as target:
        target.write(original_bytes)
    write_json(output / "skating.json", document)
    return output / "skating.json"


def skating_counts(document):
    """counts come from unique identities; unknown source denominators stay null."""
    rows = []
    for census in document["census"]:
        season = census["season"]
        for measurement in census["measurements"]:
            measurement_id = measurement["measurement_id"]
            dispositions = {player: group for group in ("f", "d") for player in measurement["eligible"][group]}
            dispositions.update({row["player_id"]: row["position_group"] for field in ("exclusions", "unresolved") for row in measurement[field]})
            for group in ("f", "d", None):
                listed = {player for player, position in dispositions.items() if position == group}
                observations = [row for row in document["observations"] if row["season"] == season and row["player_id"] in listed]
                rows.append(dict(season=season, measurement_id=measurement_id, position_group=group,
                                 universe=len(listed) if census["universe_ids"] is not None else None,
                                 listed=len(listed),
                                 acquired=sum(row[measurement_id]["status"] not in ("not_requested", "http_unavailable", "transport_failed") for row in observations),
                                 available=sum(row[measurement_id]["status"] == "available" for row in observations),
                                 excluded=sum(row["position_group"] == group for row in measurement["exclusions"]),
                                 unresolved=sum(row["position_group"] == group for row in measurement["unresolved"])))
    return rows


def main():
    parser = argparse.ArgumentParser(description="bind selected skating feasibility evidence offline", allow_abbrev=False)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--out", required=True)
    for flag in ("--selection", "--out"):
        if sum(argument.split("=", 1)[0] == flag for argument in sys.argv[1:]) > 1:
            parser.error(f"duplicate flag {flag}")
    args = parser.parse_args()
    try:
        path = bind_skating(args.selection, args.out)
        document = read_skating(path, _json(path)["purpose"])
        counts = skating_counts(document)
    except (InputContractError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"inspected {sum(c['state'] != 'deferred' for c in document['captures'])} attempts; usable measurements: "
          f"{sum(row[m]['status'] == 'available' for row in document['observations'] for m in MEASUREMENTS)}; adapter: {document['adapter_status']}")
    if any(row[m]["status"] == "context_unresolved" for row in document["observations"] for m in MEASUREMENTS):
        print("detail json and raw candidates observed; aggregate player-season context unresolved")
    print(f"population: unestablished; compact evidence: {path}")
    print("source-listed peer counts (position_group=None means unknown position):")
    for row in counts:
        print(" ".join(f"{key}={value}" for key, value in row.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
