"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, money } from "../lib/api";

type OverviewReport = {
  generated_at: string;
  current: {
    orders: number;
    delivered_orders: number;
    cancelled_orders: number;
    revenue_mad: number;
  };
  daily_sales: Array<{ date: string; orders: number; revenue_mad: number }>;
  top_products: Array<{
    product_id: number;
    name: string;
    quantity: number;
    revenue_mad: number;
  }>;
};

function StatusBar({ label, value, total, state }: { label: string; value: number; total: number; state: "success" | "pending" | "danger" }) {
  const percentage = total ? Math.round((value / total) * 100) : 0;
  return (
    <div className="overview-status-row">
      <div><span>{label}</span><strong>{value} <small>({percentage} %)</small></strong></div>
      <div className="overview-track"><i className={state} style={{ width: `${percentage}%` }} /></div>
    </div>
  );
}

export function DashboardOverviewCharts() {
  const [report, setReport] = useState<OverviewReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setReport(await api<OverviewReport>("/api/admin/ai/analytics/report?period_days=30&use_ai=false", {}, true));
    } catch (requestError) {
      setError((requestError as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const dailySales = useMemo(() => report?.daily_sales.slice(-14) || [], [report]);
  const maxRevenue = useMemo(() => Math.max(...dailySales.map((item) => item.revenue_mad), 1), [dailySales]);
  const topProducts = useMemo(() => report?.top_products.slice(0, 5) || [], [report]);
  const maxQuantity = useMemo(() => Math.max(...topProducts.map((item) => item.quantity), 1), [topProducts]);

  if (loading && !report) return <div className="page-loading">Chargement des graphiques...</div>;
  if (error && !report) return <div className="alert alert-error">Graphiques indisponibles : {error}</div>;
  if (!report) return null;

  const inProgress = Math.max(report.current.orders - report.current.delivered_orders - report.current.cancelled_orders, 0);

  return (
    <section className="overview-analytics" aria-label="Indicateurs de vente">
      <div className="overview-analytics-heading">
        <div>
          <p className="kicker">Donnees en temps reel</p>
          <h3>Activite des 30 derniers jours</h3>
          <small>Derniere mise a jour : {new Date(report.generated_at).toLocaleString("fr-MA")}</small>
        </div>
        <button type="button" className="button button-small button-outline" onClick={() => void load()} disabled={loading}>
          {loading ? "Actualisation..." : "Actualiser"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="overview-chart-grid">
        <article className="panel overview-sales-chart">
          <header><div><span>Chiffre d'affaires</span><strong>{money(report.current.revenue_mad)}</strong></div><small>14 derniers jours</small></header>
          <div className="overview-bars" role="img" aria-label="Chiffre d'affaires quotidien des quatorze derniers jours">
            {dailySales.map((point) => (
              <div key={point.date} title={`${new Date(`${point.date}T12:00:00`).toLocaleDateString("fr-MA")} : ${money(point.revenue_mad)} · ${point.orders} commande(s)`}>
                <b>{point.revenue_mad > 0 ? Math.round(point.revenue_mad) : ""}</b>
                <i style={{ height: `${point.revenue_mad > 0 ? Math.max(8, (point.revenue_mad / maxRevenue) * 100) : 3}%` }} />
                <small>{new Date(`${point.date}T12:00:00`).toLocaleDateString("fr-MA", { day: "2-digit", month: "2-digit" })}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel overview-status-chart">
          <header><span>Etat des commandes</span><strong>{report.current.orders} au total</strong></header>
          <StatusBar label="Livrees" value={report.current.delivered_orders} total={report.current.orders} state="success" />
          <StatusBar label="En cours" value={inProgress} total={report.current.orders} state="pending" />
          <StatusBar label="Annulees" value={report.current.cancelled_orders} total={report.current.orders} state="danger" />
        </article>

        <article className="panel overview-products-chart">
          <header><span>Produits plus vendus</span><small>Quantites vendues</small></header>
          {topProducts.length ? topProducts.map((product, index) => (
            <Link href={`/products/${product.product_id}`} key={product.product_id}>
              <div><b>{index + 1}</b><strong>{product.name}</strong><span>{product.quantity}</span></div>
              <div className="overview-track"><i className="product" style={{ width: `${Math.max(6, (product.quantity / maxQuantity) * 100)}%` }} /></div>
              <small>{money(product.revenue_mad)}</small>
            </Link>
          )) : <p className="muted">Aucune vente enregistree sur cette periode.</p>}
        </article>
      </div>
    </section>
  );
}
