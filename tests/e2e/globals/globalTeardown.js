import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import { deleteLeadForTestCases } from "../helpers/leadTabHelper.js";
// ------------------------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Global teardown function to delete the stale test data after running tests.
 */
const globalTeardown = async () => {
  // Locate and read test-tc-ids.json
  const projectRoot = path.resolve(__dirname, "..");
  const tcJsonPath = path.join(projectRoot, "test-tc-ids.json");

  let allTCIds = [];
  try {
    const rawTcs = await fs.promises.readFile(tcJsonPath, "utf-8");
    allTCIds = JSON.parse(rawTcs);
    console.log(`🧹 Loaded TC IDs for teardown: ${allTCIds.join(", ")}`);
  } catch (err) {
    console.warn("⚠️ Could not load TC IDs:", err.message);
  }

  //Delete leads for all the TC IDs created during tests
  for (const tcId of allTCIds) {
    await deleteLeadForTestCases([tcId], path.join(__dirname, "../data/json-files"));
  }
  console.log("✅ Global teardown completed: test data cleaned up.");
};

export default globalTeardown;
