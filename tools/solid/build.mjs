// node build.mjs  ->  ../../assets/solid-auth.js and ../../assets/qrcode.js (self-contained files, no CDN at runtime)
import { build } from "esbuild";
import { fileURLToPath } from "node:url";
const here = (p) => fileURLToPath(new URL(p, import.meta.url));
await build({
  entryPoints: [here("./entry.js")], outfile: here("../../assets/solid-auth.js"),
  bundle: true, minify: true, format: "iife", platform: "browser", target: ["es2020"],
  legalComments: "inline",
  banner: { js: "/* Desk pod mode: @inrupt/solid-client-authn-browser 5.0.1 (MIT, Inrupt Inc.) and its dependencies, bundled with esbuild. Rebuild: cd tools/solid && npm install && npm run build */" },
});
await build({
  entryPoints: [here("./entry-qr.js")], outfile: here("../../assets/qrcode.js"),
  bundle: true, minify: true, format: "iife", platform: "browser", target: ["es2020"], legalComments: "inline",
  banner: { js: "/* Desk pod mode: qrcode-generator 1.4.4 (MIT, Kazuhiko Arase), bundled with esbuild. Rebuild: cd tools/solid && npm install && npm run build */" },
});
console.log("wrote assets/solid-auth.js and assets/qrcode.js");
