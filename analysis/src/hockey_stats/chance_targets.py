"""literal recorded binary targets and their separate prediction domains."""

from .captures import InputContractError

QUANTITIES = (
    "unblocked_conversion", "all_attempt_recorded_context",
    "unblocked_on_net", "on_net_conversion",
)
DECOMPOSITION_QUANTITIES = ("unblocked_on_net", "on_net_conversion")


def component_kind(quantity):
    if quantity == "all_attempt_recorded_context":
        return "all_attempt"
    if quantity in ("unblocked_conversion", "unblocked_on_net", "on_net_conversion"):
        return "r"
    raise InputContractError(f"unsupported component quantity: {quantity}")


def recorded_on_net(row):
    """source classification; blocked contact says nothing about net-hitting."""
    kind = row["source_event"]["type_key"]
    if row["status"] == "eligible":
        if kind not in ("blocked-shot", "missed-shot", "shot-on-goal", "goal"):
            raise InputContractError(
                f"{row['game_id']}:{row['source_index']}: unsupported eligible source class {kind!r}"
            )
        if (
            type(row["blocked"]) is not bool or row["blocked"] != (kind == "blocked-shot")
            or type(row["goal"]) is not bool or row["goal"] != (kind == "goal")
        ):
            raise InputContractError(
                f"{row['game_id']}:{row['source_index']}: "
                f"eligible source class {kind!r} disagrees with recorded blocked/goal labels"
            )
    if kind in ("shot-on-goal", "goal"):
        return True
    if kind == "missed-shot":
        return False
    return None


def component_target(row, quantity):
    """return a literal observed target, or null outside its training domain."""
    component_kind(quantity)
    if row["status"] != "eligible":
        return None
    on_net = recorded_on_net(row)
    if quantity == "all_attempt_recorded_context":
        return row["goal"]
    if quantity == "on_net_conversion":
        return row["goal"] if on_net is True else None
    if on_net is None:
        return None
    return on_net if quantity == "unblocked_on_net" else row["goal"]


def component_prediction_applicable(row, quantity):
    """both decomposition stages predict every eligible unblocked attempt."""
    component_kind(quantity)
    if row["status"] != "eligible":
        return False
    on_net = recorded_on_net(row)
    return quantity == "all_attempt_recorded_context" or on_net is not None
