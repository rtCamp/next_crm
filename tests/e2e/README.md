# Next-CRM Playwright E2E Test Automation Framework

A comprehensive end-to-end test automation framework for Next-CRM built with Playwright, featuring data-driven testing, role-based authentication, and integrated Allure reporting.

## Table of Contents

- [Overview](#overview)
- [Framework Architecture](#framework-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Naming Conventions](#naming-conventions)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)
- [Additional Resources](#additional-resources)

---

## Overview

This framework provides a robust, scalable solution for testing Next-CRM application with the following key features:

- **Playwright**: Fast, reliable end-to-end testing
- **Page Object Model**: Maintainable and reusable page interactions
- **Data-Driven Testing**: JSON-based test data management
- **Role-Based Testing**: Support for multiple user roles (Admin, Manager, Employee)
- **Parallel Execution**: Run tests concurrently for faster feedback
- **Allure Reporting**: Rich, interactive test reports with history
- **CI/CD Ready**: GitHub Actions integration with scheduled runs
- **Authentication Management**: Persistent session storage per role/worker
- **Global Setup/Teardown**: Automated test data creation and cleanup

---

## Framework Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Global Setup (Before Tests)              │
│  • Discovers active test cases                              │
│  • Generates authentication states for each role            │
│  • Creates test data via API calls                          │
│  • Stores data in JSON files                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Test Execution Phase                      │
│  • Loads test data from JSON files                          │
│  • Uses Page Objects for interactions                       │
│  • Runs tests in parallel across workers                    │
│  • Captures screenshots/videos on failure                   │
│  • Generates Allure results                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Global Teardown (After Tests)             │
│  • Cleans up test data created during setup                 │
│  • Deletes temporary files                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Report Generation                       │
│  • Allure HTML report with history                          │
│  • Playwright HTML report                                   │
│  • JSON results for analysis                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before setting up the framework, ensure you have the following installed:

- **Node.js**: v18 or higher ([Download](https://nodejs.org/))
- **npm**: v8 or higher (comes with Node.js)
- **Java JDK**: v17 or higher (for Allure reports) ([Download](https://www.oracle.com/java/technologies/downloads/))
- **Allure Command Line**: For report generation
  ```bash
  npm install -g allure-commandline
  ```

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd next-crm/tests/e2e
```

### 2. Install Dependencies

```bash
npm ci
```

This will install:

- Playwright Test
- Playwright browsers
- Allure Playwright reporter
- dotenv for environment variables
- Other utility dependencies

### 3. Install Playwright Browsers

```bash
npx playwright install --with-deps
```

This installs Chromium, Firefox, and WebKit browsers along with system dependencies.

---

## Configuration

### 1. Environment Variables

Create a `.env` file in the `tests/e2e/` directory by copying the example:

```bash
cp .env.example .env
```

Update the `.env` file with your environment details.

### 2. Playwright Configuration

The `playwright.config.js` file contains all test execution settings.

**Key Configuration Options:**

- **fullyParallel**: Run all tests in parallel (faster execution)
- **retries**: Retry flaky tests automatically
- **workers**: Number of parallel test workers
- **trace**: Capture detailed execution trace for debugging
- **projects**: Define different test suites with different roles/browsers

---

## Project Structure

```
tests/e2e/
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
├── package.json                 # Node.js dependencies and scripts
├── playwright.config.js         # Playwright test configuration
├── playwright.fixture.js        # Custom fixtures (auth, test data)
│
├── auth/                        # Authentication state files
│   ├── admin-API.json           # API-only auth state
│   └── admin-w0.json            # Browser auth state for worker 0
│
├── data/                        # Test data organized by role
│   ├── admin/
│   │   └── lead.js              # Lead test data for admin
│   ├── manager/                 # Manager test data
│   └── json-files/              # Generated JSON files (runtime)
│       └── TC-LL-2.json         # Test case specific data
│
├── globals/                     # Global setup and teardown
│   ├── globalSetup.js           # Pre-test setup (auth, data creation)
│   └── globalTeardown.js        # Post-test cleanup
│
├── helpers/                     # Helper functions
│   ├── frappeRequests.js        # Generic API request handlers
│   ├── leadTabHelper.js         # Lead-specific data operations
│   └── storageStateHelper.js    # Authentication state management
│
├── pageObjects/                 # Page Object Model classes
│   ├── leadsPage.js             # Leads page interactions
│   └── loginPage.js             # Login page interactions
│
├── scripts/                     # Utility scripts
│   └── list-tests.js            # Discovers active test cases
│
├── specs/                       # Test specifications
│   └── admin/
│       └── lead.spec.js         # Lead management test cases
│
├── utils/                       # Utility functions
│   ├── api/
│   │   ├── authRequestForStorage.js  # Authentication utilities
│   │   ├── frappeRequests.js         # API request wrappers
│   │   └── leadRequests.js           # Lead API operations
│   ├── dataGenerators.js        # Random test data generators
│   ├── fileUtils.js             # File operations (JSON read/write)
│   └── stringUtils.js           # String manipulation utilities
│
├── allure-results/              # Allure test results (generated)
├── allure-report/               # Allure HTML report (generated)
├── playwright-report/           # Playwright HTML report (generated)
├── test-results/                # Screenshots, videos, traces (generated)
└── results.json                 # JSON test results (generated)
```

---

## Running Tests

### Local Execution

#### Run All Tests

```bash
cd tests/e2e/
npm run e2e:tests
```

### Viewing Reports

#### Allure Report (Recommended)

Generate and open the interactive Allure report:

```bash
npm run allure:report
npm run allure:serve
```

This will:

1. Generate the Allure report from test results
2. Start a local web server
3. Open the report in your default browser

#### Playwright HTML Report

```bash
npx playwright show-report
```

---

## Naming Conventions

- **Test IDs**: `TC-<Module>-<Number>` (e.g., `TC-LL-2` for Lead List test case 2)
  - `LL` = Lead List
  - `LD` = Lead Detail
  - `CO` = Contact
  - `DE` = Deal
- **Test Files**: `<module>.spec.js` (e.g., `lead.spec.js`)
- **Page Objects**: `<page>Page.js` (e.g., `leadsPage.js`)
- **Helpers**: `<module>Helper.js` (e.g., `leadTabHelper.js`)

---

## CI/CD Integration

### GitHub Actions Workflow

The framework includes a complete CI/CD pipeline (`.github/workflows/e2e-playwright-test.yml`).

### Running Tests on CI

Tests automatically run when:

- A PR is approved
- Daily at the scheduled time
- Manually triggered from GitHub Actions

---

## Best Practices

### 1. Test Independence

- Each test should be independent and self-contained
- Don't rely on test execution order
- Create necessary data in test setup, clean up in teardown

### 2. Stable Locators

Prefer stable locators:

```javascript
// Good - Data attributes
page.locator('[data-testid="create-button"]');

// Good - Role-based
page.getByRole("button", { name: "Create" });

// Avoid - CSS classes (can change)
page.locator(".btn-primary");
```

### 3. Explicit Waits

Always use explicit waits:

```javascript
// Wait for element to be visible
await expect(page.locator("#element")).toBeVisible();

// Wait for specific state
await page.waitForLoadState("networkidle");
```

### 4. Error Handling

Add meaningful error messages:

```javascript
expect(result, "Lead should be created successfully").toBe(true);
```

### 5. Code Reusability

- Use Page Objects for reusable interactions
- Extract common utilities to helper functions
- Share test data across similar tests

### 6. Naming Conventions

- Use descriptive test names
- Follow consistent naming patterns
- Include test case ID in test name

### 7. Documentation

- Add comments for complex logic
- Document custom fixtures and helpers
- Keep README up to date

---

## Additional Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Allure Report Documentation](https://docs.qameta.io/allure/)
- [JavaScript Testing Best Practices](https://github.com/goldbergyoni/javascript-testing-best-practices)

---

## Support

For questions or issues:

- Contact the QA team
