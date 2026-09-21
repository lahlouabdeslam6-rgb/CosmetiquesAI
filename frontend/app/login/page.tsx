"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "../components/AuthProvider";
import { AuthShell } from "../components/AuthShell";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const user = await login(email, password);
      router.push(
        user.role === "admin"
          ? "/admin"
          : user.role === "support"
            ? "/support"
            : searchParams.get("returnTo") || "/",
      );
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthShell eyebrow="Heureux de vous revoir" title="Connexion" intro="Retrouvez vos commandes et votre sélection MIELMAR." variant="login">
        {searchParams.get("expired") && <div className="alert alert-error">Votre session a expiré. Connectez-vous à nouveau.</div>}
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={submit} className="stack-form login-form">
          <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required /></label>
          <label>Mot de passe<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
          <div className="form-helper"><Link href="/forgot-password">Mot de passe oublié ?</Link></div>
          <button className="button" disabled={submitting}>{submitting ? "Connexion…" : "Se connecter"}</button>
        </form>
        <p className="auth-switch">Pas encore de compte ? <Link href="/register">Créer un compte</Link></p>
    </AuthShell>
  );
}
