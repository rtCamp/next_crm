import { test, expect } from "../../playwright.fixture.js";
import { LeadsPage } from "../../pageObjects/leadsPage.js";
import * as allure from "allure-js-commons";
import { readJSONFile } from "../../utils/fileUtils.js";
import path from "path";

// Test suite for Lead creation and verification
test.describe("Lead Management", () => {
  let leadsPage;
  let testData;

  // Setup: Initialize page objects and load test data
  test.beforeEach(async ({ page, jsonDir }) => {
    leadsPage = new LeadsPage(page);

    // Navigate to leads page
    await leadsPage.goto();
  });

  test("TC-LL-2: Create a new lead and verify details", async ({ jsonDir }) => {
    allure.story("Lead");

    // Read test data from JSON file generated in global setup
    const tcId = "TC-LL-2";
    const dataPath = path.join(jsonDir, `${tcId}.json`);
    const jsonData = await readJSONFile(dataPath);
    testData = jsonData[tcId].infoPayloadCreateLead;

    // Step 1: Create a new lead with test data
    await leadsPage.createLead(testData);

    // Step 2: Verify lead is created and sidebar is visible
    await expect(leadsPage.LeadFirstName).toBeVisible();

    // Step 3: Verify lead details in the sidebar
    const isVerified = await leadsPage.verifyLeadDetailsInSideBar(testData);
    expect(isVerified).toBe(true);
  });
});
