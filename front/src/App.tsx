import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { DashboardPage } from "@/pages/Dashboard";
import { AccountsPage } from "@/pages/Accounts";
import { RegisterPage } from "@/pages/Register";
import { SettingsPage } from "@/pages/Settings";
import { api } from "@/lib/api";
import { LoginPage } from "@/pages/Login";

export default function App() {
  const [jobRunning, setJobRunning] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [auth, setAuth] = useState({ enabled: false, setup_required: true, authenticated: false });

  useEffect(() => {
    const onAuthRequired = (event: Event) => {
      const setupRequired = !!(event as CustomEvent<{ setupRequired?: boolean }>).detail?.setupRequired;
      setAuth({ enabled: !setupRequired, setup_required: setupRequired, authenticated: false });
    };
    window.addEventListener("grok-auth-required", onAuthRequired);
    api.authMe().then((data) => setAuth(data)).catch(() => setAuth({ enabled: true, setup_required: false, authenticated: false })).finally(() => setAuthLoading(false));
    return () => window.removeEventListener("grok-auth-required", onAuthRequired);
  }, []);

  useEffect(() => {
    if (authLoading || (auth.enabled && !auth.authenticated)) return;
    let alive = true;
    const tick = async () => {
      try {
        const data = await api.job();
        if (alive) setJobRunning(!!data.job?.running);
      } catch {
        // ignore
      }
    };
    tick();
    const timer = window.setInterval(tick, 3000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [authLoading, auth.enabled, auth.authenticated]);

  if (authLoading) {
    return <div className="flex min-h-[100dvh] items-center justify-center text-muted-foreground">加载中…</div>;
  }
  if (auth.setup_required || (auth.enabled && !auth.authenticated)) {
    return <LoginPage setupRequired={!!auth.setup_required} onLoggedIn={() => setAuth({ enabled: true, setup_required: false, authenticated: true })} />;
  }

  const logout = async () => {
    try {
      await api.logout();
    } finally {
      setAuth({ enabled: true, setup_required: false, authenticated: false });
      setJobRunning(false);
    }
  };

  return (
    <Routes>
      <Route element={<Layout jobRunning={jobRunning} onLogout={auth.enabled ? logout : undefined} />}>
        <Route index element={<DashboardPage />} />
        <Route path="accounts" element={<AccountsPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
