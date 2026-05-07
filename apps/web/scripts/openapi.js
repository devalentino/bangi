const fs = require("fs");
const https = require("https");
const path = require("path");

const DEFAULT_SPEC_URL =
  process.env.OPENAPI_SPEC_URL
  || "https://tracker.i-cosanzeana.me/openapi/openapi.json";
const CACHE_DIR = path.join(__dirname, "..", ".cache");
const CACHE_FILE = path.join(CACHE_DIR, "openapi.json");
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

function ensureCacheDir() {
  fs.mkdirSync(CACHE_DIR, { recursive: true });
}

function formatDate(timestamp) {
  return new Date(timestamp).toISOString();
}

function printUsage() {
  console.log("Usage: node scripts/openapi.js <download|check> [url]");
}

function download(url) {
  ensureCacheDir();

  https
    .get(url, function (response) {
      if (response.statusCode !== 200) {
        console.error(`Failed to download spec: HTTP ${response.statusCode}`);
        response.resume();
        process.exitCode = 1;
        return;
      }

      const chunks = [];

      response.on("data", function (chunk) {
        chunks.push(chunk);
      });

      response.on("end", function () {
        const body = Buffer.concat(chunks).toString("utf8");

        try {
          JSON.parse(body);
        } catch (error) {
          console.error("Downloaded content is not valid JSON.");
          process.exitCode = 1;
          return;
        }

        fs.writeFileSync(CACHE_FILE, body);
        console.log(`Saved OpenAPI spec to ${CACHE_FILE}`);
      });
    })
    .on("error", function (error) {
      console.error(`Failed to download spec: ${error.message}`);
      process.exitCode = 1;
    });
}

function check() {
  if (!fs.existsSync(CACHE_FILE)) {
    console.log("OpenAPI spec cache is missing.");
    console.log("Run: npm run openapi:download");
    return;
  }

  const stats = fs.statSync(CACHE_FILE);
  const ageMs = Date.now() - stats.mtimeMs;

  if (ageMs > ONE_DAY_MS) {
    console.log(
      `OpenAPI spec cache is stale (last updated ${formatDate(stats.mtimeMs)}).`,
    );
    console.log("Run: npm run openapi:download");
    return;
  }

  console.log(
    `OpenAPI spec cache is fresh (last updated ${formatDate(stats.mtimeMs)}).`,
  );
}

const command = process.argv[2];
const url = process.argv[3] || DEFAULT_SPEC_URL;

if (command === "download") {
  download(url);
} else if (command === "check") {
  check();
} else {
  printUsage();
  process.exitCode = 1;
}
