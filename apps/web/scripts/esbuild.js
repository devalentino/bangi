const esbuild = require("esbuild");
const path = require("path");
const dotenv = require("dotenv");

dotenv.config({ path: path.resolve(__dirname, "..", "..", "..", ".env") });

const define = {};
for (const k in process.env) {
  define[`process.env.${k}`] = JSON.stringify(process.env[k]);
}

const options = {
  entryPoints: [path.resolve(__dirname, "..", "index.js")],
  bundle: true,
  outfile: path.resolve(__dirname, "..", "bin", "main.js"),
  define: define,
};

async function run() {
  if (process.argv.includes("--watch")) {
    const context = await esbuild.context(options);
    await context.watch();
    return;
  }

  await esbuild.build(options);
}

run().catch(() => process.exit(1));
