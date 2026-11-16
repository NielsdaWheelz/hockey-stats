# goalie sheet history axis label overlaps its first point

actual full-sheet comparison pngs on `63b49e6` show the embedded raw stopping plot's extreme y-axis label overlapping its first point. vejmelka's lower label and jarry's upper label touch the point at the plot's left edge. the repeated values below their years remain readable; this is a layout defect, not numerical loss.

evidence: `/Volumes/Expansion/hockey-stats/runs/application-v1-19-20261114-01/real/exports/comparison/{8478872,8477465}.{png,svg}`. in vejmelka's svg the lower text starts at x44 and extends into the first point at x140; jarry's upper label has the same conflict. the owner is `goalieCardSvg` in `app/src/web/goalie-card.tsx`.

resolve by reserving enough label/point separation without shrinking text or hiding labels. verify actual final downloaded pngs, including both comparison players and ordinary/thin/unused/absent histories, with no clipping, changed values or lost context. source and pixel reviews precede the final same-candidate build/start; no numerical or publication repeat is needed.
