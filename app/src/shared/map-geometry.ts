import type { DisplayGrid, GoalieEvidenceMap } from "./player-analysis.js";

export const goaliePoint = (x: number, y: number) => ({ x: 100 - x, y: 42.5 + y });
export const goaliePhysicalPoint = (x: number, y: number) => ({ x: 100 - x, y: y - 42.5 });

export function goalieEvidenceDisplayCells(
  grid: typeof DisplayGrid.Type,
  cells: typeof GoalieEvidenceMap.Type["display_cells"],
) {
  const geometry = new Map(grid.cells.map(cell => [cell.cell_id, cell]));
  return cells.map(cell => {
    const bounds = geometry.get(cell.cell_id);
    if (!bounds) throw new Error("goalie evidence display geometry is missing");
    return { ...cell, bounds, density_per100sqft: 100 * cell.mass_saved / bounds.area_sqft };
  });
}
