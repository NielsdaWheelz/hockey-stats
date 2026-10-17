import { reactRouter } from "@react-router/dev/vite";
import { isBuiltin } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const root = fileURLToPath(new URL(".", import.meta.url));
const web = resolve(root, "src/web") + "/";
const shared = resolve(root, "src/shared") + "/";

export default defineConfig({
  plugins: [
    {
      name: "browser-boundary",
      enforce: "pre",
      resolveId(source, importer) {
        if (
          importer === undefined ||
          ![web, shared].some((directory) => importer.startsWith(directory))
        )
          return;
        if (
          isBuiltin(source) ||
          ["@effect/platform-node", "@effect/sql-sqlite-node"].some(
            (name) => source === name || source.startsWith(name + "/"),
          )
        ) {
          this.error(
            `browser modules cannot import server implementation ${source}`,
          );
        }
        if (source.startsWith(".") || source.startsWith(root)) {
          const target = resolve(dirname(importer), source);
          if (![web, shared].some((directory) => target.startsWith(directory)))
            this.error(
              `browser imports must stay within web/shared: ${source}`,
            );
        }
      },
    },
    {
      name: "development-server",
      configureServer(server) {
        if (server.config.server.host !== "127.0.0.1")
          throw new Error("development server must bind to 127.0.0.1");
        // router html bypasses vite's static-response header setting.
        server.middlewares.use((_request, response, next) => {
          response.setHeader("Cache-Control", "no-store");
          next();
        });
      },
    },
    reactRouter(),
  ],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:3000" },
  },
});
