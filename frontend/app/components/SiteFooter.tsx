import Link from "next/link";
export function SiteFooter() {
  return <footer className="site-footer"><div className="shell footer-grid">
    <div className="footer-brand"><strong>MIELMAR</strong><p>Épicerie · Bien-être · Cosmétique</p><small>Découvrez nos univers et nos services.</small></div>
    <div className="footer-links"><strong>Votre boutique</strong><Link href="/#catalogue">Catalogue</Link><Link href="/promotions">Promotions</Link><Link href="/orders">Mes commandes</Link><Link href="/account">Mon compte</Link></div>
    <div className="footer-links"><strong>Laboratoire</strong><Link href="/informations/formule-cle-en-main">Formule clé en main</Link><Link href="/sur-mesure">Formule sur mesure</Link><Link href="/informations/accompagnement">Accompagnement</Link></div>
    <div className="footer-links"><strong>MIELMAR</strong><Link href="/informations/a-propos">À propos</Link><Link href="/informations/contact">Contact</Link><Link href="/help">Assistance</Link><span>Paiement à la livraison</span></div>
  </div><div className="shell footer-bottom"><span>© 2026 MIELMAR. Tous droits réservés.</span><Link href="/informations/contact">Nous contacter</Link></div></footer>;
}
