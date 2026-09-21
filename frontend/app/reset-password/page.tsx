"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "../lib/api";
import { AuthShell } from "../components/AuthShell";

export default function ResetPasswordPage() {
  const params = useSearchParams();
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const token = params.get("token") || "";

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      await api("/api/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, new_password: password }),
      });
      setMessage("Mot de passe modifie. Vous pouvez vous connecter.");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return <AuthShell eyebrow="Dernière étape" title="Nouveau mot de passe" intro="Choisissez un nouveau mot de passe pour récupérer votre espace MIELMAR." variant="recovery">{message && <div className="alert alert-success">{message}</div>}{error && <div className="alert alert-error">{error}</div>}{!message && <form className="stack-form auth-modern-form" onSubmit={submit}><label>Nouveau mot de passe<input type="password" autoComplete="new-password" placeholder="8 caractères minimum" required minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} /></label><button className="button" disabled={!token}>Enregistrer le mot de passe</button></form>}<p className="auth-switch"><Link href="/login">← Retour à la connexion</Link></p></AuthShell>;
}
