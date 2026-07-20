// Marks dist/cjs as CommonJS and dist/esm as ESM so Node resolves each
// build correctly regardless of the package root "type".
import { writeFileSync, mkdirSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

// ESM requires explicit file extensions on relative imports; the TS source
// uses extensionless imports (valid for CJS), so append ".js" in dist/esm.
for (const file of readdirSync("dist/esm").filter((f) => f.endsWith(".js"))) {
  const path = join("dist/esm", file);
  const src = readFileSync(path, "utf8").replace(
    /(from\s+["'])(\.\.?\/[^"']+?)(["'])/g,
    (m, pre, spec, post) =>
      /\.(js|json|mjs)$/.test(spec) ? m : pre + spec + ".js" + post
  );
  writeFileSync(path, src);
}
console.log("fixup-dist: appended .js to relative ESM imports");

mkdirSync("dist/cjs", { recursive: true });
mkdirSync("dist/esm", { recursive: true });
writeFileSync("dist/cjs/package.json", JSON.stringify({ type: "commonjs" }) + "\n");
writeFileSync("dist/esm/package.json", JSON.stringify({ type: "module" }) + "\n");
console.log("fixup-dist: wrote dist/cjs/package.json and dist/esm/package.json");
