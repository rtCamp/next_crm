import { request } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import config from "../../playwright.config";

// Load config variables
const baseURL = config.use?.baseURL;
// ------------------------------------------------------------------------------------------

/**
 * Helper function to ensure storage state is loaded for respective roles.
 */
const loadAuthState = (role) => {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const filePath = path.resolve(__dirname, `../../auth/${role}-API.json`);
  if (!fs.existsSync(filePath)) {
    throw new Error(`Auth state file for ${role} not found: ${filePath}`);
  }
  return filePath;
};
// ------------------------------------------------------------------------------------------

/**
 * Helper function to build the API request
 */
export const apiRequest = async (endpoint, options = {}, role = "admin") => {
  const authFilePath = loadAuthState(role);
  const requestContext = await request.newContext({ baseURL, storageState: authFilePath });
  const response = await requestContext.fetch(endpoint, {
    ...options,
    postData: options.data ? JSON.stringify(options.data) : undefined, // Transform to json format
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  let responseData;
  if (response.ok()) {
    responseData = await response.json();
  } else {
    await requestContext.dispose();
    throw new Error(
      `API request failed for ${role} and endpoint ${endpoint}: ${response.status()} ${response.statusText()}`,
    );
  }

  await requestContext.dispose();
  return responseData;
};
// ------------------------------------------------------------------------------------------

/**
 * Get Lead List
 */
export const getLead = async (leadName, role = "admin") => {
  const endpoint = `/api/resource/Lead/${encodeURIComponent(leadName)}`;
  const options = {
    method: "GET",
  };
  return await apiRequest(endpoint, options, role);
};
// ------------------------------------------------------------------------------------------

/**
 * Create Lead via API
 */
export const createLead = async (leadData, role = "admin") => {
  const endpoint = `/api/resource/Lead`;
  const options = {
    method: "POST",
    data: leadData,
  };
  return await apiRequest(endpoint, options, role);
};
// ------------------------------------------------------------------------------------------

/**
 * Delete Lead via API
 */
export const deleteLead = async (leadName, role = "admin") => {
  const endpoint = `/api/resource/Lead/${encodeURIComponent(leadName)}`;
  const options = {
    method: "DELETE",
  };
  return await apiRequest(endpoint, options, role);
};
// ------------------------------------------------------------------------------------------
