// node build.mjs  ->  ../../assets/solid-auth.js (one self-contained file, no CDN at runtime)
import { build } from "esbuild";
import { fileURLToPath } from "node:url";
const here = (p) => fileURLToPath(new URL(p, import.meta.url));
await build({
  entryPoints: [here("./entry.js")], outfile: here("../../assets/solid-auth.js"),
  bundle: true, minify: true, format: "iife", platform: "browser", target: ["es2020"],
  legalComments: "inline",
  banner: { js: "/* Desk pod mode: @inrupt/solid-client-authn-browser 5.0.1 (MIT, Inrupt Inc.) and its dependencies, bundled with esbuild. Rebuild: cd tools/solid && npm install && npm run build */" },
});
console.log("wrote assets/solid-auth.js");
