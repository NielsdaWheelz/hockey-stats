"""goal-blind study membership over unchanged prepared source dispositions."""

from collections import Counter
from copy import deepcopy
from datetime import date
import hashlib
import json

from .captures import InputContractError
from .chance_features import (
    PREPARATION_IDENTITY, FeatureUnavailableError, encode_stage_inputs,
    requirement_reason_prefix, stage_design,
)

SOURCE_STATUSES = ("eligible", "out_of_scope", "unavailable")
STUDY_INCLUSIONS = (
    "included", "feature_unavailable", "not_applicable", "source_excluded",
)
QUANTITIES = ("unblocked_conversion", "all_attempt_recorded_context")
OMISSION_REASON_ACCOUNTING = (
    "one disjoint joint missing-field/status/reason pattern per omitted attempt; "
    "exact evidence locators remain in cohort rows"
)


def _definition(required_families):
    if required_families not in ([], ["sequence"]):
        raise InputContractError("cohort requirements must be [] or ['sequence']")
    return dict(
        mode="selected_family_complete" if required_families else "all_source_eligible",
        required_families=required_families.copy(),
    )


def _counts(rows):
    sources = Counter(row["source_status"] for row in rows)
    inclusions = Counter(row["study_inclusion"] for row in rows)
    return dict(
        source_statuses={status: sources[status] for status in SOURCE_STATUSES},
        study_inclusions={status: inclusions[status] for status in STUDY_INCLUSIONS},
        source_applicable_count=inclusions["included"] + inclusions["feature_unavailable"],
        included_count=inclusions["included"],
        excluded_count=inclusions["feature_unavailable"],
    )


def component_cohort(prepared, *, quantity, required_families):
    """classify every recognized row without inspecting focal outcomes or predictions."""
    if quantity not in QUANTITIES:
        raise InputContractError("unsupported component cohort quantity")
    definition = _definition(required_families)
    if required_families and quantity != "unblocked_conversion":
        raise InputContractError("selected-family cohort requires unblocked conversion")
    if (
        set(prepared["feature_games"]) != set(prepared["game_dates"])
        or set(prepared["feature_player_games"]) != set(prepared["game_dates"])
        or any(not isinstance(prepared[table][game_id], dict)
               for table in ("feature_games", "feature_player_games")
               for game_id in prepared["game_dates"])
    ):
        raise InputContractError("prepared cohort game/player joins disagree with selected games")
    if required_families:
        core = dict(prefix=[], suffix=[], cells=0, slices={})
        baseline = stage_design(
            "r", ["game_additive", "recent_additive", "recent_interactions"],
            core_layout=core, trait_assumptions=[],
        )
        requirements = stage_design(
            "r", required_families, core_layout=core, trait_assumptions=[],
        )
    rows, by_game = [], {game_id: [] for game_id in prepared["game_dates"]}
    seen = set()
    for attempt in prepared["attempts"]:
        game_id, source_index = attempt["game_id"], attempt["source_index"]
        key = game_id, source_index
        if (
            game_id not in by_game or key in seen or type(source_index) is not int
            or source_index < 0 or attempt["status"] not in SOURCE_STATUSES
            or not isinstance(attempt["reasons"], list)
            or any(not isinstance(reason, str) for reason in attempt["reasons"])
            or type(attempt["blocked"]) is not bool
        ):
            raise InputContractError(f"{game_id}:{source_index}: invalid cohort source row")
        seen.add(key)
        inclusion, reasons = "source_excluded", []
        if attempt["status"] == "eligible":
            inclusion = "not_applicable" if quantity == "unblocked_conversion" and attempt["blocked"] else "included"
            if inclusion == "included" and required_families:
                facts = dict(
                    game_facts=prepared["feature_games"].get(game_id, {}),
                    player_game_facts=prepared["feature_player_games"].get(game_id, {}),
                )
                encode_stage_inputs(attempt, baseline, **facts)
                try:
                    encode_stage_inputs(attempt, requirements, **facts)
                except FeatureUnavailableError as error:
                    inclusion, reasons = "feature_unavailable", error.reasons.copy()
        row = dict(
            game_id=game_id, source_index=source_index, event_id=attempt["event_id"],
            source_status=attempt["status"], source_reasons=attempt["reasons"].copy(),
            study_inclusion=inclusion, study_reasons=reasons,
        )
        rows.append(row)
        by_game[game_id].append(row)
    document = dict(
        schema_version=1, purpose=prepared["purpose"], quantity=quantity,
        definition=definition, selection=deepcopy(prepared["selection"]),
        inputs=deepcopy(prepared["inputs"]),
        preparation_identity=deepcopy(prepared["preparation_identity"]),
        game_dates=dict(prepared["game_dates"]), rows=rows, counts=_counts(rows),
        per_game=[dict(game_id=game_id, game_date=game_date, **_counts(by_game[game_id]))
                  for game_id, game_date in prepared["game_dates"].items()],
        membership_sha256=hashlib.sha256(json.dumps(
            rows, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest(),
    )
    return validate_cohort_document(document)


def validate_cohort_document(cohort):
    """check the saved membership contract; source joins require validate_cohort."""
    try:
        fields = {
            "schema_version", "purpose", "quantity", "definition", "selection",
            "inputs", "preparation_identity", "game_dates", "rows", "counts",
            "per_game", "membership_sha256",
        }
        if (
            not isinstance(cohort, dict) or set(cohort) != fields
            or type(cohort["schema_version"]) is not int or cohort["schema_version"] != 1
            or cohort["purpose"] not in ("research", "fixture_exercise")
            or cohort["quantity"] not in QUANTITIES
            or not isinstance(cohort["definition"], dict)
            or cohort["definition"] != _definition(cohort["definition"]["required_families"])
            or cohort["definition"]["required_families"] and cohort["quantity"] != "unblocked_conversion"
            or cohort["preparation_identity"] != PREPARATION_IDENTITY
        ):
            raise ValueError("cohort schema, definition or preparation disagree")
        selection = cohort["selection"]
        if (
            not isinstance(selection, dict)
            or set(selection) != {"schema_version", "purpose", "corpora", "history_corpora"}
            or type(selection["schema_version"]) is not int or selection["schema_version"] != 2
            or selection["purpose"] != cohort["purpose"]
            or not isinstance(selection["corpora"], list) or not selection["corpora"]
            or not isinstance(selection["history_corpora"], list)
            or any(not isinstance(path, str) or not path for path in selection["history_corpora"])
            or len(set(selection["history_corpora"])) != len(selection["history_corpora"])
        ):
            raise ValueError("invalid cohort selection")
        selected = []
        for corpus in selection["corpora"]:
            if (
                not isinstance(corpus, dict) or set(corpus) != {"path", "game_ids"}
                or not isinstance(corpus["path"], str) or not corpus["path"]
                or not isinstance(corpus["game_ids"], list) or not corpus["game_ids"]
            ):
                raise ValueError("invalid selected corpus")
            selected.extend(corpus["game_ids"])
        dates = cohort["game_dates"]
        if (
            not isinstance(dates, dict) or not dates or list(dates) != selected
            or len(set(selected)) != len(selected)
        ):
            raise ValueError("cohort game ledger disagrees with selection")
        for game_id, value in dates.items():
            if (
                not isinstance(game_id, str) or len(game_id) != 10 or not game_id.isdigit()
                or not isinstance(value, str) or date.fromisoformat(value).isoformat() != value
            ):
                raise ValueError("invalid cohort game identity/date")
        if not isinstance(cohort["inputs"], list) or not cohort["inputs"]:
            raise ValueError("missing cohort input identities")
        for identity in cohort["inputs"]:
            digest = identity["sha256"]
            if (
                not isinstance(identity, dict) or set(identity) != {"path", "kind", "sha256"}
                or identity["kind"] not in ("selection", "corpus", "game")
                or not isinstance(identity["path"], str) or not identity["path"]
                or not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
            ):
                raise ValueError("invalid cohort input identity")
        if not isinstance(cohort["rows"], list):
            raise ValueError("cohort rows must be an array")
        by_game, positions, previous = {gid: [] for gid in dates}, {gid: i for i, gid in enumerate(dates)}, (-1, -1)
        for row in cohort["rows"]:
            if (
                not isinstance(row, dict) or set(row) != {
                    "game_id", "source_index", "event_id", "source_status", "source_reasons",
                    "study_inclusion", "study_reasons",
                }
                or row["game_id"] not in by_game
                or type(row["source_index"]) is not int or row["source_index"] < 0
                or row["event_id"] is not None and type(row["event_id"]) is not int
                or row["source_status"] not in SOURCE_STATUSES
                or row["study_inclusion"] not in STUDY_INCLUSIONS
                or any(not isinstance(row[field], list) or
                       any(not isinstance(reason, str) or not reason for reason in row[field])
                       for field in ("source_reasons", "study_reasons"))
            ):
                raise ValueError("invalid cohort row")
            position = positions[row["game_id"]], row["source_index"]
            if position <= previous:
                raise ValueError("duplicate or reordered cohort row")
            previous = position
            inclusion = row["study_inclusion"]
            if (
                (row["source_status"] != "eligible") != (inclusion == "source_excluded")
                or bool(row["study_reasons"]) != (inclusion == "feature_unavailable")
                or inclusion == "feature_unavailable" and cohort["definition"]["mode"] != "selected_family_complete"
                or inclusion == "not_applicable" and cohort["quantity"] != "unblocked_conversion"
            ):
                raise ValueError("cohort source/study dispositions disagree")
            by_game[row["game_id"]].append(row)
        expected_per_game = [dict(game_id=gid, game_date=value, **_counts(by_game[gid]))
                             for gid, value in dates.items()]
        if (
            json.dumps(cohort["counts"], sort_keys=True, allow_nan=False) !=
            json.dumps(_counts(cohort["rows"]), sort_keys=True, allow_nan=False)
            or json.dumps(cohort["per_game"], sort_keys=True, allow_nan=False) !=
            json.dumps(expected_per_game, sort_keys=True, allow_nan=False)
        ):
            raise ValueError("cohort counts/game accounting disagree")
        digest = hashlib.sha256(json.dumps(
            cohort["rows"], sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
        if cohort["membership_sha256"] != digest:
            raise ValueError("cohort membership digest disagrees")
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
        raise InputContractError(f"invalid component cohort: {error}") from error
    return cohort


def validate_cohort(cohort, prepared):
    """bind exact source order, identities and dispositions to current prepared facts."""
    validate_cohort_document(cohort)
    expected = component_cohort(
        prepared, quantity=cohort["quantity"],
        required_families=cohort["definition"]["required_families"],
    )
    if cohort != expected:
        raise InputContractError("component cohort differs from prepared identities or membership")
    return cohort


def source_outcome_counts(prepared, cohort):
    """count source-bound observed outcomes after blind membership is fixed."""
    validate_cohort_document(cohort)
    if any(cohort[field] != prepared[field] for field in (
        "purpose", "selection", "inputs", "preparation_identity", "game_dates",
    )):
        raise InputContractError("outcome audit prepared identities differ from cohort")
    seasons = {game["game_id"]: game["season"] for game in prepared["games"]}
    records = {
        season: dict(
            season=season, games=sum(value == season for value in seasons.values()),
            recognized_count=0, source_eligible_count=0,
            source_statuses=dict.fromkeys(SOURCE_STATUSES, 0),
            study_inclusions=dict.fromkeys(STUDY_INCLUSIONS, 0),
            source_applicable=dict(attempts=0, goals=0),
            included=dict(attempts=0, goals=0), omitted=dict(attempts=0, goals=0),
        ) for season in dict.fromkeys(seasons.values())
    }
    try:
        for attempt, membership in zip(prepared["attempts"], cohort["rows"], strict=True):
            if (
                any(attempt[field] != membership[field] for field in
                    ("game_id", "source_index", "event_id"))
                or attempt["status"] != membership["source_status"]
                or attempt["reasons"] != membership["source_reasons"]
                or type(attempt["goal"]) is not bool or type(attempt["blocked"]) is not bool
                or attempt["goal"] and attempt["blocked"]
            ):
                raise InputContractError("outcome audit raw/source join differs from cohort")
            record = records[seasons[attempt["game_id"]]]
            source, inclusion = membership["source_status"], membership["study_inclusion"]
            record["recognized_count"] += 1
            record["source_eligible_count"] += source == "eligible"
            record["source_statuses"][source] += 1
            record["study_inclusions"][inclusion] += 1
            if inclusion not in ("included", "feature_unavailable"):
                continue
            population = "included" if inclusion == "included" else "omitted"
            for name in ("source_applicable", population):
                record[name]["attempts"] += 1
                record[name]["goals"] += int(attempt["goal"])
    except (KeyError, ValueError) as error:
        raise InputContractError(f"invalid outcome audit source join: {error}") from error
    counts = cohort["counts"]
    return dict(
        recognized_count=len(cohort["rows"]), source_eligible_count=counts["source_statuses"]["eligible"],
        source_statuses=deepcopy(counts["source_statuses"]),
        study_inclusions=deepcopy(counts["study_inclusions"]),
        **{population: {field: sum(record[population][field] for record in records.values())
                        for field in ("attempts", "goals")}
           for population in ("source_applicable", "included", "omitted")},
        per_season=list(records.values()),
    )


def outcome_audit(prepared, cohort):
    """enrich source outcome counts with disjoint prepared missingness patterns."""
    audit = source_outcome_counts(prepared, cohort)
    seasons = {game["game_id"]: game["season"] for game in prepared["games"]}
    records = {record["season"]: record for record in audit["per_season"]}
    for record in records.values():
        record["omission_reasons"] = {}
    for attempt, membership in zip(prepared["attempts"], cohort["rows"], strict=True):
        if membership["study_inclusion"] != "feature_unavailable":
            continue
        sequence = attempt["feature_facts"]["sequence"]
        missing = tuple(
            (field, sequence["problems"][field]["status"], sequence["problems"][field]["reason"])
            for field in ("defender_sequence_index", "defender_sequence_age_seconds")
            if sequence["values"][field] is None
        )
        if not missing:
            raise InputContractError("omitted sequence row has no missing prepared requirement")
        record = records[seasons[attempt["game_id"]]]
        value = record["omission_reasons"].setdefault(missing, dict(
            requirements=[dict(field=field, status=status, reason=reason) for field, status, reason in missing],
            attempts=0, goals=0,
        ))
        value["attempts"] += 1
        value["goals"] += int(attempt["goal"])
    omission_reasons = {}
    for record in records.values():
        for missing, value in record["omission_reasons"].items():
            total = omission_reasons.setdefault(missing, dict(requirements=deepcopy(value["requirements"]), attempts=0, goals=0))
            total["attempts"] += value["attempts"]
            total["goals"] += value["goals"]
        record["omission_reasons"] = list(record["omission_reasons"].values())
    audit.update(
        omission_reasons=list(omission_reasons.values()),
        omission_reason_accounting=OMISSION_REASON_ACCOUNTING,
    )
    return audit


def validate_outcome_audit_document(audit, cohort):
    """check compact outcome and disjoint missingness summaries against blind counts."""
    try:
        counts = cohort["counts"]
        scalar_fields = ("recognized_count", "source_eligible_count")
        populations = ("source_applicable", "included", "omitted")
        fields = {*scalar_fields, "source_statuses", "study_inclusions", *populations,
                  "per_season", "omission_reasons", "omission_reason_accounting"}
        if (
            not isinstance(audit, dict) or set(audit) != fields
            or audit["omission_reason_accounting"] != OMISSION_REASON_ACCOUNTING
            or not isinstance(audit["per_season"], list) or not audit["per_season"]
            or len({record["season"] for record in audit["per_season"]}) != len(audit["per_season"])
            or audit["recognized_count"] != len(cohort["rows"])
            or audit["source_statuses"] != counts["source_statuses"]
            or audit["study_inclusions"] != counts["study_inclusions"]
            or audit["source_applicable"]["attempts"] != counts["source_applicable_count"]
            or audit["included"]["attempts"] != counts["included_count"]
            or audit["omitted"]["attempts"] != counts["excluded_count"]
        ):
            raise ValueError("outcome audit and blind cohort accounting disagree")
        aggregated_patterns = {}
        for record in [audit] + audit["per_season"]:
            if record is not audit and (
                set(record) != {*scalar_fields, "source_statuses", "study_inclusions", *populations,
                                "season", "games", "omission_reasons"}
                or not isinstance(record["season"], str) or not record["season"]
                or type(record["games"]) is not int or record["games"] <= 0
            ):
                raise ValueError("invalid outcome audit season ledger")
            if (
                any(type(record[field]) is not int or record[field] < 0 for field in scalar_fields)
                or set(record["source_statuses"]) != set(SOURCE_STATUSES)
                or set(record["study_inclusions"]) != set(STUDY_INCLUSIONS)
                or any(type(value) is not int or value < 0 for field in ("source_statuses", "study_inclusions")
                       for value in record[field].values())
                or record["recognized_count"] != sum(record["source_statuses"].values())
                or record["recognized_count"] != sum(record["study_inclusions"].values())
                or record["source_eligible_count"] != record["source_statuses"]["eligible"]
            ):
                raise ValueError("invalid outcome audit source counts")
            for population in populations:
                value = record[population]
                if (
                    set(value) != {"attempts", "goals"}
                    or any(type(value[field]) is not int for field in ("attempts", "goals"))
                    or not 0 <= value["goals"] <= value["attempts"]
                ):
                    raise ValueError("invalid outcome audit binary counts")
            if (
                any(record["source_applicable"][field] != record["included"][field] + record["omitted"][field]
                    for field in ("attempts", "goals"))
                or record["included"]["attempts"] != record["study_inclusions"]["included"]
                or record["omitted"]["attempts"] != record["study_inclusions"]["feature_unavailable"]
                or not isinstance(record["omission_reasons"], list)
            ):
                raise ValueError("outcome audit populations do not reconcile")
            patterns = {}
            for pattern in record["omission_reasons"]:
                if (
                    not isinstance(pattern, dict) or set(pattern) != {"requirements", "attempts", "goals"}
                    or type(pattern["attempts"]) is not int or type(pattern["goals"]) is not int
                    or not 0 <= pattern["goals"] <= pattern["attempts"] or pattern["attempts"] == 0
                    or not isinstance(pattern["requirements"], list) or not pattern["requirements"]
                ):
                    raise ValueError("invalid missing-requirement pattern counts")
                missing = []
                for requirement in pattern["requirements"]:
                    if (
                        not isinstance(requirement, dict) or set(requirement) != {"field", "status", "reason"}
                        or requirement["field"] not in ("defender_sequence_index", "defender_sequence_age_seconds")
                        or requirement["status"] not in ("unavailable", "conflict", "not_applicable")
                        or not isinstance(requirement["reason"], str) or not requirement["reason"]
                    ):
                        raise ValueError("invalid missing-requirement pattern vocabulary")
                    missing.append(tuple(requirement[field] for field in ("field", "status", "reason")))
                key = tuple(missing)
                if (
                    key in patterns
                    or [item[0] for item in key] not in (
                        ["defender_sequence_index"], ["defender_sequence_age_seconds"],
                        ["defender_sequence_index", "defender_sequence_age_seconds"],
                    )
                ):
                    raise ValueError("duplicate or reordered missing-requirement pattern")
                patterns[key] = (pattern["attempts"], pattern["goals"])
                if record is not audit:
                    previous = aggregated_patterns.get(key, (0, 0))
                    aggregated_patterns[key] = tuple(a + b for a, b in zip(previous, patterns[key], strict=True))
            if any(sum(value[index] for value in patterns.values()) != record["omitted"][field]
                   for index, field in enumerate(("attempts", "goals"))):
                raise ValueError("disjoint patterns do not reconcile to omitted outcomes")
            if record is audit:
                global_patterns = patterns
        if global_patterns != aggregated_patterns or sum(record["games"] for record in audit["per_season"]) != len(cohort["game_dates"]):
            raise ValueError("audit season patterns or game counts do not reconcile")
        for field in scalar_fields:
            if sum(record[field] for record in audit["per_season"]) != audit[field]:
                raise ValueError("audit season source counts do not reconcile")
        for field in ("source_statuses", "study_inclusions"):
            if any(sum(record[field][status] for record in audit["per_season"]) != value
                   for status, value in audit[field].items()):
                raise ValueError("audit season disposition counts do not reconcile")
        for population in populations:
            if any(sum(record[population][field] for record in audit["per_season"]) != audit[population][field]
                   for field in ("attempts", "goals")):
                raise ValueError("audit season binary counts do not reconcile")
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise InputContractError(f"invalid component outcome audit: {error}") from error
    return audit


def validate_outcome_audit(audit, prepared, cohort):
    """reconcile saved pattern labels and goals to source-bound row evidence."""
    validate_outcome_audit_document(audit, cohort)
    expected = source_outcome_counts(prepared, cohort)
    actual = {field: audit[field] for field in expected if field != "per_season"}
    actual["per_season"] = [{field: value for field, value in record.items() if field != "omission_reasons"}
                            for record in audit["per_season"]]
    if json.dumps(actual, sort_keys=True, allow_nan=False) != json.dumps(expected, sort_keys=True, allow_nan=False):
        raise InputContractError("outcome audit binary counts differ from source-bound stream")
    seasons = {game["game_id"]: game["season"] for game in prepared["games"]}
    patterns = audit["omission_reasons"]
    counted = Counter()
    for attempt, membership in zip(prepared["attempts"], cohort["rows"], strict=True):
        if membership["study_inclusion"] != "feature_unavailable":
            continue
        key = f"{membership['game_id']}:{membership['source_index']}:r.sequence"
        matching = [index for index, pattern in enumerate(patterns)
                    if len(pattern["requirements"]) == len(membership["study_reasons"]) and all(
                        reason.startswith(requirement_reason_prefix(
                            key, requirement["field"], status=requirement["status"], reason=requirement["reason"],
                        )) for requirement, reason in zip(pattern["requirements"], membership["study_reasons"], strict=True))]
        if len(matching) != 1:
            raise InputContractError("audit requirement pattern differs from located cohort missingness evidence")
        index, season = matching[0], seasons[attempt["game_id"]]
        counted[season, index, "attempts"] += 1
        counted[season, index, "goals"] += int(attempt["goal"])
    for record in audit["per_season"]:
        for pattern in record["omission_reasons"]:
            index = next(i for i, value in enumerate(patterns)
                         if value["requirements"] == pattern["requirements"])
            if any(counted[record["season"], index, field] != pattern[field] for field in ("attempts", "goals")):
                raise InputContractError("audit pattern outcomes differ from source-bound stream")
    return audit
