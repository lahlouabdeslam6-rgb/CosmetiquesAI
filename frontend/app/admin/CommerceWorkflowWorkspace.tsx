"use client";

import { useEffect, useState } from "react";
import { api, money } from "../lib/api";

type WorkflowStep = {
  key: string;
  agent: string;
  label: string;
  description: string;
};

type WorkflowOrder = {
  order_id: number;
  customer_name: string;
  phone: string;
  order_status: string;
  payment_status: string;
  active_agent: string;
  next_action: string;
  confirmation_status: string;
  delivery_status: string;
  feedback_status: string;
  messages: {direction:string;event_type:string;channel:string;body:string;status:string;scheduled_for:string|null;processed_at:string|null}[];
  feedback: {rating:number;comment:string|null;source:string;created_at:string}|null;
  total: number;
  currency: string;
  created_at: string;
};

type WorkflowReport = {
  generated_at: string;
  steps: WorkflowStep[];
  summary: {
    active_orders: number;
    awaiting_confirmation: number;
    in_preparation: number;
    in_delivery: number;
    feedback_scheduled: number;
    feedback_received: number;
    pending_messages: number;
  };
  orders: WorkflowOrder[];
};

const statusLabel: Record<string, string> = {
  pending: "En attente",
  confirmed: "Confirmée",
  preparing: "En préparation",
  shipped: "En livraison",
  delivered: "Livrée",
  delivery_failed: "Livraison à reprendre",
  cancelled: "Annulée",
  completed: "Terminé",
  sent: "Envoyé",
  failed: "Échec",
  not_started: "Pas commencé",
  not_queued: "Non programmé",
  scheduled: "Programmé",
  received: "Reçu",
  not_due: "Pas encore",
};

export function CommerceWorkflowWorkspace() {
  const [report, setReport] = useState<WorkflowReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setReport(await api<WorkflowReport>("/api/admin/ai/workflow", {}, true));
    } catch (requestError) {
      setError((requestError as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  return (
    <section className="commerce-workflow-workspace">
      <div className="page-title">
        <div>
          <p className="kicker">Agents connectés</p>
          <h2>Parcours AI-Commerce</h2>
        </div>
        <button className="button button-small" onClick={() => void load()} disabled={loading}>
          {loading ? "Actualisation…" : "Actualiser"}
        </button>
      </div>
      <p className="section-intro">
        Chaque agent transmet automatiquement son résultat à l&apos;étape suivante. Les messages externes restent dans la file d&apos;envoi jusqu&apos;à leur traitement par les canaux MIELMAR.
      </p>
      {error && <div className="alert alert-error">{error}</div>}

      {report && (
        <>
          <div className="workflow-step-grid" aria-label="Parcours des agents IA">
            {report.steps.map((step, index) => (
              <article className="workflow-step" key={step.key}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <small>{step.label}</small>
                <strong>{step.agent}</strong>
                <p>{step.description}</p>
              </article>
            ))}
          </div>

          <div className="workflow-metrics">
            <article><small>Commandes actives</small><strong>{report.summary.active_orders}</strong></article>
            <article><small>À confirmer</small><strong>{report.summary.awaiting_confirmation}</strong></article>
            <article><small>En préparation</small><strong>{report.summary.in_preparation}</strong></article>
            <article><small>En livraison</small><strong>{report.summary.in_delivery}</strong></article>
            <article><small>Feedback programmé</small><strong>{report.summary.feedback_scheduled}</strong></article>
            <article><small>Feedback reçu</small><strong>{report.summary.feedback_received}</strong></article>
            <article><small>Messages à envoyer</small><strong>{report.summary.pending_messages}</strong></article>
          </div>

          <div className="page-title workflow-orders-title">
            <div><p className="kicker">Suivi en direct</p><h2>Passage entre les agents</h2></div>
            <span>{report.orders.length} commande(s)</span>
          </div>
          {report.orders.length ? (
            <div className="workflow-order-list">
              {report.orders.map((order) => (
                <article key={order.order_id}>
                  <div className="workflow-order-head">
                    <div>
                      <small>Commande #{order.order_id}</small>
                      <strong>{order.customer_name}</strong>
                      <span>{order.phone}</span>
                    </div>
                    <div>
                      <b>{statusLabel[order.order_status] || order.order_status}</b>
                      <strong>{money(order.total, order.currency)}</strong>
                    </div>
                  </div>
                  <div className="workflow-order-agent">
                    <small>Agent actif</small>
                    <strong>{order.active_agent}</strong>
                    <p>{order.next_action}</p>
                  </div>
                  <div className="workflow-order-states">
                    <span><small>Confirmation</small><b>{statusLabel[order.confirmation_status] || order.confirmation_status}</b></span>
                    <span><small>Livraison</small><b>{statusLabel[order.delivery_status] || order.delivery_status}</b></span>
                    <span><small>Feedback</small><b>{statusLabel[order.feedback_status] || order.feedback_status}</b></span>
                  </div>
                  <details className="workflow-conversation">
                    <summary>Chof messages WhatsApp w feedback</summary>
                    <div className="workflow-message-list">
                      {order.messages.length ? order.messages.map((item,index)=><article className={`workflow-message ${item.direction}`} key={`${item.event_type}-${index}`}>
                        <small>{item.direction==="client_to_agent"?"Client → Confirmation Agent":`${item.channel.toUpperCase()} Agent → Client`} · {statusLabel[item.status]||item.status}</small>
                        <p>{item.body}</p>
                        <span>{item.processed_at?new Date(item.processed_at).toLocaleString("fr-MA"):item.scheduled_for?`Programmé: ${new Date(item.scheduled_for).toLocaleString("fr-MA")}`:""}</span>
                      </article>):<p className="muted">Mazal ma kayn 7ta message lhad commande.</p>}
                    </div>
                    <div className="workflow-feedback-detail">
                      <strong>Feedback client</strong>
                      {order.feedback?<><b>{"★".repeat(order.feedback.rating)}{"\u2606".repeat(5-order.feedback.rating)} · {order.feedback.rating}/5</b><p>{order.feedback.comment||"Bla commentaire."}</p><small>Source: {order.feedback.source}</small></>:<p>Mazal ma wsel 7ta feedback.</p>}
                    </div>
                  </details>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <h3>Aucune commande dans le parcours</h3>
              <p>La première commande déclenchera automatiquement Confirmation Agent.</p>
            </div>
          )}
        </>
      )}
    </section>
  );
}
