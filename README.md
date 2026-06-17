> [!WARNING]
> **Next CRM is being archived.** This repository is being archived effective immediately and will remain publicly accessible in a read-only state. You can continue to browse the code and reference the project history, but no new development, issues, or pull requests will be accepted.

## Why we are discontinuing it

Next CRM served its purpose well, but [Frappe CRM](https://github.com/frappe/crm) has matured significantly over time with new features, improvements, and active maintenance.

Maintaining a fork and continuously syncing upstream changes has become increasingly difficult and inefficient. Additionally, with ERPNext CRM DocTypes planned for deprecation in the future, we do not want to carry the long-term maintenance burden of supporting legacy CRM structures.

## What's next?

Use [Frappe CRM](https://github.com/frappe/crm) (the upstream app) for your CRM needs.

## Migration to Frappe CRM

We have built a migration app ([erpnext_crm_to_frappe_crm_migrator](https://github.com/rtCamp/erpnext_crm_to_frappe_crm_migrator)) that migrates data from ERPNext CRM and Next CRM DocTypes to [Frappe CRM](https://github.com/frappe/crm), including the required field mappings. Going forward, Frappe CRM will be the single source of truth for CRM data.

## Extended features

We built [Frappe CRM XT](https://github.com/rtCamp/frappe_crm_xt), an extension app for features required by our sales team. We will continue adding custom functionality there and contribute generic improvements back to [Frappe CRM](https://github.com/frappe/crm) whenever possible.

---

<div align="center">
    <img width="60" src=".github/logo.png" alt="Next CRM Logo">
    <h1>Next CRM</h1>
</div>

<div align="center">
    <a href="https://frappe.io/products/crm">
        <img width="800" alt="Screenshot of Opportunity page" src=".github/screenshots/OpportunityPage.jpeg">
    </a>
</div>

<p align="center">
    <a href="https://img.shields.io/github/license/frappe/crm">
        <img alt="license" src="https://img.shields.io/github/license/frappe/crm">
    </a>
</p>

## Key Features

-   **Views:** Create custom views which is a combination of filters, sort and columns.
    -   **Pinned View:** Pin important leads and opportunities in the sidebar.
    -   **Public View:** Share views with all users.
    -   **Saved View:** Save views for later use.
-   **Email Communication:** Send and receive emails directly from the Lead/Opportunity Page.
-   **Email Templates:** Create and use email templates for faster communication.
-   **Comments:** Add comments to leads and opportunities to keep track of the conversation.
-   **Notifications:** Get notified when someone mentions you in a comment.
-   **Service Level Agreement:** Set SLA for leads and opportunities and get notified when the SLA is breached.
-   **Assignment Rule:** Automatically assign leads and opportunities to users based on the criteria.
-   **ToDos:** Create todos for leads and opportunity.
-   **Notes:** Add notes to leads and opportunity.
-   **Call Logs:** See the call logs with call details and recordings.

## Getting Started

### Local Setup

1. [Install Bench](https://github.com/frappe/bench).
2. [Install ERPNext](https://github.com/frappe/erpnext)
2. Get the Next CRM app:
    ```sh
    $ bench get-app https://github.com/rtCamp/next-crm --branch next-develop
    ```
3. Create a site with the crm app:
    ```sh
    $ bench --site sitename.localhost install-app next_crm
    ```
4. Open the site in the browser:
    ```sh
    $ bench browse sitename.localhost --user Administrator
    ```
5. Access the crm page at `sitename.localhost:8000/next-crm` in your web browser.

### Changes other than DocType

1. App renamed to Next CRM
2. URL changed from /crm to /next-crm
3. Lead is compulsory to create Opportunity (being reconsidered)
4. ERPNext integration enabled by default

### Removed Features
1. CRM Invitation –  Permissions from the ERPNext CRM module are used directly.
2. Ability to link to ERPNext on a different site –  Not required as this is tightly integrated with the ERPNext CRM module.

We’d love your feedback! Please check it out and share your thoughts on <a href="https://discuss.frappe.io/t/next-crm-integrating-frappe-crm-seamlessly-with-erpnexts-crm-module/138001">Discuss Forum</a>.
