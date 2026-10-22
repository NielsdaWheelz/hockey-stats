"""02d's offline, complete-bundle source recovery selection."""

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time

from hockey_stats.artifacts import (
    artifact, clean_implementation, json_values, linked_path, require, resources, write_json,
)
from hockey_stats.captures import InputContractError, SOURCES, read_capture
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.corpus_inputs import IDENTITY_FIELDS, load_corpus, read_document
from hockey_stats.interpret import interpret_game
from hockey_stats.observed import observe_game
from hockey_stats.reconstruct import reconstruct_game


POLICY_ID = "strict_interior_other_strength_v1"
PROBES = ("2024021235", "2024021263", "2024021291")
TARGETS = tuple(str(value) for value in range(2024021235, 2024021292))
SPEC = Path(__file__).resolve().parents[2] / "docs/specs/02d-source-exposure-consistency.md"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _original(path):
    corpus, inventory, ledger = load_corpus(path, [])
    require(corpus.get("purpose") != "fixture" and len(inventory) == 1312
            and corpus["reference"]["requested_season"] == "20242025",
            "recovery requires the original real 2024–25 1,312-game corpus")
    require(set(TARGETS) <= inventory.keys(), "recovery targets absent from inventory")
    require(all(row["status"] == "reconstructed" and row["output_path"]
                for row in ledger.values()), "original corpus contains unreviewed native games")
    require(all(Path(row["capture_path"]).is_absolute()
                and "fixtures" not in Path(row["capture_path"]).parts for row in ledger.values()),
            "real recovery cannot select fixture captures")
    ordered = sorted(inventory, key=lambda gid: (inventory[gid]["game_date"], gid))
    return corpus, inventory, ledger, ordered


def _source_receipts(directory, game_id, interpreted):
    sources = {row["source"]: row for row in interpreted["inputs"]}
    require(set(sources) == set(SOURCES), "interpreted sources differ from complete bundle")
    rows = []
    for source in SOURCES:
        require(not (directory / source).is_symlink()
                and not (directory / source / "capture.json").is_symlink()
                and not (directory / source / "body.bin").is_symlink(),
                f"{directory}/{source}: complete bundles cannot mix source leaves")
        capture = read_capture(directory, source)
        require(capture.capture_path.is_file(), f"{directory}/{source}: complete bundle receipt absent")
        require(capture.requested_game_id == game_id, f"{capture.capture_path}: requested game differs")
        metadata = read_json(capture.capture_path)
        observed = sources[source]
        require(Path(observed["capture_path"]).resolve(strict=True) == capture.capture_path
                and observed["body_sha256"] == capture.body_sha256
                and observed["requested_at"] == capture.requested_at
                and observed["http_status"] == capture.http_status,
                f"{capture.capture_path}: native/source provenance differs")
        body = directory / source / "body.bin"
        rows.append(dict(source=source, receipt=identity(capture.capture_path),
            body=identity(body) if capture.body_sha256 is not None else None,
            state=metadata["state"], requested_at=capture.requested_at,
            http_status=capture.http_status, status=observed["status"], reason=observed["reason"]))
    return rows


def _support_reason(support):
    if support is None:
        return "identity_unavailable"
    if support["game"]["included_seconds"] == 0:
        return "no_retained_matched_time"
    if support["included_attempts"] == 0:
        return "no_retained_matched_attempt"
    return "matched_time_and_attempt"


def _review(directory, entry, envelope, envelope_path, output, producer):
    """admit native contracts before considering support; null identity is a gap."""
    game_id = entry["game_id"]
    interpreted = envelope["interpreted"]
    require(interpreted["requested_game_id"] == game_id, "requested game/inventory disagreement")
    sources = _source_receipts(directory, game_id, interpreted)
    game = interpreted["game"]
    if game is None:
        support = None
        receipt = None
    else:
        require(all(game[field] == entry[field] for field in IDENTITY_FIELDS),
                f"{directory}: admitted game identity conflicts with inventory")
        observed, players, _, _, receipt, _ = observe_game(entry, envelope, envelope_path, [])
        included = [row for row in receipt["event_dispositions"] if row["status"] == "included"]
        require(all(not receipt["segments"][row["segment_index"]]["excluded_reasons"] for row in included),
                "included recovery attempt assigned to excluded segment")
        support = dict(game=json_values(asdict(observed)), player_rows=len(players),
            included_attempts=len(included), link_counts=dict(Counter(
                row["match_status"] for row in envelope["reconstruction"]["events"] or [])),
            event_dispositions=dict(Counter(row["status"] for row in receipt["event_dispositions"])),
            personal=receipt["personal_identities"], spatial=receipt["spatial_identities"])
    reason = _support_reason(support)
    facts = {key: _digest(value) for key, value in interpreted.items() if key not in ("inputs", "interpretation", "issues")}
    review_path = output / (game_id + ".review.json")
    write_json(review_path, dict(schema_version=1, implementation=producer, native_envelope=identity(envelope_path),
        game_id=game_id, support=support, observed_receipt=receipt))
    return dict(native_envelope=identity(envelope_path), review=identity(review_path), sources=sources,
                interpreted_facts=facts, useful=reason == "matched_time_and_attempt", reason=reason, support=support)


def _summary(rows):
    recovered = sum(row["disposition"] == "recovered" for row in rows)
    requested = sum(row["fresh_path"] is not None for row in rows)
    return dict(targeted_games=len(TARGETS), requested_games=requested, source_requests=6 * requested,
        recovered_games=recovered, retained_gaps=len(TARGETS) - recovered,
        recovery_status="all_targeted_supported" if recovered == len(TARGETS) else "partial" if recovered else "no_recovery",
        expansion="required" if requested == len(PROBES) and recovered else "completed" if requested == len(TARGETS) else "not_requested")


def recovery(corpus_path, captures_root, output, probe_receipt=None):
    """review exactly three probes, or their bound conditional 57-game expansion."""
    started = time.monotonic()
    spec_bytes = SPEC.read_bytes()
    spec_sha256 = hashlib.sha256(spec_bytes).hexdigest()
    corpus_path = Path(corpus_path).resolve(strict=True)
    captures_root = Path(captures_root).resolve(strict=True)
    corpus, inventory, ledger, ordered = _original(corpus_path)
    requested = TARGETS if probe_receipt is not None else PROBES
    require(captures_root.is_dir() and {path.name for path in captures_root.iterdir()} == set(requested),
            "capture root must contain exactly the three probes or all 57 conditional targets")
    require("fixtures" not in captures_root.parts, "real recovery cannot select fixture captures")
    producer_document = artifact("source_recovery_selection", "research", {}, schema_version=1)
    producer = producer_document["implementation"]
    probe = None
    if probe_receipt is not None:
        probe_receipt = Path(probe_receipt).resolve(strict=True)
        probe = validate_recovery(probe_receipt)
        require(probe["consumed"]["probe_receipt"] is None
                and probe["consumed"]["corpus"] == identity(corpus_path)
                and probe["consumed"]["spec"]["sha256"] == spec_sha256
                and probe["implementation"] == producer
                and probe["summary"]["recovered_games"] > 0,
                "expansion requires an unchanged, useful initial probe with this corpus, policy and producer")
    output = output_path(str(output), [str(corpus_path.parent), str(captures_root),
        *([str(probe_receipt.parent)] if probe_receipt else [])])
    output.mkdir()
    spec_path = output / "spec.md"
    spec_path.write_bytes(spec_bytes)
    envelopes = output / "games"
    envelopes.mkdir()
    selected = output / "selected-games"
    selected.mkdir()
    rows = []
    for game_id in ordered:
        original = Path(ledger[game_id]["capture_path"]).resolve(strict=True)
        row = dict(game_id=game_id, original_path=str(original), fresh_path=None,
            selected_path=str(original), disposition="unchanged", reason="not_targeted",
            original=None, fresh=None, comparison=None)
        if game_id in TARGETS:
            old_path = (corpus_path.parent / ledger[game_id]["output_path"]).resolve(strict=True)
            old = read_document(old_path, "reconstruction", [])
            require(any(check["name"] == "shift_collection" and check["status"] == "match"
                        and check["observed"] == check["expected"] == 0 for check in old["interpreted"]["checks"]),
                    f"{game_id}: targeted original does not bind a successful empty shift collection")
            old_dir = envelopes / "original"
            old_dir.mkdir(exist_ok=True)
            row["original"] = _review(original, inventory[game_id], old, old_path, old_dir, producer)
            row.update(disposition="retained_gap", reason="not_requested")
            if game_id in requested:
                fresh = (captures_root / game_id).resolve(strict=True)
                require(fresh.is_dir() and fresh != original and "fixtures" not in fresh.parts,
                        f"{game_id}: fresh complete bundle must be distinct from original and fixtures")
                interpreted = interpret_game(fresh)
                envelope = dict(schema_version=4, implementation=producer,
                    interpreted=interpreted, reconstruction=reconstruct_game(interpreted))
                fresh_path = envelopes / (game_id + ".json")
                write_json(fresh_path, envelope)
                row["fresh_path"] = str(fresh)
                row["fresh"] = _review(fresh, inventory[game_id], envelope, fresh_path, envelopes, producer)
                row["reason"] = row["fresh"]["reason"]
                if row["fresh"]["useful"]:
                    row.update(selected_path=str(fresh), disposition="recovered")
                old_sources = {item["source"]: item for item in row["original"]["sources"]}
                row["comparison"] = dict(sources=[dict(source=item["source"],
                    receipt_changed=item["receipt"]["sha256"] != old_sources[item["source"]]["receipt"]["sha256"],
                    body_changed=(item["body"] or {}).get("sha256") != (old_sources[item["source"]]["body"] or {}).get("sha256"))
                    for item in row["fresh"]["sources"]],
                    changed_interpreted_fields=sorted(key for key in row["fresh"]["interpreted_facts"]
                        if row["original"]["interpreted_facts"].get(key) != row["fresh"]["interpreted_facts"][key]))
                if probe is not None and game_id in PROBES:
                    prior = next(item for item in probe["games"] if item["game_id"] == game_id)
                    require(prior["fresh_path"] == row["fresh_path"] and prior["fresh"]["sources"] == row["fresh"]["sources"]
                            and prior["fresh"]["interpreted_facts"] == row["fresh"]["interpreted_facts"]
                            and prior["fresh"]["support"] == row["fresh"]["support"],
                            f"{game_id}: probe was changed or recaptured before expansion")
        (selected / game_id).symlink_to(row["selected_path"], target_is_directory=True)
        rows.append(row)
    producer_document.update(consumed=dict(corpus=identity(corpus_path), spec=identity(spec_path),
        probe_receipt=identity(probe_receipt) if probe_receipt else None),
        policy_id=POLICY_ID, inventory_sha256=_digest([inventory[gid] for gid in ordered]),
        selected_games=str(selected), capture_root=str(captures_root), games=rows,
        summary=_summary(rows), resources=resources(started))
    receipt_path = output / "recovery.json"
    write_json(receipt_path, producer_document)
    validate_recovery(receipt_path)
    return producer_document


def validate_recovery(path, *, corpus_path=None, audit_sources=True):
    """audit the explicit receipt/tree; never discover alternate runtime inputs."""
    path = Path(path).resolve(strict=True)
    document = read_json(path)
    require(type(document) is dict and document.get("schema_version") == 1
            and document.get("kind") == "source_recovery_selection" and document.get("purpose") == "research"
            and document.get("policy_id") == POLICY_ID, "expected schema-1 source recovery selection")
    clean_implementation(document["implementation"])
    consumed = document["consumed"]
    require(set(consumed) == {"corpus", "spec", "probe_receipt"}, "recovery input references differ")
    bound_corpus = linked_path(consumed["corpus"])
    require(linked_path(consumed["spec"]) == path.parent / "spec.md",
            "recovery spec must bind its stable local snapshot")
    if corpus_path is not None:
        require(bound_corpus == Path(corpus_path).resolve(strict=True), "recovery original corpus differs")
    _, inventory, ledger, ordered = _original(bound_corpus)
    require(document["inventory_sha256"] == _digest([inventory[gid] for gid in ordered]), "recovery inventory digest differs")
    rows = document["games"]
    require(type(rows) is list and [row["game_id"] for row in rows] == ordered,
            "recovery must contain exactly all 1,312 ordered inventory games")
    tree = Path(document["selected_games"])
    require(tree == path.parent / "selected-games" and tree.is_dir()
            and {item.name for item in tree.iterdir()} == set(ordered), "recovery selection tree differs")
    requested = TARGETS if consumed["probe_receipt"] is not None else PROBES
    present = {item.name for item in Path(document["capture_root"]).iterdir()}
    require(present == set(requested) or consumed["probe_receipt"] is None and present == set(TARGETS),
            "recovery capture budget differs")
    for row in rows:
        game_id = row["game_id"]
        require(row["original_path"] == str(Path(ledger[game_id]["capture_path"]).resolve(strict=True)), "recovery original path differs")
        targeted = game_id in TARGETS
        fresh = game_id in requested
        require((row["original"] is not None) == targeted and (row["fresh"] is not None) == fresh
                and (row["fresh_path"] is not None) == fresh and (row["comparison"] is not None) == fresh,
                f"{game_id}: recovery target/request review differs")
        useful = fresh and row["fresh"]["useful"]
        expected = "recovered" if useful else "retained_gap" if targeted else "unchanged"
        reason = row["fresh"]["reason"] if fresh else "not_requested" if targeted else "not_targeted"
        require(row["disposition"] == expected and row["reason"] == reason
                and row["selected_path"] == (row["fresh_path"] if useful else row["original_path"]),
                f"{game_id}: unexplained recovery selection")
        link = tree / game_id
        require(link.is_symlink() and link.readlink() == Path(row["selected_path"])
                and link.resolve(strict=True).is_dir(), f"{link}: selection symlink target differs")
        for name, directory in (("original", row["original_path"]), ("fresh", row["fresh_path"])):
            review = row[name]
            if review is None:
                continue
            native_path = linked_path(review["native_envelope"])
            reviewed = read_json(linked_path(review["review"]))
            require(reviewed["schema_version"] == 1 and reviewed["implementation"] == document["implementation"]
                    and reviewed["game_id"] == game_id and reviewed["native_envelope"] == review["native_envelope"]
                    and reviewed["support"] == review["support"], "recovery native review binding differs")
            support = review["support"]
            expected_reason = _support_reason(support)
            actual_useful = expected_reason == "matched_time_and_attempt"
            require(review["useful"] == actual_useful and review["reason"] == expected_reason,
                    "recovery reason/predicate differs from matched support")
            if audit_sources:
                native = read_json(native_path)
                require(review["sources"] == _source_receipts(Path(directory), game_id, native["interpreted"]), "recovery source receipts changed")
                facts = {key: _digest(value) for key, value in native["interpreted"].items() if key not in ("inputs", "interpretation", "issues")}
                require(review["interpreted_facts"] == facts, "recovery interpreted facts differ")
        if fresh:
            require(row["fresh_path"] == str((Path(document["capture_root"]) / game_id).resolve(strict=True)), "recovery fresh path differs")
    require(document["summary"] == _summary(rows), "recovery summary differs from selections")
    if consumed["probe_receipt"] is not None:
        probe = validate_recovery(linked_path(consumed["probe_receipt"]), audit_sources=audit_sources)
        require(probe["consumed"]["probe_receipt"] is None and probe["summary"]["recovered_games"] > 0
                and probe["consumed"]["corpus"] == consumed["corpus"]
                and probe["consumed"]["spec"]["sha256"] == consumed["spec"]["sha256"]
                and probe["implementation"] == document["implementation"], "invalid conditional probe binding")
        for game_id in PROBES:
            before = next(row for row in probe["games"] if row["game_id"] == game_id)
            after = next(row for row in rows if row["game_id"] == game_id)
            require(before["fresh_path"] == after["fresh_path"]
                    and all(before["fresh"][key] == after["fresh"][key] for key in ("sources", "interpreted_facts", "support", "useful", "reason")),
                    "conditional expansion changed probe evidence")
    return document


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    if arguments and arguments[0] == "assess":
        from source_exposure_assess import main as assess_main
        return assess_main(arguments[1:])
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("recovery", allow_abbrev=False)
    for name in ("corpus", "captures", "out"):
        command.add_argument("--" + name, required=True)
    command.add_argument("--probe-receipt")
    args = parser.parse_args(arguments)
    try:
        result = recovery(args.corpus, args.captures, args.out, args.probe_receipt)
        print(json.dumps(result["summary"]))
    except (InputContractError, OSError) as error:
        print(f"source recovery failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
