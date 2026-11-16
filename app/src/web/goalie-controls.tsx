import type { GoalieSelection } from "./explorer";

export default function GoalieControls({ selection, render, onChange, onRenderChange }: {
  readonly selection: GoalieSelection;
  readonly render: "contours" | "rectangles";
  readonly onChange: (changes: Partial<GoalieSelection>) => void;
  readonly onRenderChange: (render: "contours" | "rectangles") => void;
}) {
  return <section className="comparative-controls" aria-label="goalie selections">
    <label>modeled core strength<select value={selection.coreStrength}
      onChange={event => onChange({ coreStrength: event.currentTarget.value as GoalieSelection["coreStrength"] })}>
      <option value="ev">ev · 5v5 / 4v4 / 3v3</option><option value="pk">pk · defending 4v5 / 3v5 / 3v4</option>
    </select></label>
    <label>actual evidence strength<select value={selection.evidenceStrength}
      onChange={event => onChange({ evidenceStrength: event.currentTarget.value as GoalieSelection["evidenceStrength"] })}>
      {["ev", "pk", "5v5", "4v4", "3v3", "5v4", "5v3", "4v3", "4v5", "3v5", "3v4", "covered_all"].map(value => <option key={value} value={value}>{value}</option>)}
    </select></label>
    <label>actual population<select value={selection.population}
      onChange={event => onChange({ population: event.currentTarget.value as GoalieSelection["population"] })}>
      <option value="unblocked">unblocked</option><option value="on_net">on-net</option>
    </select></label>
    <label>actual map quantity<select value={selection.evidenceView}
      onChange={event => onChange({ evidenceView: event.currentTarget.value as GoalieSelection["evidenceView"] })}>
      <option value="mass">saved above expected · additive</option><option value="ratio">goals / expected · league-relative ratio</option>
    </select></label>
    <label>detail type<select value={selection.type}
      onChange={event => onChange({ type: event.currentTarget.value as GoalieSelection["type"] })}>
      <option value="all">all</option><option value="wrist_snap">wrist + snap</option><option value="slap">slap</option>
      <option value="tip">tip / deflection</option><option value="backhand">backhand</option><option value="other">other</option>
    </select></label>
    <label>map drawing<select value={render} onChange={event => onRenderChange(event.currentTarget.value as typeof render)}>
      <option value="contours">contours · ratio remains cells</option><option value="rectangles">display cells</option>
    </select></label>
    <p>actual selections apply to saving, type panels and danger. modeled stopping retains its ev/pk common reference. covered_all is supported actual-state coverage; it has no modeled coefficient or cohort.</p>
  </section>;
}
