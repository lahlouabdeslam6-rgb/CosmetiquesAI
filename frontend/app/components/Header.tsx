"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "./AuthProvider";
import { CommerceCartSummary } from "./CommerceCartSummary";
import { NotificationBell } from "./NotificationBell";
import { StorefrontNavigation } from "./StorefrontNavigation";
import { api } from "../lib/api";

type HeaderOffer = {
  id: number | string;
  title: string;
  headline?: string | null;
  message?: string | null;
};

function readableOffer(value: string | null | undefined) {
  return (value || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading, logout } = useAuth();
  const [catalogSearch, setCatalogSearch] = useState("");
  const [isCompact, setIsCompact] = useState(false);
  const [offer, setOffer] = useState<HeaderOffer | null>(null);
  const [offerVisible, setOfferVisible] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isShopper = !user || user.role === "customer";
  const links = !user
    ? [["/", "Produits"]]
    : user.role === "support"
      ? [["/", "Produits"], ["/support", "Espace support"], ["/account", "Compte"]]
      : user.role === "admin"
        ? [["/", "Produits"], ["/admin", "Administration"], ["/account", "Compte"]]
        : [["/", "Produits"], ["/orders", "Mes commandes"], ["/help", "Aide"], ["/account", "Compte"]];

  useEffect(() => {
    if (pathname === "/" || pathname === "/epicerie") {
      setCatalogSearch(searchParams.get("search") || "");
    }
  }, [pathname, searchParams]);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!mobileMenuOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileMenuOpen(false);
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [mobileMenuOpen]);

  useEffect(() => {
    if (!isShopper) return;
    const update = () => setIsCompact(window.scrollY > 135);
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, [isShopper]);

  useEffect(() => {
    if (!isShopper) return;
    void Promise.allSettled([
      api<Array<{ id: number; title: string; headline: string; message: string }>>("/api/marketing/promotions/active/all"),
      api<{ id: number; title: string; subtitle?: string | null; body?: string | null } | null>("/api/content/published?content_type=promotion"),
    ]).then(([campaignsResult, contentResult]) => {
      const campaign = campaignsResult.status === "fulfilled" ? campaignsResult.value[0] : null;
      const content = contentResult.status === "fulfilled" ? contentResult.value : null;
      const nextOffer: HeaderOffer | null = campaign
        ? { id: `campaign-${campaign.id}`, title: campaign.title, headline: campaign.headline, message: campaign.message }
        : content
          ? { id: `content-${content.id}`, title: content.title, headline: content.subtitle, message: content.body }
          : null;
      setOffer(nextOffer);
      setOfferVisible(Boolean(nextOffer && sessionStorage.getItem(`mielmar-offer-${nextOffer.id}`) !== "dismissed"));
    });
  }, [isShopper]);

  const dismissOffer = () => {
    if (offer) sessionStorage.setItem(`mielmar-offer-${offer.id}`, "dismissed");
    setOfferVisible(false);
  };

  const searchCatalogue = (event: FormEvent) => {
    event.preventDefault();
    const term = catalogSearch.trim();
    if (pathname === "/epicerie") {
      router.push(term ? `/epicerie?search=${encodeURIComponent(term)}` : "/epicerie");
      return;
    }
    router.push(term ? `/?search=${encodeURIComponent(term)}#catalogue` : "/#catalogue");
  };

  const navigation = (
    <nav className="main-nav" aria-label="Navigation principale">
      {links.map(([href, label]) => (
        <Link key={href} href={href} className={pathname === href ? "active" : ""} onClick={() => setMobileMenuOpen(false)}>
          {label}
        </Link>
      ))}
    </nav>
  );

  return (
    <header className={`site-header ${isShopper ? "storefront-header" : ""} ${isShopper && isCompact ? "is-compact" : ""}`}>
      {isShopper && offerVisible && offer && (
        <div className="commerce-strip" role="status">
          <div className="commerce-offer-inner">
            <span>Offre MIELMAR</span>
            <strong>{readableOffer(offer.headline) || readableOffer(offer.title)}</strong>
            {offer.message && <small>{readableOffer(offer.message)}</small>}
            <Link href="/#offres-marketing">Découvrir</Link>
            <button type="button" onClick={dismissOffer} aria-label="Fermer l’offre">×</button>
          </div>
        </div>
      )}
      <div className={`header-inner ${isShopper ? "commerce-header-inner" : ""}`}>
        <Link href="/" className="brand" aria-label="MIELMAR accueil">
          <span className="brand-logo"><img src="/mielmar-logo-bold.png" alt="" width="1256" height="1256" /></span>
          <span>MIELMAR <strong>Épicerie · Bien-être · Cosmétique</strong></span>
        </Link>
        <button
          type="button"
          className="mobile-menu-toggle"
          aria-label="Ouvrir le menu"
          aria-expanded={mobileMenuOpen}
          aria-controls="mobile-storefront-menu"
          onClick={() => setMobileMenuOpen(true)}
        >
          <span /><span /><span />
        </button>
        {isShopper ? (
          <form className="commerce-search" role="search" onSubmit={searchCatalogue}>
            <input
              value={catalogSearch}
              onChange={(event) => setCatalogSearch(event.target.value)}
              placeholder="Rechercher un produit ou une marque..."
              aria-label="Rechercher un produit"
            />
            <button type="submit" aria-label="Lancer la recherche">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle cx="11" cy="11" r="6.5" />
                <path d="m16 16 4 4" />
              </svg>
            </button>
          </form>
        ) : navigation}
        <div className={`header-actions ${!user ? "guest-actions" : ""}`}>
          {isShopper && <CommerceCartSummary user={user} />}
          {!loading && user ? (
            <>
              {user.role === "customer" && (
                <Link href="/orders" className="button button-small button-outline header-orders-link">
                  Mes commandes
                </Link>
              )}
              <NotificationBell />
              <span className="user-chip">{user.full_name || user.email.split("@")[0]}</span>
              <button className="link-button" onClick={() => { logout(); router.push("/"); }}>
                Sortir
              </button>
            </>
          ) : (
            <>
              <Link href="/register" className="button button-small button-outline">Créer un compte</Link>
              <Link href="/login" className="button button-small">Se connecter</Link>
            </>
          )}
        </div>
      </div>
      {isShopper && (
        <div className="commerce-nav-row">
          <div className="commerce-nav-inner">
            <StorefrontNavigation />
            
          </div>
        </div>
      )}
      <>
          <button
            type="button"
            className={`mobile-menu-backdrop ${mobileMenuOpen ? "is-open" : ""}`}
            aria-label="Fermer le menu"
            tabIndex={mobileMenuOpen ? 0 : -1}
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside id="mobile-storefront-menu" className={`mobile-storefront-menu ${mobileMenuOpen ? "is-open" : ""}`} aria-hidden={!mobileMenuOpen}>
            <div className="mobile-menu-heading">
              <Link href="/" className="brand" onClick={() => setMobileMenuOpen(false)}>
                <span className="brand-logo"><img src="/mielmar-logo-bold.png" alt="" width="1256" height="1256" /></span>
                <span>MIELMAR</span>
              </Link>
              <button type="button" className="mobile-menu-close" aria-label="Fermer le menu" onClick={() => setMobileMenuOpen(false)}>×</button>
            </div>
            {isShopper ? (
              <StorefrontNavigation variant="mobile" onNavigate={() => setMobileMenuOpen(false)} />
            ) : (
              <div className="mobile-account-navigation">{navigation}</div>
            )}
            <div className="mobile-menu-account">
              {!loading && user ? (
                <>
                  {user.role === "customer" && (
                    <Link href="/orders" className="button" onClick={() => setMobileMenuOpen(false)}>Mes commandes</Link>
                  )}
                  <Link href="/account" className="button button-outline" onClick={() => setMobileMenuOpen(false)}>Mon compte</Link>
                  <button className="button" onClick={() => { setMobileMenuOpen(false); logout(); router.push("/"); }}>Sortir</button>
                </>
              ) : (
                <>
                  <Link href="/login" className="button" onClick={() => setMobileMenuOpen(false)}>Se connecter</Link>
                  <Link href="/register" className="button button-outline" onClick={() => setMobileMenuOpen(false)}>Créer un compte</Link>
                </>
              )}
            </div>
          </aside>
      </>
    </header>
  );
}
