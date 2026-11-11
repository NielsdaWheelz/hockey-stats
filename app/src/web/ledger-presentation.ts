export const ledgerPresentation = [
  ["5v5 offense", "five_on_five_offense", "spatial.5v5.offense_xg_per60"],
  ["5v5 defense", "five_on_five_defense", "spatial.5v5.defense_xg_per60"],
  ["pp offense", "power_play_offense", "spatial.pp.offense_xg_per60"],
  ["pk defense", "penalty_kill_defense", "spatial.pk.defense_xg_per60"],
  ["finishing", "finishing", "execution.5v5.finishing_goals_per100_attempts"],
  [
    "inferred setting",
    "setting",
    "execution.5v5.setting_goals_per100_assisted_opportunities",
  ],
  ["drawing", "penalties_drawn", "penalties.drawn_value_per60"],
  ["taking", "penalties_taken", "penalties.taken_value_per60"],
  ["ice won", "ice_won", "territory.ice_won_goals_per_basket"],
  ["ice lost", "ice_lost", "territory.ice_lost_goals_per_basket"],
] as const;
