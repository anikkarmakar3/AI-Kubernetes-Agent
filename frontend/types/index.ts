export type HealthStatus = {
  status: string;
  service: string;
};

export type Cluster = { name: string; current: boolean };

export type Diagnosis = {
  root_cause: string;
  explanation: string;
  fix: string;
  kubectl_command: string;
  prevention: string;
  confidence: number;
  evidence: string[];
};

export type InvestigationResponse = {
  status: string;
  investigation_id: string;
  context?: string;
  progress: string[];
  investigation: Record<string, unknown>;
  diagnosis: Diagnosis;
  error?: string;
};
