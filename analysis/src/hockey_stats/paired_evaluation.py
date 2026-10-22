"""paired additive ratios with shared game and calendar resampling units."""

from datetime import date

import numpy as np

from .artifacts import require


def calendar_blocks(dates, days):
    """retain empty blocks between the earliest and latest selected dates."""
    require(bool(dates) and type(days) is int and days > 0, "invalid calendar resampling units")
    parsed = [date.fromisoformat(value) for value in dates]
    first = min(parsed)
    return np.array([(value - first).days // days for value in parsed], dtype=np.int64)


def paired_samples(dates, seed):
    """one shared draw matrix per scheme, including zero-contribution units."""
    dates = list(dates.values()) if isinstance(dates, dict) else list(dates)
    require(bool(dates), "paired resampling requires selected games")
    units = dict(games=None, calendar_7_day=calendar_blocks(dates, 7),
                 calendar_14_day=calendar_blocks(dates, 14))
    result = {}
    for name, blocks in units.items():
        count = len(dates) if blocks is None else int(max(blocks)) + 1
        result[name] = dict(blocks=blocks, samples=np.random.Generator(np.random.PCG64(seed)).integers(
            0, count, size=(2000, count)))
    return result


def ratio_bootstrap(numerators, denominators, seed, *, blocks=None, samples=None):
    """pool float denominators; an undefined draw makes its interval unavailable."""
    numerators, denominators = (np.asarray(value, dtype=np.float64)
                                for value in (numerators, denominators))
    require(numerators.shape == denominators.shape and numerators.ndim == 1
            and len(numerators) > 0 and np.isfinite(numerators).all()
            and np.isfinite(denominators).all() and np.all(denominators >= 0),
            "invalid resampling sums")
    contributing_games = int(np.count_nonzero(denominators))
    total = float(denominators.sum())
    estimate = float(numerators.sum() / total) if total else None
    if blocks is not None:
        blocks = np.asarray(blocks)
        require(blocks.shape == denominators.shape and np.issubdtype(blocks.dtype, np.integer)
                and np.all(blocks >= 0), "invalid calendar block assignments")
        n = int(max(blocks)) + 1
        numerators = np.bincount(blocks, weights=numerators, minlength=n)
        denominators = np.bincount(blocks, weights=denominators, minlength=n)
    else:
        n = len(numerators)
    if samples is None:
        samples = np.random.Generator(np.random.PCG64(seed)).integers(0, n, size=(2000, n))
    require(samples.shape == (2000, n) and np.issubdtype(samples.dtype, np.integer)
            and np.all(samples >= 0) and np.all(samples < n), "resampling dimensions disagree")
    sampled_denominators = denominators[samples].sum(axis=1)
    undefined = int(np.count_nonzero(sampled_denominators == 0))
    sampled = np.divide(numerators[samples].sum(axis=1), sampled_denominators,
                        out=np.full(2000, np.nan), where=sampled_denominators != 0)
    require((estimate is None or np.isfinite(estimate))
            and np.isfinite(sampled).sum() + undefined == 2000, "nonfinite bootstrap estimate")
    result = dict(estimate=estimate, denominator=total, contributing_games=contributing_games,
        interval=None if undefined else np.percentile(sampled, [2.5, 97.5], method="linear").tolist(),
        undefined_draws=undefined,
        missing_reason="zero denominator in at least one resampled draw" if undefined else None,
        draws=sampled)
    if blocks is not None:
        result.update(contributing_blocks=int(np.count_nonzero(denominators)), selected_blocks=n)
    return result


def paired_ratio_intervals(numerators, denominators, dates, seed, *, samples=None):
    """resample columns on the same draws; dates and rows have one fixed order."""
    numerators, denominators = (np.asarray(value, dtype=np.float64)
                                for value in (numerators, denominators))
    require(numerators.ndim in (1, 2) and len(numerators) == len(dates)
            and (denominators.shape == numerators.shape or denominators.shape == (len(dates),)),
            "paired additive sums differ from the selected game ledger")
    if samples is None:
        samples = paired_samples(dates, seed)
    require(set(samples) == {"games", "calendar_7_day", "calendar_14_day"},
            "paired resampling methods differ")
    if numerators.ndim == 1:
        return {name: ratio_bootstrap(numerators, denominators, seed, **unit)
                for name, unit in samples.items()}
    require(numerators.shape[1] > 0, "paired additive contrast inventory is empty")
    if denominators.ndim == 1:
        denominators = np.broadcast_to(denominators[:, None], numerators.shape)
    result = {}
    for name, unit in samples.items():
        columns = [ratio_bootstrap(numerators[:, i], denominators[:, i], seed, **unit)
                   for i in range(numerators.shape[1])]
        result[name] = {field: np.asarray([column[field] for column in columns])
                       for field in ("denominator", "contributing_games", "undefined_draws")}
        result[name].update(
            estimate=np.asarray([np.nan if column["estimate"] is None else column["estimate"]
                                 for column in columns]),
            interval=np.asarray([[np.nan, np.nan] if column["interval"] is None else column["interval"]
                                 for column in columns]),
            missing_reason=[column["missing_reason"] for column in columns],
            draws=np.column_stack([column["draws"] for column in columns]))
        if unit["blocks"] is not None:
            result[name].update(contributing_blocks=np.asarray([column["contributing_blocks"]
                                                               for column in columns]),
                                selected_blocks=columns[0]["selected_blocks"])
    return result
