"""five-foot recorded-location display cells and fixed mass-preserving pooling."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import cache
import math

import numpy as np
from scipy.integrate import quad

from .artifacts import require
from .shot_origins import in_rink

POPULATION_VERSION = "matched_unblocked_locations_v1"
DISPLAY_VERSION = "rect5_gaussian10_v1"


@cache
def cells():
    """integrate clipped rectangles, splitting at every change of boundary formula."""
    result = []
    for xi in range(40):
        x_min, x_max = -100 + 5 * xi, -95 + 5 * xi
        for yi in range(17):
            y_min, y_max = -42.5 + 5 * yi, -37.5 + 5 * yi
            points = [x_min, x_max]
            for x in (-72, 72):
                if x_min < x < x_max:
                    points.append(x)
            for y in (y_min, y_max):
                if 14.5 < abs(y) < 42.5:
                    x = 72 + math.sqrt(28**2 - (abs(y) - 14.5)**2)
                    points.extend(v for v in (-x, x) if x_min < v < x_max)
            points.sort()
            def section(x, moment):
                b = 42.5 if abs(x) <= 72 else 14.5 + math.sqrt(max(0, 28**2 - (abs(x)-72)**2))
                lo, hi = max(y_min, -b), min(y_max, b)
                if hi <= lo:
                    return 0.0
                return (hi-lo, x*(hi-lo), (hi*hi-lo*lo)/2)[moment]
            area, mx, my = (sum(quad(section, lo, hi, args=(moment,), epsabs=1e-11, epsrel=1e-13)[0]
                for lo, hi in zip(points, points[1:])) for moment in range(3))
            if area > 0:
                result.append(dict(cell_id=17*xi+yi, x_min=x_min, x_max=x_max,
                    y_min=y_min, y_max=y_max, center_x=mx/area, center_y=my/area, area_sqft=area))
    require(len(result) == 668 and abs(sum(r["area_sqft"] for r in result)
            - (17000-4*28**2+math.pi*28**2)) <= 1e-8, "invalid spatial partition")
    require(all(in_rink(r["center_x"], r["center_y"]) for r in result), "spatial centroid outside rink")
    return tuple(result)


def cell_id(x, y):
    if not all(type(v) in (int, float) and math.isfinite(v) for v in (x, y)) or not in_rink(x, y):
        raise ValueError("spatial location outside rink")
    xi = 39 if x == 100 else math.floor((x+100)/5)
    yi = 16 if y == 42.5 else math.floor((y+42.5)/5)
    identity = 17*xi+yi
    require(identity in {r["cell_id"] for r in cells()}, "spatial point has no positive-area cell")
    return identity


@cache
def pooling():
    rows = cells()
    centers = np.array([(r["center_x"], r["center_y"]) for r in rows])
    areas = np.array([r["area_sqft"] for r in rows])
    distances = np.sum((centers[:, None, :] - centers[None, :, :])**2, axis=2)
    weights = areas[:, None] * np.exp(-distances / 200)
    kernel = weights / weights.sum(axis=0)
    require(np.isfinite(kernel).all() and (kernel >= 0).all()
            and np.allclose(kernel.sum(axis=0), 1, atol=1e-14, rtol=0), "invalid spatial pooling")
    kernel.flags.writeable = False
    return kernel


@dataclass(frozen=True, slots=True)
class GameCell:
    player_id: str
    game_id: str
    cell_id: int
    for_count: int
    against_count: int


@dataclass(frozen=True, slots=True)
class SeasonCell:
    player_id: str
    cell_id: int
    for_count: int
    against_count: int
    for_raw_per60: float
    against_raw_per60: float
    for_density: float
    against_density: float
    for_difference: float
    against_difference: float


def finalize(games, player_games, seasons, physical_cells, sparse):
    """reduce recorded cells once, then pool season rates against the physical reference."""
    geometry = cells()
    ids = [r["cell_id"] for r in geometry]
    areas = np.array([r["area_sqft"] for r in geometry])
    index = {identity: i for i, identity in enumerate(ids)}
    league = Counter()
    for row in physical_cells:
        league[row["cell_id"]] += row["count"]
    seconds = sum(g.spatial_included_seconds for g in games)
    excluded = sum(g.spatial_known_excluded_seconds for g in games)
    reasons = {reason for g in games for reason in g.spatial_reason_codes} - {"no_spatial_5v5_exposure"}
    if not seconds and not reasons:
        reasons.add("no_spatial_5v5_exposure")
    status = ("partial" if reasons else "complete") if seconds else ("unavailable" if reasons - {"no_spatial_5v5_exposure"} else "complete")
    available = bool(seconds) or status == "complete"
    total = sum(league.values()) if available else None
    raw = np.array([3600*league[identity]/(2*seconds) for identity in ids]) if seconds else None
    density = 100*(pooling()@raw)/areas if seconds else None
    final_cells = tuple(r | dict(league_count=league[r["cell_id"]] if available else None,
        league_raw_per60=float(raw[i]) if seconds else None,
        league_density=float(density[i]) if seconds else None) for i, r in enumerate(geometry))
    coverage = dict(included_seconds=seconds, known_excluded_seconds=excluded,
        unblocked_attempts=total, unblocked_per60=3600*total/(2*seconds) if seconds else None,
        coverage_status=status, reason_codes=sorted(reasons), inventory_games=len(games),
        games_with_included_time=sum(g.spatial_included_seconds > 0 for g in games),
        partial_games=sum(g.spatial_coverage_status == "partial" for g in games),
        unavailable_games=sum(g.spatial_coverage_status == "unavailable" for g in games),
        reason_game_counts=[dict(code=code,games=count) for code,count in sorted(Counter(
            reason for g in games for reason in g.spatial_reason_codes).items())])
    by_player = defaultdict(lambda: np.zeros((2,len(ids)), dtype=np.int64))
    teams = {(r.player_id,r.game_id):r.team_id for r in player_games}
    player_counts = Counter()
    player_seconds = Counter()
    for row in player_games:
        player_seconds[row.game_id] += row.spatial.included_seconds
    team_for, team_against = Counter(), Counter()
    for r in sparse:
        require(r.for_count >= 0 and r.against_count >= 0 and r.for_count+r.against_count > 0, "invalid sparse spatial count")
        by_player[r.player_id][:,index[r.cell_id]] += (r.for_count,r.against_count)
        player_counts[r.player_id,r.game_id,"for"] += r.for_count
        player_counts[r.player_id,r.game_id,"against"] += r.against_count
        team = teams[r.player_id,r.game_id]
        team_for[r.game_id,team,r.cell_id] += r.for_count
        team_against[r.game_id,team,r.cell_id] += r.against_count
    physical = Counter({(r["game_id"],r["team_id"],r["cell_id"]):r["count"] for r in physical_cells})
    opponents = {(g.game_id,g.away_team_id):g.home_team_id for g in games} | {(g.game_id,g.home_team_id):g.away_team_id for g in games}
    require(all(value == 5*physical[key] for key,value in team_for.items())
            and all(value == 5*physical[gid,opponents[gid,team],cid] for (gid,team,cid),value in team_against.items())
            and sum(team_for.values()) == sum(team_against.values()) == 5*sum(league.values()), "spatial physical cell conservation failed")
    physical_totals = Counter()
    for (gid,team,identity),count in physical.items():
        physical_totals[gid,team] += count
    for game in games:
        require(player_seconds[game.game_id] == 10*game.spatial_included_seconds
                and physical_totals[game.game_id,game.away_team_id] == (game.spatial_away_unblocked or 0)
                and physical_totals[game.game_id,game.home_team_id] == (game.spatial_home_unblocked or 0), "spatial game conservation failed")
    for row in player_games:
        require(player_counts[row.player_id,row.game_id,"for"] == (row.spatial.unblocked_for or 0)
                and player_counts[row.player_id,row.game_id,"against"] == (row.spatial.unblocked_against or 0), "spatial player-game cells differ from totals")
    dense = []
    for season in seasons:
        counts = by_player[season.player_id]
        support = season.spatial
        require(sum(counts[0]) == (support.unblocked_for or 0)
                and sum(counts[1]) == (support.unblocked_against or 0), "spatial season count reduction failed")
        if not support.included_seconds:
            continue
        rates = 3600*counts/support.included_seconds
        densities = 100*(pooling()@rates.T).T/areas
        differences = densities-density
        for side in range(2):
            expected = float(rates[side].sum())
            require(math.isclose(float(np.sum(densities[side]*areas/100)),expected,abs_tol=1e-10,rel_tol=1e-10)
                    and math.isclose(float(np.sum(differences[side]*areas/100)),expected-float(raw.sum()),abs_tol=1e-10,rel_tol=1e-10), "spatial mass conservation failed")
        dense.extend(SeasonCell(season.player_id,identity,int(counts[0,i]),int(counts[1,i]),
            float(rates[0,i]),float(rates[1,i]),float(densities[0,i]),float(densities[1,i]),
            float(differences[0,i]),float(differences[1,i])) for i,identity in enumerate(ids))
    return final_cells, tuple(dense), coverage
