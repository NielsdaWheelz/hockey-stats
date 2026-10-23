"""strict game and reference receipts; source bytes remain uninterpreted."""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re


SOURCES = ("play-by-play", "boxscore", "shifts", "game-summary", "play-report", "landing")
REFERENCE_SOURCES = ("season-summary", "season-games", "skater-bios", "goalie-bios")


class InputContractError(Exception):
    """capture files contradict their receipt contract and need repair."""


@dataclass(frozen=True)
class Capture:
    source: str
    capture_path: Path
    requested_game_id: str | None
    requested_at: str | None
    http_status: int | None
    body_sha256: str | None
    body: bytes | None
    reason: str | None


@dataclass(frozen=True)
class ReferenceCapture:
    source: str
    capture_path: Path
    requested_season: str | None
    requested_at: str | None
    http_status: int | None
    body_sha256: str | None
    body: bytes | None
    reason: str | None


@dataclass(frozen=True)
class SkatingCapture:
    source: str
    capture_path: Path
    requested_identity: dict | None
    requested_at: str | None
    http_status: int | None
    body_sha256: str | None
    body: bytes | None
    reason: str | None


def skating_url(kind: str, season: str | None = None, player_id: str | None = None) -> str:
    """the three fixed supplemental skating locators."""
    if kind == "detail":
        return f"https://api-web.nhle.com/v1/edge/skater-skating-speed-detail/{player_id}/{season}/2"
    if kind == "listing":
        return f"https://www.nhl.com/nhl-edge/skaters/{season}/2/skating-speed/all"
    if kind == "glossary":
        return "https://www.nhl.com/nhl-edge/glossary"
    raise ValueError(f"unknown skating source {kind!r}")


def strict_json(data: bytes) -> object:
    """reject ambiguous objects and all non-finite json numbers."""
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate object key {key!r}")
            result[key] = value
        return result

    def number(text: str) -> float:
        value = float(text)
        if not math.isfinite(value):
            raise ValueError(f"non-finite number {text}")
        return value

    def constant(text: str) -> object:
        raise ValueError(f"non-finite number {text}")

    return json.loads(data, object_pairs_hook=pairs, parse_float=number,
                      parse_constant=constant)


def read_capture(directory: Path, source: str) -> Capture:
    """read one fixed game source under the unchanged game receipt contract."""
    if source not in SOURCES:
        raise ValueError(f"unknown capture source {source!r}")
    return _read_capture(directory, source, reference=False)


def read_reference_capture(directory: Path, source: str) -> ReferenceCapture:
    """read one fixed season source with shared byte integrity checks."""
    if source not in REFERENCE_SOURCES:
        raise ValueError(f"unknown reference source {source!r}")
    return _read_capture(directory, source, reference=True)


def read_supplemental_capture(directory: Path, source: str = "right-rail") -> Capture:
    """read a selected supplemental game source; its receipt must exist."""
    if source != "right-rail":
        raise ValueError(f"unknown supplemental source {source!r}")
    return _read_capture(directory, source, reference=False, required=True)


def read_skating_capture(directory: Path, kind: str) -> SkatingCapture:
    """read one required skating receipt through the common byte validator."""
    if kind not in ("detail", "listing", "glossary"):
        raise ValueError(f"unknown skating source {kind!r}")
    return _read_capture(directory, "edge-skating-" + kind, reference=False,
                         required=True, skating=True)


def _read_capture(directory: Path, source: str, *, reference: bool,
                  required: bool = False, skating: bool = False) -> Capture | ReferenceCapture | SkatingCapture:
    """read one fixed source, checking metadata and promised body integrity.

    unavailable sources retain known metadata; malformed records raise
    InputContractError, while filesystem failures propagate as OSError.
    """
    receipt = SkatingCapture if skating else ReferenceCapture if reference else Capture
    path = (directory / source / "capture.json").resolve()
    try:
        metadata_bytes = path.read_bytes()
    except FileNotFoundError as error:
        if required:
            raise InputContractError(
                f"{path}: selected capture.json is absent; restore the receipt or select a new capture directory"
            ) from error
        return receipt(source, path, None, None, None, None, None,
                       f"{path}: capture.json absent; source unavailable")

    def require(condition: bool, problem: str) -> None:
        if not condition:
            raise InputContractError(
                f"{path}: {problem}; repair this capture or select a new capture directory"
            )

    try:
        metadata = strict_json(metadata_bytes)
    except (ValueError, UnicodeDecodeError) as error:
        raise InputContractError(
            f"{path}: invalid metadata json ({error}); repair this capture or select a new capture directory"
        ) from error
    require(isinstance(metadata, dict), "metadata must be an object")
    require(type(metadata.get("schemaVersion")) is int and metadata["schemaVersion"] == 1,
            "unsupported metadata schemaVersion; expected integer 1")
    require(metadata.get("source") == source, "source identity does not match its directory")
    if skating:
        kind = source.removeprefix("edge-skating-")
        identity_keys = {"source"}
        if kind != "glossary":
            identity_keys |= {"seasonId", "gameTypeId"}
            season = metadata.get("seasonId")
            require(season in ("20232024", "20242025", "20252026"), "unsupported skating seasonId")
            require(type(metadata.get("gameTypeId")) is int and metadata["gameTypeId"] == 2,
                    "skating gameTypeId must be integer 2")
        else:
            season = None
        player = metadata.get("playerId")
        if kind == "detail":
            identity_keys.add("playerId")
            require(isinstance(player, str) and re.fullmatch(r"[0-9]+", player) is not None
                    and int(player) > 0, "skating playerId must be a positive digit string")
        require(set(metadata) == identity_keys | {"schemaVersion", "request", "responseHeaders",
                "httpStatus", "state", "body", "failure"}, "unexpected skating receipt keys")
        identity = {key: metadata[key] for key in identity_keys}
        urls = {source: skating_url(kind, season, player)}
    elif reference:
        identity = metadata.get("seasonId")
        require(isinstance(identity, str) and re.fullmatch(r"[0-9]{8}", identity) is not None,
                "seasonId must be an eight-digit string")
        require(int(identity[4:]) == int(identity[:4]) + 1,
                "seasonId must describe consecutive years")
        require("gameId" not in metadata, "reference metadata must not contain gameId")
        urls = {
            "season-summary": f"https://api.nhle.com/stats/rest/en/season?cayenneExp=id%3D{identity}&limit=-1",
            "season-games": f"https://api.nhle.com/stats/rest/en/game?cayenneExp=season%3D{identity}%20and%20gameType%3D2&limit=-1",
            "skater-bios": f"https://api.nhle.com/stats/rest/en/skater/bios?isAggregate=false&isGame=false&cayenneExp=seasonId%3D{identity}%20and%20gameTypeId%3D2&limit=-1",
            "goalie-bios": f"https://api.nhle.com/stats/rest/en/goalie/bios?isAggregate=false&isGame=false&cayenneExp=seasonId%3D{identity}%20and%20gameTypeId%3D2&limit=-1",
        }
    else:
        identity = metadata.get("gameId")
        require(isinstance(identity, str) and re.fullmatch(r"[0-9]{10}", identity) is not None,
                "gameId must be a ten-digit string")
        season = identity[:4] + str(int(identity[:4]) + 1)
        urls = {
            "play-by-play": f"https://api-web.nhle.com/v1/gamecenter/{identity}/play-by-play",
            "landing": f"https://api-web.nhle.com/v1/gamecenter/{identity}/landing",
            "right-rail": f"https://api-web.nhle.com/v1/gamecenter/{identity}/right-rail",
            "boxscore": f"https://api-web.nhle.com/v1/gamecenter/{identity}/boxscore",
            "shifts": f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId%3D{identity}&limit=-1",
            "game-summary": f"https://www.nhl.com/scores/htmlreports/{season}/GS{identity[-6:]}.HTM",
            "play-report": f"https://www.nhl.com/scores/htmlreports/{season}/PL{identity[-6:]}.HTM",
        }
    request = metadata.get("request")
    require(isinstance(request, dict), "request must be an object")
    if skating:
        require(set(request) == {"method", "url", "requestedAt"}, "unexpected skating request keys")
    require(request.get("method") == "GET" and request.get("url") == urls[source],
            "request method/url does not identify the requested source and identity")
    requested_at = request.get("requestedAt")
    require(isinstance(requested_at, str) and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z", requested_at
    ) is not None, "request.requestedAt must be a utc iso timestamp")
    try:
        datetime.fromisoformat(requested_at)
    except ValueError:
        require(False, "request.requestedAt is not a calendar timestamp")
    headers = metadata.get("responseHeaders")
    require(isinstance(headers, dict) and all(
        key in {"content-type", "content-encoding", "content-length", "date", "etag", "last-modified", "location"}
        and isinstance(value, str) for key, value in headers.items()
    ), "responseHeaders must contain selected lowercase headers with string values")
    status = metadata.get("httpStatus")
    require("httpStatus" in metadata and (status is None or type(status) is int and 100 <= status <= 599),
            "httpStatus must be a received integer status from 100 through 599 or null")
    state = metadata.get("state")
    require(state in ("captured", "failed"), "state must be captured or failed")
    if state == "failed":
        require("body" in metadata and metadata["body"] is None,
                "failed capture must have body null")
        failure = metadata.get("failure")
        require(isinstance(failure, dict) and failure.get("kind") in ("transport", "body-read", "timeout")
                and isinstance(failure.get("message"), str), "failed capture must name its failure kind/message")
        if skating:
            require(set(failure) == {"kind", "message"}, "unexpected skating failure keys")
        return receipt(source, path, identity, requested_at, status, None, None,
                       f"{path}: request failed ({failure['kind']}: {failure['message']}); source unavailable")

    require(status is not None, "captured body requires an httpStatus")
    require("failure" in metadata and metadata["failure"] is None,
            "captured body must have failure null")
    body = metadata.get("body")
    require(isinstance(body, dict), "captured body must have a body record")
    if skating:
        require(set(body) == {"path", "representation", "bytes", "sha256"}, "unexpected skating body keys")
    require(body.get("path") == "body.bin" and body.get("representation") == "http-client-body",
            "body must identify body.bin in http-client-body representation")
    length = body.get("bytes")
    digest = body.get("sha256")
    require(type(length) is int and length >= 0, "body.bytes must be a nonnegative integer")
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
            "body.sha256 must be a lowercase sha-256 digest")
    body_path = directory / source / "body.bin"
    try:
        body_bytes = body_path.read_bytes()
    except FileNotFoundError as error:
        raise InputContractError(
            f"{body_path}: captured record promises a missing body; restore its matching body or select a new capture directory"
        ) from error
    require(len(body_bytes) == length, "body.bin length does not match body.bytes")
    require(hashlib.sha256(body_bytes).hexdigest() == digest,
            "body.bin digest does not match body.sha256")
    if not 200 <= status <= 299:
        return receipt(source, path, identity, requested_at, status, digest, None,
                       f"{path}: http {status} response; source unavailable")
    return receipt(source, path, identity, requested_at, status, digest, body_bytes, None)
