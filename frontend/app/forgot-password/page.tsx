"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { api } from "../lib/api";
import { AuthShell } from "../components/AuthShell";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [devToken, setDevToken] = useState("");
  const [error, setError] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      const result = await api<{ message: string; dev_token: string | null }>(
        "/api/auth/forgot-password",
        { method: "POST", body: JSON.stringify({ email }) },
      );
      setMessage("Si le compte existe, la demande a ete creee.");
      setDevToken(result.dev_token || "");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return <AuthShell eyebrow="Accès sécurisé" title="Mot de passe oublié" intro="Indiquez votre email pour recevoir votre lien de réinitialisation." variant="recovery">{message && <div className="alert alert-success">{message}</div>}{error && <div className="alert alert-error">{error}</div>}<form className="stack-form auth-modern-form" onSubmit={submit}><label>Email<input type="email" autoComplete="email" placeholder="vous@exemple.com" required value={email} onChange={(event) => setEmail(event.target.value)} /></label><button className="button">Continuer</button></form>{devToken && <div className="dev-token"><b>Mode local</b><Link href={`/reset-password?token=${encodeURIComponent(devToken)}`}>Ouvrir la réinitialisation</Link></div>}<p className="auth-switch"><Link href="/login">← Retour à la connexion</Link></p></AuthShell>;
}
