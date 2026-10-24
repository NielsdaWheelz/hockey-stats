import { useRef, useState } from "react";
import type { PlayerIdentity } from "./presentation";
import { matchingPlayers, nameOrder, playerName, teamName } from "./presentation";

export default function PlayerPicker<T extends PlayerIdentity>({
  slot,
  players,
  selected,
  error,
  otherId,
  committedPair,
  onChoose,
  onClear,
}: {
  readonly slot: "first" | "second";
  readonly players: readonly T[];
  readonly selected: T | undefined;
  readonly error: string | undefined;
  readonly otherId: string | undefined;
  readonly committedPair: string;
  readonly onChoose: (player: T) => void;
  readonly onClear: () => void;
}) {
  const [search, setSearch] = useState({ committedPair, draft: "" });
  if (search.committedPair !== committedPair)
    setSearch({ committedPair, draft: "" });
  const draft = search.draft;
  const input = useRef<HTMLInputElement>(null);
  const matches = draft.trim()
    ? matchingPlayers(players, draft)
        .filter((player) => player.player_id !== otherId)
        .sort(nameOrder)
    : [];
  return (
    <fieldset className="player-picker">
      <legend>{slot} player</legend>
      <p id={`${slot}-selection`} className="picker-selection">
        {selected ? (
          <>
            {playerName(selected)} · {selected.teams.map(teamName).join(" / ")} ·
            reported position {selected.reported_position ?? "unavailable"} · player{" "}
            {selected.player_id}
          </>
        ) : (
          `choose ${slot} player`
        )}
      </p>
      {error && (
        <p id={`${slot}-error`} className="selection-error">
          {error}
        </p>
      )}
      <label htmlFor={`${slot}-player-search`}>search {slot} player</label>
      <input
        ref={input}
        id={`${slot}-player-search`}
        type="search"
        value={draft}
        aria-describedby={`${slot}-selection${error ? ` ${slot}-error` : ""}`}
        onChange={(event) =>
          setSearch({ committedPair, draft: event.currentTarget.value })
        }
        autoComplete="off"
        spellCheck={false}
      />
      <button
        type="button"
        className="picker-clear"
        onClick={() => {
          onClear();
          setSearch({ committedPair, draft: "" });
          input.current?.focus();
        }}
      >
        clear {slot} player
      </button>
      {!draft.trim() ? (
        <p className="picker-hint">search by player name</p>
      ) : matches.length === 0 ? (
        <p className="picker-hint">no other players match this name</p>
      ) : (
        <>
          <p className="picker-hint">
            {matches.length} matching {matches.length === 1 ? "player" : "players"}
            {matches.length > 10 && (
              <>; showing 10 of {matches.length}; refine this name</>
            )}
          </p>
          <ul className="picker-results">
            {matches.slice(0, 10).map((player) => (
              <li key={player.player_id}>
                <button
                  type="button"
                  aria-label={`choose ${playerName(player)}, player ${player.player_id}, as ${slot} player`}
                  onClick={() => {
                    onChoose(player);
                    setSearch({ committedPair, draft: "" });
                    input.current?.focus();
                  }}
                >
                  <span>{playerName(player)}</span>
                  <span>
                    {player.teams.map(teamName).join(" / ")} · reported position{" "}
                    {player.reported_position ?? "unavailable"} · player {player.player_id}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </fieldset>
  );
}
