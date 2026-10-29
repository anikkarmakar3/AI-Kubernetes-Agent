import axios from "axios";

import type { Cluster, HealthStatus, InvestigationResponse } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  timeout: 8000,
});

export async function getHealth(): Promise<HealthStatus> {
  const response = await api.get<HealthStatus>("/health");
  return response.data;
}

export async function getClusters(): Promise<Cluster[]> {
  const response = await api.get<Cluster[]>("/clusters");
  return response.data;
}

export async function investigateCluster(context?: string, token?: string): Promise<InvestigationResponse> {
  const response = await api.post<InvestigationResponse>("/investigate", { context }, token ? { headers: { Authorization: `Bearer ${token}` } } : undefined);
  return response.data;
}
