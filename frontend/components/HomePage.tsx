"use client";

import { useEffect, useState } from "react";

import { useHealth } from "@/hooks/useHealth";
import { useInvestigation } from "@/hooks/useInvestigation";
import { getClusters } from "@/services/api";
import { insforge, isInsforgeConfigured } from "@/lib/insforge";
import type { Cluster, Diagnosis, InvestigationResponse } from "@/types";

const steps = ["Checking Pods", "Reading Logs", "Analyzing Events", "Inspecting Deployments", "Checking Networking", "AI Reasoning", "Root Cause Found"];

export function HomePage() {
  const health = useHealth();
  const investigation = useInvestigation();
  const [user, setUser] = useState<{ id: string; email?: string } | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authMode, setAuthMode] = useState<"signin" | "signup" | "verify">("signin");
  const [authError, setAuthError] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [verificationEmail, setVerificationEmail] = useState("");
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [context, setContext] = useState("");
  const [result, setResult] = useState<InvestigationResponse | null>(null);
  const [history, setHistory] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    const client = insforge;
    if (!client) return;
    void client.auth.getCurrentUser().then(({ data }) => setUser(data?.user ? { id: data.user.id, email: data.user.email } : null));
    void client.database.from("investigations").select().order("created_at", { ascending: false }).limit(10).then(({ data }) => setHistory((data as Array<Record<string, unknown>>) ?? []));
    void client.realtime.connect().then(async () => {
      await client.realtime.subscribe("investigations");
      client.realtime.on("investigation_created", (payload) => {
        const item = payload as Record<string, unknown>;
        setHistory((current) => current.some((entry) => entry.id === item.id) ? current : [item, ...current].slice(0, 10));
      });
    }).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (isInsforgeConfigured && !user) return;
    void getClusters().then((items) => {
      setClusters(items);
      setContext(items.find((item) => item.current)?.name ?? items[0]?.name ?? "");
    }).catch(() => setClusters([]));
  }, [user]);

  async function authenticate(event: React.FormEvent) {
    event.preventDefault();
    if (!insforge) return;
    setAuthError("");
    try {
      if (authMode === "verify") {
        const result = await insforge.auth.verifyEmail({ email: verificationEmail, otp: verificationCode });
        if (result.error || !result.data?.user) {
          setAuthError(result.error?.message ?? "The verification code is invalid or expired.");
          return;
        }
        setUser({ id: result.data.user.id, email: result.data.user.email });
        return;
      }

      const result = authMode === "signin"
        ? await insforge.auth.signInWithPassword({ email, password })
        : await insforge.auth.signUp({ email, password, redirectTo: window.location.origin });

      if (result.error) {
        setAuthError(result.error.message);
        return;
      }

      if (authMode === "signup") {
        if (!result.data?.accessToken) {
          setVerificationEmail(email);
          setVerificationCode("");
          setAuthMode("verify");
          setAuthError("Account created. Enter the 6-digit code sent to your email.");
          return;
        }
      }

      if (!result.data?.user) {
        setAuthError("The authentication service returned an incomplete response. Please try again.");
        return;
      }

      setUser({ id: result.data.user.id, email: result.data.user.email });
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Unable to reach the authentication service.");
    }
  }

  async function runInvestigation() {
    const response = await investigation.mutateAsync({ context });
    setResult(response);
    if (insforge && user) {
      const row = { user_id: user.id, root_cause: response.diagnosis.root_cause, namespace: context, confidence: response.diagnosis.confidence, status: response.status, diagnosis: response.diagnosis };
      const { data } = await insforge.database.from("investigations").insert([row]).select();
      if (data) setHistory((current) => [data[0] as Record<string, unknown>, ...current].slice(0, 10));
    }
  }

  const statusLabel = health.isLoading ? "Checking..." : health.isError ? "Backend Unavailable" : health.data?.status === "healthy" ? "Ready" : "Unknown";

  if (isInsforgeConfigured && !user) {
    return <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-slate-100"><form onSubmit={authenticate} className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-xl"><p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Secure dashboard</p><h1 className="mt-3 text-3xl font-semibold">AI Kubernetes Agent</h1><p className="mt-3 text-slate-400">{authMode === "signin" ? "Sign in to investigate clusters and view history." : authMode === "signup" ? "Create an account to save investigation history." : `Enter the verification code sent to ${verificationEmail}.`}</p>{authMode === "verify" ? <input className="mt-8 w-full rounded-lg border border-slate-700 bg-slate-950 p-3" type="text" inputMode="numeric" pattern="[0-9]{6}" placeholder="6-digit code" value={verificationCode} onChange={(event) => setVerificationCode(event.target.value)} minLength={6} maxLength={6} required /> : <><input className="mt-8 w-full rounded-lg border border-slate-700 bg-slate-950 p-3" type="email" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} required /><input className="mt-3 w-full rounded-lg border border-slate-700 bg-slate-950 p-3" type="password" placeholder="Password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required /></>}<button className="mt-5 w-full rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-slate-950 hover:bg-cyan-400">{authMode === "signin" ? "Sign in" : authMode === "signup" ? "Create account" : "Verify email"}</button>{authMode !== "verify" && <button type="button" onClick={() => { setAuthMode(authMode === "signin" ? "signup" : "signin"); setAuthError(""); }} className="mt-4 w-full text-sm text-cyan-300 hover:text-cyan-200">{authMode === "signin" ? "Need an account? Sign up" : "Already have an account? Sign in"}</button>}{authError && <p className="mt-4 text-sm text-rose-300">{authError}</p>}</form></main>;
  }

  return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100"><div className="mx-auto max-w-6xl"><header className="flex items-center justify-between"><div><p className="text-sm uppercase tracking-[0.2em] text-cyan-400">On-demand troubleshooting</p><h1 className="mt-2 text-4xl font-semibold">AI Kubernetes Agent</h1></div>{isInsforgeConfigured && <button onClick={() => void insforge?.auth.signOut().then(() => setUser(null))} className="text-sm text-slate-400 hover:text-white">Sign out</button>}</header>{!isInsforgeConfigured && <p className="mt-4 text-sm text-amber-300">Local mode: configure InsForge to enable authentication, history, and realtime updates.</p>}<div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_1fr]"><section className="rounded-2xl border border-slate-800 bg-slate-900 p-8"><p className="text-lg text-slate-300">Troubleshoot Kubernetes with AI</p><div className="mt-6 flex flex-col gap-3 sm:flex-row"><select value={context} onChange={(event) => setContext(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm" disabled={!clusters.length}><option value="">Current kubeconfig context</option>{clusters.map((cluster) => <option key={cluster.name} value={cluster.name}>{cluster.name}{cluster.current ? " (current)" : ""}</option>)}</select><button onClick={() => void runInvestigation()} disabled={investigation.isPending || !context} className="rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50">{investigation.isPending ? "Investigating..." : "Investigate Cluster"}</button></div>{investigation.isError && <p className="mt-5 rounded-lg bg-rose-950/50 p-4 text-sm text-rose-200">Unable to investigate the cluster. Verify kubeconfig, cluster access, kubectl permissions, and backend availability.</p>}{investigation.isPending && <div className="mt-8"><p className="font-medium">Investigating Kubernetes Cluster...</p><div className="mt-4 space-y-2">{steps.slice(0, 6).map((step) => <p key={step} className="text-sm text-cyan-300">✓ {step}</p>)}</div></div>}{result && <DiagnosisCard diagnosis={result.diagnosis} />}</section><aside className="rounded-2xl border border-slate-800 bg-slate-900 p-8"><h2 className="text-xl font-semibold">Recent Investigations</h2>{history.length ? <div className="mt-5 space-y-3">{history.map((item, index) => <div key={String(item.id ?? index)} className="rounded-lg border border-slate-800 p-3"><p className="font-medium">{String(item.root_cause ?? "Investigation")}</p><p className="mt-1 text-xs text-slate-400">{String(item.status ?? "unknown")} · confidence {String(item.confidence ?? "—")}%</p></div>)}</div> : <p className="mt-5 text-sm text-slate-400">No investigations saved yet.</p>}</aside></div></div></main>;
}

function DiagnosisCard({ diagnosis }: { diagnosis: Diagnosis }) {
  return <div className="mt-8 rounded-xl border border-cyan-900/70 bg-slate-950 p-6"><div className="flex items-start justify-between gap-4"><h2 className="text-xl font-semibold">Diagnosis</h2><span className="rounded-full bg-cyan-950 px-3 py-1 text-sm text-cyan-300">{diagnosis.confidence}% confidence</span></div><dl className="mt-5 space-y-4 text-sm"><div><dt className="font-semibold text-slate-400">Root Cause</dt><dd className="mt-1 text-lg">{diagnosis.root_cause}</dd></div><div><dt className="font-semibold text-slate-400">Explanation</dt><dd className="mt-1 text-slate-300">{diagnosis.explanation}</dd></div><div><dt className="font-semibold text-slate-400">Suggested Fix</dt><dd className="mt-1 text-slate-300">{diagnosis.fix}</dd></div><div><dt className="font-semibold text-slate-400">kubectl Command</dt><dd className="mt-1 overflow-x-auto rounded bg-slate-900 p-3 font-mono text-xs text-cyan-300">{diagnosis.kubectl_command}</dd></div></dl></div>;
}
