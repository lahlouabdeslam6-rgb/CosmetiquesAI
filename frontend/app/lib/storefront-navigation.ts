export const PRODUCT_CATEGORIES = ["Épicerie", "Forme et bien-être", "Visage", "Corps", "Cheveux"];
export const INFORMATION_PAGES: Record<string, string> = {
  laboratoire: "Notre laboratoire", "a-propos": "À propos",
  "marque-blanche": "Marque blanche", professionnels: "Professionnels",
  references: "Références", temoignages: "Témoignages et expériences",
  magazine: "Magazine", franchise: "Franchise", "carte-cadeau": "Carte cadeau",
  contact: "Contact",
  "formule-cle-en-main": "Formule clé en main",
  "formule-sur-mesure": "Formule sur mesure",
  "accompagnement": "Accompagnement",
  "ingredients": "Ingrédients",
  "packaging": "Packaging",
  "branding": "Branding",
  "reglementaire": "Réglementaire",

};
export const categoryHref = (category: string) => category === "Épicerie"
  ? "/epicerie"
  : `/?category=${encodeURIComponent(category)}#catalogue`;
