import { storeStorageState } from "../helpers/storageStateHelper";
import { createJSONFile, populateJsonStubs } from "../utils/fileUtils";
import path from "path";
import fs from "fs";
import { execSync } from "child_process";
import { fileURLToPath } from "url";
import { createLeadForTestCases } from "../helpers/leadTabHelper";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const globalSetup = async () => {
  console.log("🚀 Starting global setup...");

  // 0) Discover active tests and extract TC IDs
  console.log("🔍 Discovering active tests via list-tests.js...");
  const projectRoot = path.resolve(__dirname, "..");
  let rawList = "[]";
  try {
    rawList = execSync("node scripts/list-tests.js", {
      cwd: projectRoot,
      stdio: ["ignore", "pipe", "inherit"],
    }).toString();
  } catch (err) {
    console.warn("⚠️ list-tests.js did not return any tests:", err.message);
  }

  let tests = [];
  try {
    tests = JSON.parse(rawList);
  } catch {
    tests = [];
  }

  //Match TC IDs in the format TC-<tabName>-<TCNumber>
  const tcPattern = /TC-([A-Z]+)-(\d+)/g;
  const tcSet = new Set();
  tests.forEach(({ title }) => {
    let match;
    while ((match = tcPattern.exec(title)) !== null) {
      tcSet.add(`TC-${match[1]}-${match[2]}`);
    }
  });
  const allTCIds = Array.from(tcSet);
  console.log(`📑 Extracted TC IDs: ${allTCIds.join(", ")}`);

  // Persist TC IDs
  const tcJsonPath = path.join(projectRoot, "test-tc-ids.json");
  fs.writeFileSync(tcJsonPath, JSON.stringify(allTCIds, null, 2));
  console.log(`✅ TC ID list written to: ${tcJsonPath}`);

  // 1) Pre‑generate API auth states for all roles
  const roles = ["admin"];
  await Promise.all(roles.map((role) => storeStorageState(role, true)));

  // 2) Create and populate JSON stubs for each TC ID
  console.log("📁 Creating JSON stubs for each TC ID...");

  const jsonDir = path.resolve(__dirname, "../data/json-files");
  await fs.promises.mkdir(jsonDir, { recursive: true });
  for (const tcId of allTCIds) {
    const filePath = path.join(jsonDir, `${tcId}.json`);
    await createJSONFile(filePath, { [tcId]: {} });
    await populateJsonStubs(jsonDir, [tcId]);
  }

  // Verify JSON files
  //console.log("🔍 Verifying JSON stubs...");
  for (const tcId of allTCIds) {
    const filePath = path.join(jsonDir, `${tcId}.json`);
    const content = await fs.promises.readFile(filePath, "utf-8");
    const data = JSON.parse(content);
    if (!data[tcId]) {
      throw new Error(`Missing data for ${tcId}`);
    }
  }

  // 3) Clean up orphan data (Not implemented here - placeholder for future)

  // 4) Generate data for each TC in sequence
  console.log("🛠 Generating test data per TC ID...");
  for (const tcId of allTCIds) {
    console.log(`➡️ Processing ${tcId}`);
    await createLeadForTestCases([tcId], jsonDir);
  }

  console.log("✅ Data generation completed for all TC IDs! Global setup done.");
};

export default globalSetup;
