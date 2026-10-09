"""extract the current official play report's structure without hockey inference."""

from datetime import date
import re
from typing import Any, TypedDict

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


class ExtractedSummary(TypedDict):
    game_info: list[list[str]]
    values: dict[str, Any]
    paths: dict[str, str]
    issues: list[ExtractionIssue]


def _text(tag: Tag) -> str | None:
    text = " ".join(tag.stripped_strings)
    return text or None


def report_identity(cells: list[str], game_date: str, game_number: str) -> bool:
    """require the supplied report date, game number and final status."""
    months = {name: index for index, name in enumerate(("January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"), 1)}
    dates: list[str | None] = []
    numbers = []
    statuses = []
    for text in cells:
        match = re.fullmatch(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), ([A-Za-z]+) ([0-9]{1,2}), ([0-9]{4})", text)
        if match is not None and match[1] in months:
            try:
                dates.append(date(int(match[3]), months[match[1]], int(match[2])).isoformat())
            except ValueError:
                dates.append(None)
        if re.fullmatch(r"Game [0-9]{4}", text):
            numbers.append(text.removeprefix("Game "))
        if text in ("Final", "In Progress", "Preview"):
            statuses.append(text)
    return dates == [game_date] and numbers == [game_number] and statuses == ["Final"]


def extract_summary(body: bytes) -> ExtractedSummary:
    """extract located recording fields from the official game summary."""
    soup = BeautifulSoup(body, "html.parser")
    tables = soup.select("table#GameInfo")
    game_info = [[text for cell in table.find_all("td") if (text := _text(cell)) is not None] for table in tables]
    values: dict[str, Any] = dict.fromkeys(("reported_date", "reported_start", "reported_end", "attendance", "venue", "officials"))
    paths = {field: "/GameInfo" for field in values}
    paths["officials"] = "/OFFICIALS"
    issues: list[ExtractionIssue] = []
    if len(tables) != 1:
        issues.append({"code": "unsupported_summary_structure", "path": "/GameInfo",
                       "message": "expected one game identity table; summary recording unavailable"})
    else:
        found: dict[str, list[tuple[Any, str]]] = {field: [] for field in values if field != "officials"}
        for index, cell in enumerate(tables[0].find_all("td")):
            text = _text(cell)
            if text is None:
                continue
            text = " ".join(text.split())
            path = f"/GameInfo/td/{index}"
            if re.fullmatch(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), [A-Za-z]+ [0-9]{1,2}, [0-9]{4}", text):
                found["reported_date"].append((text, path))
            attendance = re.fullmatch(r"Attendance ([0-9]+(?:,[0-9]{3})*) at (.+)", text)
            if attendance is not None:
                found["attendance"].append((int(attendance[1].replace(",", "")), path))
                found["venue"].append((attendance[2], path))
            clocks = re.fullmatch(r"Start (.+); End (.+)", text)
            if clocks is not None:
                for field, fragment in (("reported_start", clocks[1]), ("reported_end", clocks[2])):
                    if re.fullmatch(r"(?:0?[0-9]|1[0-9]|2[0-3]):[0-5][0-9] [A-Z]+", fragment):
                        found[field].append((fragment, path))
        for field, matches in found.items():
            if len(matches) == 1:
                values[field], paths[field] = matches[0]
            else:
                issues.append({"code": "unavailable_summary_field", "path": paths[field],
                               "message": f"expected one supported {field} fragment; field unavailable"})
    sections = [cell for cell in soup.find_all("td") if _text(cell) == "OFFICIALS"]
    if len(sections) == 1:
        row = sections[0].find_parent("tr")
        following = row.find_next_sibling("tr") if row is not None else None
        cells = following.find_all("td", recursive=False) if following is not None else []
        role_tables = cells[0].find_all("table", recursive=False) if cells else []
        role_rows = []
        if len(role_tables) == 1:
            role_table = role_tables[0]
            role_rows = [row for row in role_table.find_all("tr") if row.find_parent("table") is role_table]
        headings = role_rows[0].find_all("td", recursive=False) if role_rows else []
        names = role_rows[1].find_all("td", recursive=False) if len(role_rows) >= 2 else []
        if (len(role_rows) in (2, 4) and len(headings) == len(names) == 2
                and len({_text(cell) for cell in headings}) == 2 and all(_text(cell) is not None for cell in headings)):
            officials = {_text(heading): list(cell.stripped_strings) for heading, cell in zip(headings, names, strict=True)}
            if len(role_rows) == 4:
                standby_headings = role_rows[2].find_all("td", recursive=False)
                standby_names = role_rows[3].find_all("td", recursive=False)
                if len(standby_headings) == len(standby_names) == 2:
                    for heading, cell, main_heading in zip(standby_headings, standby_names, headings, strict=True):
                        listed = list(cell.stripped_strings)
                        if listed and _text(heading) == "Standby":
                            officials["Standby " + _text(main_heading)] = listed
            values["officials"] = officials
    if values["officials"] is None:
        issues.append({"code": "unavailable_officials", "path": "/OFFICIALS",
                       "message": "expected one supported officials section with labeled role columns; officials unavailable"})
    return {"game_info": game_info, "values": values, "paths": paths, "issues": issues}


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
