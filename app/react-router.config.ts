import type { Config } from "@react-router/dev/config";

export default {
  ssr: false,
  appDirectory: "src/web",
  buildDirectory: "dist",
  routeDiscovery: { mode: "initial" },
} satisfies Config;
