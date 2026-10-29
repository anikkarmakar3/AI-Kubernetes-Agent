import { createClient } from "@insforge/sdk";

const baseUrl = process.env.NEXT_PUBLIC_INSFORGE_BASE_URL;
const anonKey = process.env.NEXT_PUBLIC_INSFORGE_ANON_KEY;

function isValidConfig(value: string | undefined, placeholder: string) {
  return Boolean(value && value.trim() && !value.includes(placeholder));
}

const hasValidBaseUrl = isValidConfig(baseUrl, "your-project.region.insforge.app");
const hasValidAnonKey = isValidConfig(anonKey, "your-anon-key");

export const insforge = hasValidBaseUrl && hasValidAnonKey && baseUrl && anonKey
  ? createClient({ baseUrl, anonKey })
  : null;
export const isInsforgeConfigured = Boolean(insforge);
