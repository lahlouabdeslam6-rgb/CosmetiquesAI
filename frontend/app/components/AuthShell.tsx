import Link from "next/link";
import type { ReactNode } from "react";

type AuthShellProps = {
  eyebrow: string;
  title: string;
  intro?: string;
  variant: "login" | "register" | "recovery";
  children: ReactNode;
};

export function AuthShell({ eyebrow, title, intro, variant, children }: AuthShellProps) {
  return (
    <section className={`auth-modern-page auth-modern-${variant}`}>
      <span className="auth-glow auth-glow-one" aria-hidden="true" />
      <span className="auth-glow auth-glow-two" aria-hidden="true" />
      <span className="auth-honeycomb auth-honeycomb-one" aria-hidden="true" />
      <span className="auth-honeycomb auth-honeycomb-two" aria-hidden="true" />
      <div className="auth-modern-card">
        <Link href="/" className="auth-modern-brand" aria-label="Retour à l’accueil MIELMAR">
          <img src="/mielmar-logo-bold.png" alt="" width="1256" height="1256" />
          <span>MIELMAR</span>
        </Link>
        <div className="auth-modern-heading">
          <p className="kicker">{eyebrow}</p>
          <h1>{title}</h1>
          {intro && <p>{intro}</p>}
        </div>
        {children}
        <div className="auth-trust-line"><span aria-hidden="true">✦</span> Espace client protégé</div>
      </div>
    </section>
  );
}
