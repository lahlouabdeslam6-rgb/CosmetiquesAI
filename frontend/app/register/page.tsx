"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "../components/AuthProvider";
import { AuthShell } from "../components/AuthShell";

export default function RegisterPage() {
  const router = useRouter(); const { register, login } = useAuth();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" }); const [error, setError] = useState(""); const [submitting, setSubmitting] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); setSubmitting(true); setError(""); try { await register(form); await login(form.email, form.password); router.push("/"); } catch (err) { setError((err as Error).message); } finally { setSubmitting(false); } };
  return <AuthShell eyebrow="Bienvenue chez MIELMAR" title="Créer un compte" intro="Créez votre espace en quelques secondes pour suivre vos achats et vos projets." variant="register">{error && <div className="alert alert-error">{error}</div>}<form onSubmit={submit} className="stack-form auth-modern-form"><label>Nom complet<input autoComplete="name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="Votre nom" required minLength={2} /></label><label>Email<input type="email" autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="vous@exemple.com" required /></label><label>Mot de passe<input type="password" autoComplete="new-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="8 caractères minimum" required minLength={8} /></label><button className="button" disabled={submitting}>{submitting ? "Création…" : "Créer mon compte"}</button></form><p className="auth-switch">Déjà inscrit ? <Link href="/login">Se connecter</Link></p></AuthShell>;
}
