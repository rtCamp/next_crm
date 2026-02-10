import { expect } from "@playwright/test";

/**
 * LeadsPage class handles interactions with the leads Tab.
 */
export class LeadsPage {
  /**
   * Initializes the LeadsPage object.
   * @param {import('@playwright/test').Page} page - Playwright page instance.
   */
  constructor(page) {
    this.page = page;

    // Create Lead Dialog Selectors
    this.createLeadBtn = page.getByRole("button", { name: "Create" });
    this.createLeadHeading = page.getByRole("heading", { name: "Create Lead" });
    this.closeLeadDialogBtn = page.getByRole("button").filter({ hasText: /^$/ }).nth(1);
    this.salutationBtn = page.getByRole("button", { name: "Select Salutation" });
    this.SalutationDropDownVal = (Salutation) => page.getByRole("option", { name: `${Salutation}`, exact: true });
    this.firstNameInput = page.getByRole("textbox", { name: "Enter First Name" });
    this.lastNameInput = page.getByRole("textbox", { name: "Enter Last Name" });
    this.emailInput = page.getByRole("textbox", { name: "Enter Email" });
    this.mobileInput = page.getByRole("textbox", { name: "Enter Mobile No" });
    this.genderBtn = page.getByRole("button", { name: "Select Gender" });
    this.genderDropDownVal = (gender) => page.getByRole("option", { name: `${gender}`, exact: true });
    this.organizationNameInput = page.getByRole("textbox", { name: "Enter Organization Name" });
    this.annualRevenueInput = page.getByRole("textbox", { name: "Enter Annual Revenue" });
    this.selectLeadStatus = (LeadValue) =>
      page
        .locator("select")
        .last()
        .selectOption({ value: `${LeadValue}` });
    this.createButton = page.getByRole("button", { name: "Create" });

    //Leads Side bar
    //Person section
    this.LeadFirstName = page.getByRole("textbox", { name: "Add First Name..." });
    this.LeadLastName = page.getByRole("textbox", { name: "Add Last Name..." });
    this.LeadEmail = page.getByRole("textbox", { name: "Add Email..." });
    this.LeadMobile = page.getByRole("textbox", { name: "Add Mobile No..." });
    //this.LeadGender = page.getByRole('button', { name: 'Select Gender' });
    this.LeadOrganization = page.getByRole("textbox", { name: "Add Organization Name..." });
    this.LeadAnnualRevenue = page.getByRole("textbox", { name: "Add Annual Revenue..." });

    //Lead -> Top Bar
    this.LeadStatusInPage = (LeadValue) => page.getByRole("button", { name: `${LeadValue}`, exact: true });
  }

  // --------------------------------------
  // General
  // --------------------------------------

  /**
   * Navigates to the timesheet page and waits for it to fully load.
   */
  async goto() {
    await this.page.goto("/next-crm/leads/view", { waitUntil: "domcontentloaded" });
  }
  // ------------------------------------------------------------------------------------------

  // --------------------------------------
  // Leads Tab Actions
  // --------------------------------------

  /**
   * Creates a new Lead with provided test case data
   * @param {Object} tcData  Test case data containing lead details
   */
  async createLead(tcData) {
    // Click on 'Create Lead' button
    await this.createLeadBtn.click();

    // Verify 'Create Lead' dialog is opened
    await expect(this.createLeadHeading).toBeVisible();

    // Fill Lead details
    await this.salutationBtn.click();
    await this.SalutationDropDownVal(tcData.salutation).click();
    await this.firstNameInput.fill(tcData.first_name);
    await this.lastNameInput.fill(tcData.last_name);
    await this.emailInput.fill(tcData.email_id);
    await this.mobileInput.fill(tcData.mobile_no);
    await this.genderBtn.click();
    await this.genderDropDownVal(tcData.gender).click();
    await this.organizationNameInput.fill(tcData.company_name);
    await this.annualRevenueInput.fill(tcData.annual_revenue);
    await this.selectLeadStatus(tcData.status);

    // Click on 'Create' button to create Lead
    await this.createButton.click();

    // Verify Lead is created and dialog is closed
    await expect(this.createLeadHeading).toBeHidden();

    //Wait until lead first name is visible in side bar
    await expect(this.LeadFirstName).toBeVisible();
  }
  // ------------------------------------------------------------------------------------------
  /**
   * Verify the lead details in side bar
   * @param {Object} tcData  Test case data containing lead details
   * @returns {boolean} true if all verifications are passed
   */
  async verifyLeadDetailsInSideBar(tcData) {
    //Verify the lead details in side bar
    await expect(this.LeadFirstName).toHaveValue(tcData.first_name);
    await expect(this.LeadLastName).toHaveValue(tcData.last_name);
    await expect(this.LeadEmail).toHaveValue(tcData.email_id);
    await expect(this.LeadMobile).toHaveValue(tcData.mobile_no);
    //Return true if all the verifications are passed
    return true;
  }
  // ------------------------------------------------------------------------------------------
}
