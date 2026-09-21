import type { Metadata } from "next";
import { headers } from "next/headers";
import { AuthProvider } from "./components/AuthProvider";
import { AIShoppingAssistant } from "./components/AIShoppingAssistant";
import { Header } from "./components/Header";
import { SiteNavigationProvider } from "./components/SiteNavigationProvider";
import { Toast } from "./components/Toast";
import "./globals.css";
import "./cosmetics-theme.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("host") || "localhost:5173";
  const protocol = requestHeaders.get("x-forwarded-proto") || "http";
  const origin = `${protocol}://${host}`;
  const description =
    "MIELMAR : épicerie, forme et bien-être, cosmétique, laboratoire et services.";
  return {
    title: {
      default: "MIELMAR | Épicerie, bien-être et cosmétique",
      template: "%s | MIELMAR",
    },
    description,
    openGraph: {
      title: "MIELMAR | Épicerie, bien-être et cosmétique",
      description,
    },
    twitter: {
      card: "summary_large_image",
      title: "MIELMAR | Épicerie, bien-être et cosmétique",
      description,
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr">
      <body>
        <AuthProvider><SiteNavigationProvider>
          <Header />
          <main>{children}</main>
          <AIShoppingAssistant />
          <Toast />
        </SiteNavigationProvider></AuthProvider>
      </body>
    </html>
  );
}
