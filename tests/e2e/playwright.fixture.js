import { test as base, expect, devices } from "@playwright/test";
import path from "path";
import fs from "fs/promises";
import { fileURLToPath } from "url";
import { storeStorageState } from "./helpers/storageStateHelper.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Define the single shared JSON directory
const SHARED_JSON_DIR = path.resolve(__dirname, "data", "json-files");
// ------------------------------------------------------------------------------------------

const test = base.extend({
  // Worker-scoped fixture: generate a unique storageState per role per worker
  authState: [
    async ({}, use, testInfo) => {
      const role = testInfo.project.metadata.TEST_ROLE;
      if (!role) {
        throw new Error("`metadata.TEST_ROLE` must be set on the project");
      }

      const workerIndex = testInfo.workerIndex;
      const fileName = `${role}-w${workerIndex}.json`;
      const outPath = path.resolve(__dirname, "./auth", fileName);

      //console.log(`🔐 Setting up auth state for role: ${role}, worker: ${workerIndex}`);

      try {
        await fs.access(outPath);
        //console.log(`✅ Auth state already exists: ${outPath}`);
      } catch {
        //console.log(`🔄 Generating new auth state: ${outPath}`);
        // Generate storage state with CSRF (isApi=false)
        await storeStorageState(role, false, outPath);
      }

      await use(outPath);
    },
    { scope: "worker" },
  ],

  // Fixed JSON directory - same for all workers
  jsonDir: [
    async ({}, use) => {
      //console.log(`📁 Using shared JSON directory: ${SHARED_JSON_DIR}`);

      // Verify directory exists (should be created in global setup)
      try {
        await fs.access(SHARED_JSON_DIR);
        //console.log("✅ JSON directory exists");
      } catch {
        console.error("❌ JSON directory missing - was global setup run?");
        throw new Error("JSON directory not found. Ensure global setup has run.");
      }

      await use(SHARED_JSON_DIR);
    },
    { scope: "worker" },
  ],

  // Override built-in storageState to use our worker-scoped authState
  storageState: async ({ authState }, use) => {
    await use(authState);
  },
});

export { test, expect, devices };
