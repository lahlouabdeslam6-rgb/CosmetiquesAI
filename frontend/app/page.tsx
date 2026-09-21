"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import { ProductRail } from "./components/ProductRail";
import { ProductCard } from "./components/ProductCard";
import { PackRail } from "./components/PackRail";
import { SiteFooter } from "./components/SiteFooter";
import { api } from "./lib/api";
import { EDITORIAL_PAGE_CONTENT, HOME_SERVICES } from "./lib/editorial-content";
import { useSiteNavigation } from "./components/SiteNavigationProvider";
import type { Pack, PackList, Product, ProductList } from "./types";

type PublishedContent = {
  id: number;
  topic: string;
  title: string;
  subtitle: string | null;
  body: string;
  cta_label: string | null;
  hashtags: string[];
  content_type: string;
};

type ActiveMarketingPromotion = {
  id: number;
  promotion_kind: "single_product" | "pack";
  title: string;
  headline: string;
  message: string;
  cta_label: string;
  products: Product[];
  regular_total: number;
  discount_percentage: number;
  promotional_total: number;
  currency: string;
  starts_at: string | null;
  ends_at: string | null;
};

const PROMOTION_SEARCH_TERMS = [
  "creatine",
  "whey",
  "protein",
  "omega 3",
  "multivitamin",
  "vitamin",
  "magnesium",
  "zinc",
  "bcaa",
  "pre workout",
  "collagen",
];

function normalizeText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function cleanPublishedText(value: string): string {
  return value
    .replace(/<li[^>]*>/gi, "\n- ")
    .replace(/<\/(?:p|div|li|ul|ol|h[1-6])>/gi, "\n")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function promotionCriteria(
  promotion: PublishedContent,
  filters: { brands: string[]; categories: string[]; flavors: string[] },
) {
  const promotionText = normalizeText([
    promotion.topic,
    promotion.title,
    promotion.subtitle || "",
    promotion.body,
    ...(promotion.hashtags || []),
  ].join(" "));
  const category = filters.categories.find((item) =>
    promotionText.includes(normalizeText(item)),
  );
  const brand = filters.brands.find((item) =>
    promotionText.includes(normalizeText(item)),
  );
  const flavor = filters.flavors.find((item) =>
    promotionText.includes(normalizeText(item)),
  );
  const search = PROMOTION_SEARCH_TERMS.find((term) =>
    promotionText.includes(term),
  ) || promotion.topic;
  return { category, brand, flavor, search };
}

export default function Home() {
  const { categories: navigationCategories } = useSiteNavigation();
  const searchParams = useSearchParams();
  const requestedSearch = searchParams.get("search") || "";
  const requestedCategory = searchParams.get("category") || "";
  const [products, setProducts] = useState<ProductList | null>(null);
  const [bestSellers, setBestSellers] = useState<Product[]>([]);
  const [promotionProducts, setPromotionProducts] = useState<Product[]>([]);
  const [filters, setFilters] = useState<{ brands: string[]; categories: string[]; flavors: string[] }>({ brands: [], categories: [], flavors: [] });
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [brand, setBrand] = useState("");
  const [flavor, setFlavor] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [inStock, setInStock] = useState(false);
  const [sortBy, setSortBy] = useState("newest");
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [heroContent, setHeroContent] = useState<PublishedContent | null>(null);
  const [promotion, setPromotion] = useState<PublishedContent | null>(null);
  const [marketingPromotions, setMarketingPromotions] = useState<ActiveMarketingPromotion[]>([]);
  const [packs, setPacks] = useState<Pack[]>([]);
  const singleMarketingPromotions = marketingPromotions.filter(
    (item) => item.promotion_kind === "single_product",
  );
  const marketingPromotion = singleMarketingPromotions[0] || null;
  const query = useMemo(() => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: "24",
    });
    if (search.trim()) params.set("search", search.trim());
    if (category) params.set("category", category);
    if (brand) params.set("brand", brand);
    if (flavor) params.set("flavor", flavor);
    if (minPrice) params.set("min_price", minPrice);
    if (maxPrice) params.set("max_price", maxPrice);
    if (inStock) params.set("in_stock", "true");
    params.set("sort_by", sortBy);
    return params.toString();
  }, [search, category, brand, flavor, minPrice, maxPrice, inStock, sortBy, page]);

  const resetFilters = () => {
    setSearch("");
    setCategory("");
    setBrand("");
    setFlavor("");
    setMinPrice("");
    setMaxPrice("");
    setInStock(false);
    setSortBy("newest");
    setPage(1);
  };

  const applyPromotionFilter = () => {
    if (!promotion) return;
    const criteria = promotionCriteria(promotion, filters);

    resetFilters();
    if (criteria.category) {
      setCategory(criteria.category);
    } else if (criteria.brand) {
      setBrand(criteria.brand);
    } else if (criteria.flavor) {
      setFlavor(criteria.flavor);
    } else {
      setSearch(criteria.search);
    }
    window.requestAnimationFrame(() => {
      document.getElementById("catalogue")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  };

  useEffect(() => {
    api<{ brands: string[]; categories: string[]; flavors: string[] }>("/api/products/filters").then(setFilters).catch(() => undefined);
    api<Product[]>("/api/products/best-sellers?limit=12").then(setBestSellers).catch(() => undefined);
    api<PublishedContent | null>("/api/content/published?content_type=homepage_hero").then(setHeroContent).catch(() => undefined);
    api<PublishedContent | null>("/api/content/published?content_type=promotion").then(setPromotion).catch(() => undefined);
    api<ActiveMarketingPromotion[]>("/api/marketing/promotions/active/all").then(setMarketingPromotions).catch(() => undefined);
    api<PackList>("/api/packs").then((result) => setPacks(result.items)).catch(() => undefined);
  }, []);

  useEffect(() => {
    setSearch(requestedSearch);
    setPage(1);
  }, [requestedSearch]);

  useEffect(() => {
    const match = filters.categories.find(item => normalizeText(item) === normalizeText(requestedCategory));
    setCategory(match || requestedCategory);
    setPage(1);
  }, [requestedCategory, filters.categories]);

  useEffect(() => {
    if (searchParams.get("sort") === "newest") { setSortBy("newest"); setPage(1); }
  }, [searchParams]);

  useEffect(() => {
    const activeSingle = marketingPromotions.find((item) => item.promotion_kind === "single_product");
    if (activeSingle) {
      setPromotionProducts(activeSingle.products);
      return;
    }
    if (!promotion) {
      setPromotionProducts([]);
      return;
    }
    const criteria = promotionCriteria(promotion, filters);
    const params = new URLSearchParams({
      page: "1",
      page_size: "12",
      in_stock: "true",
      sort_by: "stock_desc",
    });
    if (criteria.category) params.set("category", criteria.category);
    else if (criteria.brand) params.set("brand", criteria.brand);
    else if (criteria.flavor) params.set("flavor", criteria.flavor);
    else if (criteria.search) params.set("search", criteria.search);
    api<ProductList>(`/api/products?${params.toString()}`)
      .then((result) => setPromotionProducts(result.items))
      .catch(() => setPromotionProducts([]));
  }, [filters, marketingPromotions, promotion]);

  useEffect(() => {
    setProducts(null);
    setError("");
    const timer = window.setTimeout(() => {
      api<ProductList>(`/api/products?${query}`).then(setProducts).catch((err: Error) => setError(err.message));
    }, 220);
    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    if (!requestedCategory || !products) return;
    const timer = window.setTimeout(() => {
      document.getElementById("catalogue")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 120);
    return () => window.clearTimeout(timer);
  }, [requestedCategory, products, packs.length, marketingPromotions.length]);

  return (
    <>
      <section className="hero">
        <div className="hero-content shell">
          <div className="hero-copy">
            <p className="kicker">Trésors naturels du Maroc</p>
            <h1>{heroContent?.title || <>La Nature au Service <span>de Votre Beauté</span></>}</h1>
            <p>{heroContent?.body || "Du miel pur aux soins naturels, MIELMAR révèle la beauté authentique, inspirée par la richesse de la nature marocaine."}</p>
            <a href="#catalogue" className="button hero-cta">{heroContent?.cta_label || "Découvrir nos produits"}<span aria-hidden="true">→</span></a>
            <nav className="hero-univers" aria-label="Découvrir les univers MIELMAR">
              <a href="/epicerie"><span>01</span>Miel & terroir</a>
              <a href="/?category=Visage#catalogue"><span>02</span>Soins naturels</a>
              <a href="/sur-mesure"><span>03</span>Création sur mesure</a>
            </nav>
          </div>
        </div>
      </section>

      {bestSellers.length > 0 && (
        <div className="storefront-rail shell">
          <ProductRail
            eyebrow="Choix des clients"
            title="Les plus vendus"
            subtitle="Les références les plus commandées sur MIELMAR."
            products={bestSellers}
          />
        </div>
      )}

      {singleMarketingPromotions.slice(1).map((item) => (
        <section className="content-promotion shell" key={item.id}>
          <div>
            <p className="kicker">Offre MIELMAR</p>
            <h2>{item.title}</h2>
            <strong>{item.headline}</strong>
            <p>{item.message}</p>
          </div>
          <a href="#catalogue" className="button">{item.cta_label || "Voir la selection"}</a>
        </section>
      ))}

      {marketingPromotion ? (
        <>
          <section className="content-promotion shell">
            <div>
              <p className="kicker">
                {marketingPromotion.promotion_kind === "pack"
                  ? "Pack MIELMAR"
                  : "Offre MIELMAR"}
              </p>
              <h2>{marketingPromotion.title}</h2>
              <strong>{marketingPromotion.headline}</strong>
              <p>{marketingPromotion.message}</p>
            </div>
            <a href="#offres-marketing" className="button">
              {marketingPromotion.cta_label || "Voir la sélection"}
            </a>
          </section>
          <div
            className="storefront-rail promotion-rail shell"
            id="offres-marketing"
          >
            <ProductRail
              eyebrow="Sélection validée par l'admin"
              title={
                marketingPromotion.promotion_kind === "pack"
                  ? "Pack promotionnel"
                  : "Produit en promotion"
              }
              subtitle="Produits choisis par Marketing Agent selon les ventes, le stock et la demande."
              products={marketingPromotion.products}
            />
          </div>
        </>
      ) : promotion && (
        <>
          <section className="content-promotion shell">
            <div>
              <p className="kicker">Offre MIELMAR</p>
              <h2>{cleanPublishedText(promotion.title)}</h2>
              {promotion.subtitle && <strong>{cleanPublishedText(promotion.subtitle)}</strong>}
              <p>{cleanPublishedText(promotion.body)}</p>
            </div>
            <a href="#catalogue" className="button" onClick={applyPromotionFilter}>
              Voir toute la sélection
            </a>
          </section>
          {promotionProducts.length > 0 && (
            <div className="storefront-rail promotion-rail shell">
              <ProductRail
                eyebrow="Sélection promotionnelle"
                title="Offres & packs"
                subtitle="Les sélections publiées par votre équipe et les agents MIELMAR."
                products={promotionProducts}
              />
            </div>
          )}
        </>
      )}

      <PackRail packs={packs} />

      <section className="catalogue shell" id="catalogue">
        <div className="catalogue-heading">
          <h2>{navigationCategories.find(c => c.value === category)?.label || category || (searchParams.get("sort") === "newest" ? "Nouveautés" : "Tout le catalogue")}</h2>
          <p>
            {products
              ? `${products.total} produits selon tes critères`
              : "Chargement de la sélection..."}
          </p>
        </div>
        <div className="filters-bar">
          <label className="search-field"><span>Rechercher</span><input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Produit ou marque…" /></label>
          <label><span>Catégorie</span><select value={category} onChange={(e) => { setCategory(e.target.value); setPage(1); }}><option value="">Toutes</option>{[...new Set([...navigationCategories.map(c => c.value), ...filters.categories])].map((item) => <option key={item} value={item}>{navigationCategories.find(c => c.value === item)?.label || item}</option>)}</select></label>
          <label><span>Marque</span><select value={brand} onChange={(e) => { setBrand(e.target.value); setPage(1); }}><option value="">Toutes</option>{filters.brands.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label><span>Parfum</span><select value={flavor} onChange={(e) => { setFlavor(e.target.value); setPage(1); }}><option value="">Tous</option>{filters.flavors.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label><span>Prix minimum</span><input type="number" min="0" value={minPrice} onChange={(e) => { setMinPrice(e.target.value); setPage(1); }} placeholder="0 MAD" /></label>
          <label><span>Prix maximum</span><input type="number" min="0" value={maxPrice} onChange={(e) => { setMaxPrice(e.target.value); setPage(1); }} placeholder="500 MAD" /></label>
          <label className="check-filter"><input type="checkbox" checked={inStock} onChange={(e) => { setInStock(e.target.checked); setPage(1); }} /><span>En stock uniquement</span></label>
          <label><span>Trier par</span><select value={sortBy} onChange={(e) => { setSortBy(e.target.value); setPage(1); }}><option value="newest">Nouveautes</option><option value="name">Nom A-Z</option><option value="price_asc">Prix croissant</option><option value="price_desc">Prix decroissant</option><option value="stock_desc">Stock disponible</option></select></label>
          <button className="button button-secondary" type="button" onClick={resetFilters}>Effacer les filtres</button>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        {!products ? (
          <div className="product-rail product-rail-loading">{Array.from({ length: 6 }).map((_, index) => <div className="skeleton-card" key={index}><Skeleton height={230} borderRadius={8} /><Skeleton count={3} /></div>)}</div>
        ) : products.items.length ? (
          <div className="catalogue-product-grid">
            {products.items.map((product) => <ProductCard key={product.product_id} product={product} />)}
          </div>
        ) : (
          <div className="empty-state"><h3>Aucun produit trouvé</h3><p>Essayez une autre recherche.</p></div>
        )}
        {products && products.total_pages > 1 && <div className="pagination"><button disabled={page === 1} onClick={() => setPage((v) => v - 1)}>Précédent</button><span>Page {page} sur {products.total_pages}</span><button disabled={page === products.total_pages} onClick={() => setPage((v) => v + 1)}>Suivant</button></div>}
      </section>

      <section className="home-lab-story shell">
        <div className="home-lab-story-copy">
          <p className="kicker">Création cosmétique</p>
          <h2>Votre formule, construite avec vous.</h2>
          <p>Vous décrivez le produit souhaité dans un cahier des charges simple. Le laboratoire étudie votre besoin, sélectionne les matières disponibles et vous présente une formule complète avant toute validation.</p>
          <div className="home-lab-story-points">
            <span><b>01</b> Besoin cadré</span>
            <span><b>02</b> Formule expliquée</span>
            <span><b>03</b> Décision validée</span>
          </div>
          <a className="button" href="/sur-mesure">Créer mon produit</a>
        </div>
        <a className="home-lab-story-image" href="/informations/formule-sur-mesure" aria-label="Découvrir la formule sur mesure">
          <img src="/editorial/custom-formulation.png" alt="Création d’une formule cosmétique à partir d’un cahier des charges" />
        </a>
      </section>

      <section className="home-services-section shell">
        <div className="home-section-heading">
          <div><p className="kicker">Les services MIELMAR</p><h2>Tout ce qu’il faut pour faire avancer votre projet.</h2></div>
          <p>De la sélection des ingrédients à la préparation du lancement, chaque étape reste claire et suivie.</p>
        </div>
        <div className="home-services-grid">
          {HOME_SERVICES.map((slug, index) => {
            const service = EDITORIAL_PAGE_CONTENT[slug];
            return <a href={`/informations/${slug}`} className="home-service-card" key={slug}>
              <img src={service.image} alt={service.imageAlt} />
              <div><span>0{index + 1}</span><h3>{slug === "reglementaire" ? "Réglementaire" : slug.charAt(0).toUpperCase() + slug.slice(1)}</h3><p>{service.summary}</p><strong>Découvrir →</strong></div>
            </a>;
          })}
        </div>
      </section>

      <section className="home-process-section shell">
        <div className="home-section-heading">
          <div><p className="kicker">Un parcours lisible</p><h2>De votre idée au produit prêt à avancer.</h2></div>
        </div>
        <div className="home-process-grid">
          {[
            ["01", "Votre besoin", "Vous précisez l’usage, le public et le résultat recherché."],
            ["02", "La formulation", "Les matières sont sélectionnées et chaque choix est expliqué."],
            ["03", "La validation", "Vous examinez la proposition avant de confirmer la suite."],
            ["04", "Le lancement", "Packaging, identité et contenus préparent la mise en marché."],
          ].map(([number, title, text]) => <article key={number}><span>{number}</span><h3>{title}</h3><p>{text}</p></article>)}
        </div>
      </section>
      <SiteFooter />
    </>
  );
}
