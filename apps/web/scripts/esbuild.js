const esbuild = require("esbuild");
const path = require("path");

const options = {
  entryPoints: [path.resolve(__dirname, "..", "index.js")],
  bundle: true,
  outfile: path.resolve(__dirname, "..", "bin", "main.js"),
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
