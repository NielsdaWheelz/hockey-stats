import { index, route, type RouteConfig } from "@react-router/dev/routes";

export default [
  index("routes/league.tsx"),
  route("players/:playerId", "routes/player.tsx"),
] satisfies RouteConfig;
