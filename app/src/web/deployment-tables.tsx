import { useId, useState } from "react";
import { Link } from "react-router";
import type { Deployment, PlayerSummary, Season } from "../shared/observed";
import { CoverageDetail, Minutes, playerName, seasonLabel } from "./presentation";

const timeShare = (sharedSeconds: number, includedSeconds: number) => {
  const percent = (100 * sharedSeconds) / includedSeconds;
  return percent < 0.1 ? "<0.1%" : `${percent.toFixed(1)}%`;
};

export default function DeploymentTables({
  season,
  player,
  deployment,
  players,
  profileLink,
}: {
  readonly season: Season;
  readonly player: PlayerSummary;
  readonly deployment: Deployment;
  readonly players: readonly PlayerSummary[];
  readonly profileLink: (playerId: string) => {
    readonly to: string;
    readonly state: unknown;
  };
}) {
  const id = useId();
  const [expanded, setExpanded] = useState({ teammates: false, opponents: false });
  const identities = new Map(players.map((row) => [row.player_id, row]));
  const seconds = player.metrics.included_seconds;
  return (
    <section className="deployment-context" aria-labelledby={`${id}-heading`}>
      <h3 id={`${id}-heading`}>5v5 deployment · {seasonLabel(season)}</h3>
      {seconds > 0 ? (
        <p className="deployment-explanation">
          shares use {playerName(player)}'s <Minutes seconds={seconds} /> included
          5v5 minutes, including intervals with no recorded attempts. shares
          overlap: each included second counts for four teammates and five
          opponents.
        </p>
      ) : (
        <p>included on-ice time: <Minutes seconds={seconds} /> minutes.</p>
      )}
      <CoverageDetail metrics={player.metrics} />
      {seconds === 0 ? (
        <p>
          {player.metrics.coverage_status === "unavailable"
            ? "shared time is unavailable in the included evidence"
            : "no included 5v5 time to report"}
        </p>
      ) : (
        <>
          <p className="deployment-explanation">
            a player can appear in both tables after a trade. an omitted
            counterpart may have shared excluded or unavailable time.
          </p>
          <div className="deployment-tables">
            {(["teammates", "opponents"] as const).map((relation) => {
              const peers = deployment[relation];
              const visible = expanded[relation] ? peers : peers.slice(0, 10);
              const title = relation === "teammates"
                ? "teammates shared with"
                : "opponents faced";
              return (
                <section key={relation} aria-labelledby={`${id}-${relation}-heading`}>
                  <h4 id={`${id}-${relation}-heading`}>{title}</h4>
                  <table className="deployment-table" id={`${id}-${relation}`}>
                    <caption>
                      ordered by exact shared included 5v5 time; shares use the
                      selected player's included on-ice time.
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">name / reported position</th>
                        <th scope="col" className="numeric">shared min</th>
                        <th scope="col" className="numeric">share of included time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visible.map((peer) => {
                        const counterpart = identities.get(peer.player_id)!;
                        return (
                          <tr key={peer.player_id}>
                            <th scope="row">
                              <Link {...profileLink(peer.player_id)}>{playerName(counterpart)}</Link>
                              <span className="deployment-position">{counterpart.reported_position}</span>
                            </th>
                            <td className="numeric"><Minutes seconds={peer.shared_seconds} /></td>
                            <td className="numeric">{timeShare(peer.shared_seconds, seconds)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  <div className="deployment-expansion">
                    <p aria-live="polite">showing {visible.length} of {peers.length}</p>
                    {peers.length > 10 && (
                      <button
                        type="button"
                        aria-label={expanded[relation] ? `show fewer ${relation}` : `show all ${peers.length} ${relation}`}
                        aria-expanded={expanded[relation]}
                        aria-controls={`${id}-${relation}`}
                        onClick={() => setExpanded((current) => ({ ...current, [relation]: !current[relation] }))}
                      >
                        {expanded[relation] ? "show fewer" : `show all ${peers.length}`}
                      </button>
                    )}
                  </div>
                </section>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
