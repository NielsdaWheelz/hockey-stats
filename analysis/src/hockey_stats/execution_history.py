"""coarsened execution history from supported records strictly before the clock."""

from .feature_data import ACTION_KINDS, RESETS, preclock_strength_transition


def _value(record, field):
    if not isinstance(record, dict) or field in record.get("problems", {}):
        return None
    return record.get("values", {}).get(field)


def _clock(source):
    period, elapsed = source.get("period_number"), source.get("elapsed_seconds")
    if source.get("timed_period") is not True or period not in (1, 2, 3, 4) or elapsed is None:
        return None
    return period, elapsed


def _relation(source, cutoff):
    if source.get("period_number") in (1, 2, 3, 4) and source["period_number"] != cutoff[0]:
        return "outside"
    clock = _clock(source)
    return "unknown" if clock is None else "outside" if clock >= cutoff else "earlier"


def preclock_history(game):
    """select a prior-clock phase proxy; never recover physical release order.

    known absent phases have an empty participant set. unsupported/censored
    phases remain unknown. a supported earlier reset or faceoff restores the
    corresponding recorded phase boundary; same-clock rows do nothing.
    """
    events = game.get("events") or []
    rows = sorted((row for row in events if type(_value(row["chronology"], "order_index")) is int),
                  key=lambda row: _value(row["chronology"], "order_index"))
    unordered = [row for row in events if type(_value(row["chronology"], "order_index")) is not int]
    by_index = {row["source"]["source_index"]: row for row in events}
    anchors = {row["start_source_index"] for row in game.get("episodes") or [] if row["start_kind"] == "faceoff"}
    result = {}
    for attempt in game.get("attempts") or []:
        index = attempt["source_index"]
        focal = by_index[index]
        cutoff = _clock(focal["source"])
        order = _value(focal["chronology"], "order_index")
        prefix, phase = [], []
        phase_status, reason = "unavailable", "prior_clock_phase_left_censored"
        ordered = type(order) is int and cutoff is not None
        if ordered and any(_relation(row["source"], cutoff) != "outside" for row in unordered):
            ordered = False
        uncertain, preceding = not ordered, None
        if type(order) is not int or cutoff is not None and not ordered:
            reason = "verified_source_order_unavailable"
        elif cutoff is None:
            reason = "focal_clock_unavailable"
        if not uncertain:
            for row in rows:
                if _value(row["chronology"], "order_index") >= order:
                    break
                source = row["source"]
                relation = _relation(source, cutoff)
                # exclude every known same-clock row before examining its kind,
                # validity, roles, membership, reset or prepared episode state.
                if relation == "outside":
                    continue
                if relation == "unknown":
                    uncertain, phase_status, reason = True, "unavailable", "earlier_record_clock_unavailable"
                    phase = []
                    prefix.append(source)
                    continue
                prefix.append(source)
                preceding = row
                if not source["kind_valid"]:
                    uncertain, phase_status, reason = True, "unavailable", "earlier_record_kind_unavailable"
                    phase = []
                elif source["type_key"] in RESETS:
                    uncertain, phase_status, reason = False, "absent", "known_no_prior_clock_phase"
                    phase = []
                elif source["source_index"] in anchors:
                    uncertain, phase_status, reason = False, "live", "supported_prior_clock_faceoff"
                    phase = [row]
                elif source["type_key"] in ACTION_KINDS:
                    if phase_status == "absent":
                        phase_status, reason = "live", "supported_prior_clock_action_after_reset"
                    if phase_status == "live":
                        phase.append(row)
                elif phase_status == "live":
                    phase.append(row)
        transition = preclock_strength_transition(
            prefix, game["game"].get("native_intervals"),
            focal["source"], game["game"]["identity"], not uncertain,
        )
        result[index] = dict(preceding=preceding, recent_available=not uncertain,
                             phase_status=phase_status, phase_reason=reason,
                             phase_events=tuple(phase), transition=transition,
                             cutoff={"period": None if cutoff is None else cutoff[0],
                                     "elapsed_seconds": None if cutoff is None else cutoff[1],
                                     "source_order": order},
                             source_indices=[source["source_index"] for source in prefix])
    return result


def recent_context(history, attempt, game):
    """encode the last allowed record in the focal attacking frame."""
    result = dict(status="unavailable", kind=None, time_gap_seconds=None,
                  owner_team_relation=None, current_attack_x=None,
                  current_attack_y=None, same_shooter=None)
    if not history["recent_available"]:
        return result
    row = history["preceding"]
    if row is None:
        return dict(result, status="none")
    source = row["source"]
    elapsed = history["cutoff"]["elapsed_seconds"]
    gap = elapsed - source["elapsed_seconds"]
    if source["type_key"] in RESETS or gap > 5:
        return dict(result, status="none")
    identity = game["game"]["identity"]
    state = attempt["feature_facts"]["state"]
    team = _value(state, "shooting_team_id")
    owner = source["owner_team_id"]
    geometry = row["geometry"]
    x, y = _value(geometry, "x_ft"), _value(geometry, "y_ft")
    if (source["type_key"] not in ACTION_KINDS or owner not in (identity["home_team_id"], identity["away_team_id"])
            or team not in (identity["home_team_id"], identity["away_team_id"])
            or _value(geometry, "frame") != "home_attack" or x is None or y is None):
        return result
    same_shooter = None
    if source["type_key"] in ACTION_KINDS[4:]:
        prior = next((row for row in game["attempts"] if row["source_index"] == source["source_index"]), None)
        shooter = _value(prior["details"], "physical_shooter_id") if prior is not None else None
        person = (game.get("people") or {}).get(str(shooter), {}).get("people", {})
        if (shooter is None or _value(person, "team_id") != source["shooting_team_id"]
                or owner != source["shooting_team_id"]):
            return result
        same_shooter = shooter == _value(attempt["details"], "physical_shooter_id")
    sign = 1 if team == identity["home_team_id"] else -1
    return dict(status="recent", kind=source["type_key"], time_gap_seconds=gap,
                owner_team_relation="same" if owner == team else "opponent",
                current_attack_x=sign*x, current_attack_y=sign*y, same_shooter=same_shooter)
