import path from "path";
import { readJSONFile } from "../utils/fileUtils";

import { createLead, deleteLead } from "../utils/api/leadRequests";
import { filterApi } from "../utils/api/frappeRequests.js";
// ------------------------------------------------------------------------------------------

/**
 * Creates Lead(s) for provided testCaseID(s).
 * @param {string[]} testCaseID  IDs to process
 * @param {string} jsonDir  Directory where JSON stubs are located
 */
export const createLeadForTestCases = async (testCaseID, jsonDir) => {
  if (!Array.isArray(testCaseID) || testCaseID.length === 0) return;
  const [tcId] = testCaseID;
  const stubPath = path.join(jsonDir, `${tcId}.json`);
  const fullStub = await readJSONFile(stubPath);
  const entry = fullStub[tcId];
  if (!entry || !entry.payloadCreateLead) {
    console.warn(`Skipping ${tcId}: no payloadCreateLead`);
    return;
  }

  try {
    await createLead(entry.payloadCreateLead);
    console.log(`✅ Created Lead for '${tcId}'`);
  } catch (error) {
    console.error(`❌ Failed to create Lead for '${tcId}': ${error.message}`);
  }
};

// ------------------------------------------------------------------------------------------

/**
 * Deletes Lead(s) for provided testCaseID(s).
 * @param {string[]} testCaseID  IDs to process
 * @param {string} jsonDir  Directory where JSON stubs are located
 */
export const deleteLeadForTestCases = async (testCaseID, jsonDir) => {
  if (!Array.isArray(testCaseID) || testCaseID.length === 0) return;
  const [tcId] = testCaseID;
  const stubPath = path.join(jsonDir, `${tcId}.json`);
  const fullStub = await readJSONFile(stubPath);
  const entry = fullStub[tcId];
  //Print entry for debugging
  console.log(`Entry or TEST CASE for ${tcId}:`, entry);
  if (!entry || !entry.infoPayloadCreateLead || !entry.infoPayloadCreateLead.company_name) {
    console.warn(`Skipping ${tcId}: No company_name to identify Lead`);
    return;
  }

  try {
    const leadRes = await filterApi("Lead", [["Lead", "company_name", "=", entry.infoPayloadCreateLead.company_name]]);

    // Extract lead names from the response and delete each lead
    if (leadRes?.message?.values && Array.isArray(leadRes.message.values)) {
      const leadNames = leadRes.message.values.map((valueArray) => valueArray[0]);

      // Delete each lead individually
      const deletePromises = leadNames.map(async (leadName) => {
        try {
          await deleteLead(leadName);
          console.log(`✅ Successfully deleted Lead: ${leadName}`);
        } catch (deleteError) {
          console.error(`❌ Failed to delete Lead '${leadName}': ${deleteError.message}`);
          throw deleteError;
        }
      });

      // Wait for all deletions to complete
      await Promise.all(deletePromises);
      console.log(
        `✅ Completed deletion process for '${tcId}' with company_name '${entry.infoPayloadCreateLead.company_name}'`,
      );
    } else {
      console.warn(`No leads found for '${tcId}' with company_name '${entry.infoPayloadCreateLead.company_name}'`);
    }
  } catch (error) {
    console.error(
      `❌ Failed to delete Lead for '${tcId}' with company_name '${entry.infoPayloadCreateLead.company_name}': ${error.message}`,
    );
  }
};
