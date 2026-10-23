import type { SqliteClient } from "@effect/sql-sqlite-node/SqliteClient";
import * as Effect from "effect/Effect";

// the pinned sqlite adapter has no streaming cursor. keep one bounded batch live.
export const forEachRow = <E, R>(
  sql: SqliteClient,
  table: string,
  visit: (row: Record<string, unknown>) => Effect.Effect<unknown, E, R>,
) =>
  Effect.gen(function* () {
    let after: number | undefined;
    while (true) {
      const rows = yield* sql.unsafe<Record<string, unknown> & { __rowid: number }>(
        `SELECT rowid AS __rowid,* FROM ${table}${after === undefined ? "" : " WHERE rowid>?"} ORDER BY rowid LIMIT 128`,
        after === undefined ? [] : [after],
      );
      if (rows.length === 0) break;
      for (const { __rowid, ...row } of rows) {
        yield* visit(row);
        after = __rowid;
      }
    }
  });

// JSON.parse owns syntax; this scan rejects duplicate keys after JSON escape decoding.
export const strictJson = (text: string): unknown => {
  const value: unknown = JSON.parse(text);
  const stack: Array<{ object: boolean; keys: Set<string>; key: boolean }> = [];
  for (const token of text.match(/"(?:[^"\\]|\\.)*"|[{}\[\]:,]/g) ?? []) {
    const top = stack.at(-1);
    if (token === "{" || token === "[")
      stack.push({ object: token === "{", keys: new Set(), key: token === "{" });
    else if (token === "}" || token === "]") stack.pop();
    else if (token === "," && top?.object) top.key = true;
    else if (token === ":" && top?.object) top.key = false;
    else if (token.startsWith('"') && top?.object && top.key) {
      const key = JSON.parse(token) as string;
      if (top.keys.has(key)) throw new Error("duplicate stored JSON key");
      top.keys.add(key);
    }
  }
  return value;
};
