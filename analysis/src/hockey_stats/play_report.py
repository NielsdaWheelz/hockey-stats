"""extract the current official play report's structure without hockey inference."""

from typing import TypedDict

from bs4 import BeautifulSoup, Tag


class ExtractionIssue(TypedDict):
    code: str
    path: str
    message: str


class ExtractedMember(TypedDict):
    sweater_number: str | None
    reported_position: str | None


class ExtractedRow(TypedDict):
    source_index: int
    row_id: str
    event_number: str | None
    period_number: str | None
    reported_strength: str | None
    time_in_period: str | None
    time_remaining: str | None
    event_code: str | None
    description: str | None
    away_members: list[ExtractedMember] | None
    home_members: list[ExtractedMember] | None


class ExtractedReport(TypedDict):
    game_info: list[list[str]]
    team_headers: list[list[str]]
    rows: list[ExtractedRow]
    issues: list[ExtractionIssue]


def _text(tag: Tag) -> str | None:
    text = " ".join(tag.stripped_strings)
    return text or None


def _members(cell: Tag, path: str, issues: list[ExtractionIssue]) -> list[ExtractedMember] | None:
    if _text(cell) is None:
        return None
    tables = cell.find_all("table", recursive=False)
    if len(tables) != 1 or len(tables[0].find_all("tr", recursive=False)) != 1:
        issues.append({"code": "unsupported_member_list", "path": path,
                       "message": "expected one single-row player table; reported membership unavailable"})
        return None
    members: list[ExtractedMember] = []
    for slot in tables[0].find("tr", recursive=False).find_all("td", recursive=False):
        player_tables = slot.find_all("table", recursive=False)
        if not player_tables and _text(slot) is None:
            continue
        if len(player_tables) != 1:
            issues.append({"code": "malformed_member", "path": f"{path}/{len(members)}",
                           "message": "nonblank player slot does not contain one player table; unavailable slot retained as null fields"})
            members.append({"sweater_number": None, "reported_position": None})
            continue
        rows = player_tables[0].find_all("tr", recursive=False)
        values: list[str | None] = []
        for index in range(2):
            cells = rows[index].find_all("td", recursive=False) if index < len(rows) else []
            values.append(_text(cells[0]) if len(cells) == 1 else None)
        if len(rows) > 2:
            values = [None, None]
        if len(rows) != 2 or None in values:
            issues.append({"code": "malformed_member", "path": f"{path}/{len(members)}",
                           "message": "player slot must have jersey and position rows; unavailable fields retained as null"})
        members.append({"sweater_number": values[0], "reported_position": values[1]})
    if not members:
        issues.append({"code": "unsupported_member_list", "path": path,
                       "message": "nonblank on-ice cell has no player slots; reported membership unavailable"})
        return None
    return members


def extract_report(body: bytes) -> ExtractedReport:
    soup = BeautifulSoup(body, "html.parser")
    issues: list[ExtractionIssue] = []
    game_info = [[text for cell in table.find_all("td") if (text := _text(cell)) is not None]
                 for table in soup.select("table#GameInfo")]
    team_headers: list[list[str]] = []
    pages = soup.select("div.page")
    if not pages:
        issues.append({"code": "unsupported_report_structure", "path": "/pages",
                       "message": "report has no supported page containers; report identity unavailable"})
    for index, page in enumerate(pages):
        headers = []
        table = page.find("table", recursive=False)
        if table is not None:
            for row in table.find_all("tr", recursive=False):
                cells = row.find_all("td", recursive=False)
                if len(cells) == 8 and _text(cells[0]) == "#" and _text(cells[1]) == "Per":
                    headers.append([_text(cells[6]) or "", _text(cells[7]) or ""])
        if len(headers) != 1 or len(page.select("table#GameInfo")) != 1:
            issues.append({"code": "unsupported_report_structure", "path": f"/pages/{index}",
                           "message": "page requires one game identity and one eight-column on-ice header; report identity unavailable"})
        team_headers.extend(headers)
    rows: list[ExtractedRow] = []
    for index, row in enumerate(soup.select('tr[id^="PL-"]')):
        row_id = row["id"]
        assert isinstance(row_id, str)
        path = f"/rows/{index}[{row_id}]"
        record: ExtractedRow = {"source_index": index, "row_id": row_id,
            "event_number": None, "period_number": None, "reported_strength": None,
            "time_in_period": None, "time_remaining": None, "event_code": None,
            "description": None, "away_members": None, "home_members": None}
        cells = row.find_all("td", recursive=False)
        if len(cells) != 8:
            issues.append({"code": "unsupported_report_row", "path": path,
                           "message": f"expected eight direct cells, received {len(cells)}; row fields unavailable"})
        else:
            record.update(event_number=_text(cells[0]), period_number=_text(cells[1]),
                          reported_strength=_text(cells[2]), event_code=_text(cells[4]), description=_text(cells[5]))
            clocks = list(cells[3].stripped_strings)
            if len(clocks) == 2:
                record.update(time_in_period=clocks[0], time_remaining=clocks[1])
            else:
                issues.append({"code": "unsupported_report_clock", "path": path + "/clock",
                               "message": "expected elapsed then remaining clock fragments; clock fields unavailable"})
            record["away_members"] = _members(cells[6], path + "/away_members", issues)
            record["home_members"] = _members(cells[7], path + "/home_members", issues)
        rows.append(record)
    return {"game_info": game_info, "team_headers": team_headers, "rows": rows, "issues": issues}
