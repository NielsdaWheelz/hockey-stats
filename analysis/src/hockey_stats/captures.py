"""the pr1 capture contract; source bytes remain uninterpreted."""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re


SOURCES = ("play-by-play", "boxscore", "shifts", "game-summary")


class InputContractError(Exception):
    """capture files contradict the pr1 contract and need repair."""


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
    """read one fixed source, checking metadata and promised body integrity.

    unavailable sources retain known metadata; malformed records raise
    InputContractError, while filesystem failures propagate as OSError.
    """
    if source not in SOURCES:
        raise ValueError(f"unknown capture source {source!r}")
    path = (directory / source / "capture.json").resolve()
    try:
        metadata_bytes = path.read_bytes()
    except FileNotFoundError:
        return Capture(source, path, None, None, None, None, None,
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
    game_id = metadata.get("gameId")
    require(isinstance(game_id, str) and re.fullmatch(r"[0-9]{10}", game_id) is not None,
            "gameId must be a ten-digit string")
    require(metadata.get("source") == source, "source identity does not match its directory")
    season = game_id[:4] + str(int(game_id[:4]) + 1)
    urls = {
        "play-by-play": f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play",
        "boxscore": f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore",
        "shifts": f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId%3D{game_id}&limit=-1",
        "game-summary": f"https://www.nhl.com/scores/htmlreports/{season}/GS{game_id[-6:]}.HTM",
    }
    request = metadata.get("request")
    require(isinstance(request, dict), "request must be an object")
    require(request.get("method") == "GET" and request.get("url") == urls[source],
            "request method/url does not identify the requested source and game")
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
    require("httpStatus" in metadata and (status is None or type(status) is int),
            "httpStatus must be a received integer status or null")
    state = metadata.get("state")
    require(state in ("captured", "failed"), "state must be captured or failed")
    if state == "failed":
        require("body" in metadata and metadata["body"] is None,
                "failed capture must have body null")
        failure = metadata.get("failure")
        require(isinstance(failure, dict) and failure.get("kind") in ("transport", "body-read", "timeout")
                and isinstance(failure.get("message"), str), "failed capture must name its failure kind/message")
        return Capture(source, path, game_id, requested_at, status, None, None,
                       f"{path}: request failed ({failure['kind']}: {failure['message']}); source unavailable")

    require(status is not None, "captured body requires an httpStatus")
    require("failure" in metadata and metadata["failure"] is None,
            "captured body must have failure null")
    body = metadata.get("body")
    require(isinstance(body, dict), "captured body must have a body record")
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
        return Capture(source, path, game_id, requested_at, status, digest, None,
                       f"{path}: http {status} response; source unavailable")
    return Capture(source, path, game_id, requested_at, status, digest, body_bytes, None)
