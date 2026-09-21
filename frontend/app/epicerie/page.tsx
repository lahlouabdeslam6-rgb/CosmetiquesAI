"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import { ProductCard } from "../components/ProductCard";
import { SiteFooter } from "../components/SiteFooter";
import { api } from "../lib/api";
import type { ProductList } from "../types";

const PAGE_SIZE = 4;

export default function EpiceriePage() {
  const searchParams = useSearchParams();
  const requestedSearch = searchParams.get("search") || "";
  const [draftSearch, setDraftSearch] = useState(requestedSearch);
  const [search, setSearch] = useState(requestedSearch);
  const [sortBy, setSortBy] = useState("newest");
  const [page, setPage] = useState(1);
  const [products, setProducts] = useState<ProductList | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setDraftSearch(requestedSearch);
    setSearch(requestedSearch);
    setPage(1);
  }, [requestedSearch]);

  const query = useMemo(() => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(PAGE_SIZE),
      category: "Épicerie",
      sort_by: sortBy,
    });
    if (search.trim()) params.set("search", search.trim());
    return params.toString();
  }, [page, search, sortBy]);

  useEffect(() => {
    setProducts(null);
    setError("");
    api<ProductList>(`/api/products?${query}`)
      .then(setProducts)
      .catch((err: Error) => setError(err.message));
  }, [query]);

  const submitSearch = (event: FormEvent) => {
    event.preventDefault();
    setSearch(draftSearch.trim());
    setPage(1);
  };

  const changePage = (nextPage: number) => {
    setPage(nextPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <>
      <main className="epicerie-page shell">
        <header className="epicerie-page-heading">
          <div>
            <p className="kicker">La sélection MIELMAR</p>
            <h1>Épicerie</h1>
          </div>
          <p>Miels, huiles, amlou et produits de bien-être disponibles dans une seule sélection.</p>
        </header>

        <form className="epicerie-toolbar" onSubmit={submitSearch}>
          <label className="epicerie-search">
            <span>Rechercher un produit</span>
            <input
              value={draftSearch}
              onChange={(event) => setDraftSearch(event.target.value)}
              placeholder="Nom du produit ou marque…"
            />
          </label>
          <button className="button" type="submit">Rechercher</button>
          <label className="epicerie-sort">
            <span>Trier par</span>
            <select value={sortBy} onChange={(event) => { setSortBy(event.target.value); setPage(1); }}>
              <option value="newest">Nouveautés</option>
              <option value="name">Nom A-Z</option>
              <option value="price_asc">Prix croissant</option>
              <option value="price_desc">Prix décroissant</option>
              <option value="stock_desc">Stock disponible</option>
            </select>
          </label>
        </form>

        <div className="epicerie-result-line">
          <strong>{products ? `${products.total} produits` : "Chargement…"}</strong>
          {search && <span>Résultats pour « {search} »</span>}
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {!products ? (
          <div className="epicerie-product-grid">
            {Array.from({ length: PAGE_SIZE }).map((_, index) => (
              <div className="skeleton-card" key={index}><Skeleton height={220} borderRadius={8} /><Skeleton count={3} /></div>
            ))}
          </div>
        ) : products.items.length ? (
          <div className="epicerie-product-grid">
            {products.items.map((product) => <ProductCard key={product.product_id} product={product} />)}
          </div>
        ) : (
          <div className="empty-state"><h2>Aucun produit trouvé</h2><p>Essayez un autre mot dans la recherche.</p></div>
        )}

        {products && products.total_pages > 1 && (
          <nav className="pagination epicerie-pagination" aria-label="Pages des produits">
            <button disabled={page === 1} onClick={() => changePage(page - 1)}>Précédent</button>
            <span>Page {page} sur {products.total_pages}</span>
            <button disabled={page === products.total_pages} onClick={() => changePage(page + 1)}>Suivant</button>
          </nav>
        )}
      </main>
      <SiteFooter />
    </>
  );
}
