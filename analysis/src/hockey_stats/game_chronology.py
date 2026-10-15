"""corroborated all-or-unavailable score chronology for native games."""

def period_length(event):
    if event["timed_period"] is True:
        if event["period_number"] in (1, 2, 3) and event["period_type"] == "REG":
            return 1200
        if event["period_number"] == 4 and event["period_type"] == "OT":
            return 300
    return None


def score_chronology(interpreted, events, game):
    """count all strengths before each event; never read post-event scores."""
    failures = []
    for source in ("play-by-play", "boxscore"):
        checks = [
            c
            for c in interpreted["checks"]
            if c["name"] == "timed_goals" and c.get("source") == source
        ]
        if len(checks) != 1 or checks[0]["status"] != "match":
            failures.append(
                {
                    "source": source,
                    "path": "/checks",
                    "message": "unique matching timed_goals check required",
                    "checks": checks,
                }
            )
    if interpreted["events"] is None:
        failures.append(
            {
                "source": "play-by-play",
                "path": "/events",
                "message": "event collection unavailable",
            }
        )
    orders = [event["sort_order"] for event in events.values()]
    unique_order = None not in orders and len(orders) == len(set(orders))
    order_supported = unique_order
    if not order_supported:
        failures.append(
            {
                "source": "play-by-play",
                "path": "/events",
                "message": "unique sort_order required for every source event",
            }
        )
    previous = None
    previous_period = 0
    shootout_started = False
    ordered = sorted(
        events.values(),
        key=lambda e: e["sort_order"] if e["sort_order"] is not None else -1,
    )
    teams = (game["away_team_id"], game["home_team_id"])
    for event in ordered:
        problem = None
        period = event["period_number"]
        if period is None or period < previous_period:
            problem = "event periods must be known and nondecreasing in sort_order"
            order_supported = False
        elif period is not None:
            previous_period = period
        if event["timed_period"] is True and not event["kind_valid"]:
            failures.append(
                {
                    "source": "play-by-play",
                    "path": f"/events/{event['source_index']}",
                    "message": "event kind cannot exclude an unaccounted timed goal",
                }
            )
        if event["timed_period"] is None:
            problem = "event kind or period cannot exclude an unaccounted timed goal"
        elif event["timed_period"] is True:
            period, seconds = event["period_number"], event["elapsed_seconds"]
            length = period_length(event)
            if shootout_started:
                problem = "timed play follows shootout evidence"
            elif (
                period is None
                or length is None
                or seconds is not None
                and not (0 <= seconds <= length)
            ):
                problem = "supported timed period/clock required"
            elif (
                seconds is not None
                and previous is not None
                and (period, seconds) < previous
            ):
                problem = "sort_order contradicts period/elapsed chronology"
            elif seconds is not None:
                previous = (period, seconds)
            if event["type_key"] == "goal" and seconds is None:
                failures.append(
                    {
                        "source": "play-by-play",
                        "path": f"/events/{event['source_index']}",
                        "message": "known timed goal clock required for score accounting",
                    }
                )
            if event["type_key"] == "goal" and (
                event["shooting_team_id"] not in teams
                or event["owner_team_id"] != event["shooting_team_id"]
            ):
                failures.append(
                    {
                        "source": "play-by-play",
                        "path": f"/events/{event['source_index']}",
                        "message": "timed goal ownership missing or conflicting",
                    }
                )
        else:
            shootout_started = True
            if event["period_type"] != "SO" or period != 5:
                problem = "untimed event must identify regular-season shootout period 5"
        if problem:
            order_supported = False
            failures.append(
                {
                    "source": "play-by-play",
                    "path": f"/events/{event['source_index']}",
                    "message": problem,
                }
            )
    if failures:
        return {}, failures, ordered if unique_order else None, order_supported
    score = {"away": 0, "home": 0}
    result = {}
    for event in ordered:
        result[event["source_index"]] = dict(score)
        if event["type_key"] == "goal" and event["timed_period"] is True:
            score[
                "away" if event["shooting_team_id"] == game["away_team_id"] else "home"
            ] += 1
    # corroborate the embedded observed totals, not just a stale status label.
    for check in interpreted["checks"]:
        if (
            check["name"] == "timed_goals"
            and check.get("source") in ("play-by-play", "boxscore")
            and check.get("observed") != score
        ):
            failures.append(
                {
                    "source": check["source"],
                    "path": "/checks",
                    "message": "counted timed goals disagree with embedded observed accounting",
                    "check": check,
                }
            )
    return (
        ({}, failures, ordered, order_supported)
        if failures
        else (result, [], ordered, order_supported)
    )


