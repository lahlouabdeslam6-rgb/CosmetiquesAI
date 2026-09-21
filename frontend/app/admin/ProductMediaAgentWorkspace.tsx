"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { api, assetUrl } from "../lib/api";
import type { Product } from "../types";

type MediaKind = "image" | "video";
type SourceMode = "upload" | "agent";
type MediaDraft = {
  id: number;
  product_id: number;
  product_name: string;
  language: string;
  visual_style: string;
  requested_media: string[];
  instructions: string | null;
  image_prompt: string | null;
  video_prompt: string | null;
  status: string;
  provider: string | null;
  image_url: string | null;
  video_url: string | null;
  error_message: string | null;
  parent_id: number | null;
  request_spec: { image_description?: string; video_description?: string } | null;
  render_plan: { summary: string; limitations: { request_quote: string; reason: string }[] } | null;
};

const statusLabels: Record<string, string> = {
  queued: "Dans la file locale",
  provider_required: "Prêt pour le fournisseur",
  planning: "Lecture des descriptions par l’agent",
  generating: "Création des médias",
  needs_changes: "Consigne à adapter",
  review: "À vérifier",
  approved: "Validé",
  failed: "À relancer",
};

export function ProductMediaAgentWorkspace({ products }: { products: Product[] }) {
  const [productId, setProductId] = useState<number | null>(products[0]?.product_id || null);
  const [language, setLanguage] = useState("fr");
  const [visualStyle, setVisualStyle] = useState("premium naturel");
  const [media, setMedia] = useState<MediaKind[]>(["image", "video"]);
  const [imageDescription, setImageDescription] = useState("");
  const [videoDescription, setVideoDescription] = useState("");
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [sourceMode, setSourceMode] = useState<SourceMode>("agent");
  const [referenceImageUrl, setReferenceImageUrl] = useState<string | null>(null);
  const [draft, setDraft] = useState<MediaDraft | null>(null);
  const [versions, setVersions] = useState<MediaDraft[]>([]);
  const [feedback, setFeedback] = useState("");
  const [revision, setRevision] = useState(false);
  const feedbackRef = useRef<HTMLTextAreaElement>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const product = products.find((item) => item.product_id === productId) || null;
  const hasReferencePhoto = Boolean(referenceFile || referenceImageUrl);
  const busy = versions.some((item) => ["queued", "planning", "generating"].includes(item.status));

  const selectVersion = (item: MediaDraft | null) => {
    setDraft(item);
    setRevision(false);
    setFeedback("");
    setImageDescription(item?.request_spec?.image_description || "");
    setVideoDescription(item?.request_spec?.video_description || "");
    if (item) { setLanguage(item.language); setVisualStyle(item.visual_style); }
    if (item) setMedia(item.requested_media.filter((kind): kind is MediaKind => kind === "image" || kind === "video"));
  };

  useEffect(() => {
    if (revision) {
      feedbackRef.current?.focus();
      feedbackRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [revision]);

  useEffect(() => {
    if (!productId && products.length) setProductId(products[0].product_id);
  }, [productId, products]);

  useEffect(() => {
    if (!productId) return;
    let cancelled = false;
    const currentProduct = products.find((item) => item.product_id === productId);
    const originalImages = currentProduct?.images.filter((value) => !value.includes("/ai/")) || [];
    setReferenceImageUrl(originalImages.at(-1) || null);
    setReferenceFile(null);
    selectVersion(null);
    setVersions([]);
    setMessage("");
    setError("");
    api<{ items: MediaDraft[] }>(
      `/api/admin/ai/product-media?product_id=${productId}`,
      {},
      true,
    )
      .then((result) => { if (!cancelled) { setVersions(result.items); selectVersion(result.items[0] || null); } })
      .catch((reason) => { if (!cancelled) setError((reason as Error).message); });
    return () => { cancelled = true; };
  }, [productId]);

  useEffect(() => {
    if (!productId || !busy) return;
    let cancelled = false;
    const timer = window.setInterval(() => {
      api<{ items: MediaDraft[] }>(
        `/api/admin/ai/product-media?product_id=${productId}`,
        {},
        true,
      )
        .then((result) => {
          if (cancelled) return;
          setVersions(result.items);
          setDraft((current) => result.items.find((item) => item.id === current?.id) || result.items[0] || null);
          if (!result.items.some((item) => ["queued", "planning", "generating"].includes(item.status))) setMessage("");
        })
        .catch(() => undefined);
    }, 5000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [busy, productId]);

  const toggleMedia = (kind: MediaKind) => {
    setMedia((current) =>
      current.includes(kind)
        ? current.length === 1
          ? current
          : current.filter((value) => value !== kind)
        : [...current, kind],
    );
  };

  const prepare = async (event: FormEvent) => {
    event.preventDefault();
    if (!productId || busy) return;
    setLoading(true);
    setError("");
    setMessage("");
    try {
      if (referenceFile) {
        const form = new FormData();
        form.append("files", referenceFile);
        const updated = await api<Product>(
          `/api/products/${productId}/media`,
          { method: "POST", body: form },
          true,
        );
        const uploadedUrl = updated.images.at(-1) || null;
        setReferenceImageUrl(uploadedUrl);
        setReferenceFile(null);
      }
      const result = await api<MediaDraft>(
        "/api/admin/ai/product-media/prepare",
        {
          method: "POST",
          body: JSON.stringify({
            product_id: productId,
            source_mode: sourceMode,
            parent_id: revision && draft ? draft.id : null,
            feedback: revision ? feedback.trim() || null : null,
            language,
            visual_style: visualStyle,
            requested_media: media,
            instructions: null,
            image_description: imageDescription.trim() || null,
            video_description: videoDescription.trim() || null,
          }),
        },
        true,
      );
      setDraft(result);
      setVersions((current) => [result, ...current]);
      setRevision(false);
      setFeedback("");
      setMessage("La génération est lancée. Restez sur cette page: la photo et la vidéo vont apparaître ici.");
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const approve = async () => {
    if (!draft) return;
    setLoading(true);
    setError("");
    try {
      const result = await api<MediaDraft>(
        `/api/admin/ai/product-media/${draft.id}/approve`,
        { method: "POST" },
        true,
      );
      setDraft(result);
      setVersions((current) => current.map((item) => item.id === result.id ? result : item));
      setMessage("Les médias validés ont été ajoutés au produit.");
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="full-field product-media-agent">
      <div className="product-media-heading">
        <div>
          <span>PRODUCT MEDIA AGENT</span>
          <strong>Photos et vidéos de {product?.name || "votre produit"}</strong>
        </div>
        {draft && <small className={`media-agent-status status-${draft.status}`}>{statusLabels[draft.status] || draft.status}</small>}
      </div>

      <form className="product-media-form" onSubmit={prepare}>
        <label className="full-field">
          Produit
          <select disabled={loading} value={productId || ""} onChange={(event) => setProductId(Number(event.target.value))} required>
            {products.map((item) => <option key={item.product_id} value={item.product_id}>{item.name} — {item.brand}</option>)}
          </select>
        </label>
        <label>
          Langue
          <select value={language} onChange={(event) => setLanguage(event.target.value)}>
            <option value="fr">Français</option>
            <option value="ar">Arabe</option>
            <option value="darija">Darija</option>
          </select>
        </label>
        <label>
          Style visuel
          <input value={visualStyle} maxLength={120} onChange={(event) => setVisualStyle(event.target.value)} />
        </label>
        <div className="media-kind-picker">
          <span>Médias demandés</span>
          <button type="button" className={media.includes("image") ? "active" : ""} onClick={() => toggleMedia("image")}>Photo</button>
          <button type="button" className={media.includes("video") ? "active" : ""} onClick={() => toggleMedia("video")}>Vidéo</button>
        </div>
        <div className="full-field media-source-mode">
          <strong>Source du produit</strong>
          <div>
            <button type="button" className={sourceMode === "agent" ? "active" : ""} onClick={() => setSourceMode("agent")}>L’agent crée le packaging</button>
            <button type="button" className={sourceMode === "upload" ? "active" : ""} onClick={() => setSourceMode("upload")}>J’ajoute une photo réelle</button>
          </div>
          <small>Le mode agent crée un packaging MIELMAR original à partir du nom et du type de produit. Toute publication reste soumise à votre validation.</small>
        </div>
        {sourceMode === "upload" && <label className="full-field media-reference-field">
          Photo réelle du produit
          <input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setReferenceFile(event.target.files?.[0] || null)} />
          <small>L’agent conserve le vrai produit de cette photo pour créer le visuel et la vidéo.</small>
          {referenceImageUrl && <img src={assetUrl(referenceImageUrl) || ""} alt={`Photo de référence de ${product?.name || "produit"}`} />}
          {referenceFile && <small>Nouvelle photo sélectionnée: {referenceFile.name}</small>}
        </label>}
        <label className="full-field">
          Description souhaitée pour la photo (optionnelle)
          <textarea rows={3} value={imageDescription} maxLength={1500} onChange={(event) => setImageDescription(event.target.value)} placeholder="Exemple: pot seul, vue de face, fond sombre et lumière douce." />
        </label>
        <label className="full-field">
          Description souhaitée pour la vidéo (optionnelle)
          <textarea rows={3} value={videoDescription} maxLength={1500} onChange={(event) => setVideoDescription(event.target.value)} placeholder="Exemple : même décor que la photo, format vertical, zoom arrière lent pendant 8 secondes." />
        </label>
        {revision && <label className="full-field">
          Corrections de la version #{draft?.id}
          <textarea ref={feedbackRef} value={feedback} rows={3} maxLength={1500} onChange={(event) => setFeedback(event.target.value)} placeholder="Ce qui doit changer : fond plus clair, produit plus grand, lumière à gauche…" />
          <small>Une nouvelle version sera créée à partir de vos corrections. La précédente reste disponible.</small>
        </label>}
        <div className="full-field media-agent-actions">
          <button className="button button-ai" disabled={loading || busy || !productId || (sourceMode === "upload" && !hasReferencePhoto)}>{loading ? "Lancement..." : busy ? "L’agent travaille…" : revision ? "Appliquer mes corrections" : "Générer avec ces descriptions"}</button>
          <small>L’agent lit vos consignes à chaque génération. Publication après votre validation.</small>
        </div>
        {sourceMode === "upload" && !hasReferencePhoto && <p className="full-field media-reference-warning">Ajoutez la photo réelle du produit pour activer ce mode.</p>}
      </form>

      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}

      {versions.length > 0 && <label className="full-field">
        Versions du produit
        <select value={draft?.id || ""} onChange={(event) => selectVersion(versions.find((item) => item.id === Number(event.target.value)) || null)}>
          {versions.map((item) => <option key={item.id} value={item.id}>#{item.id}{item.parent_id ? ` · correction de #${item.parent_id}` : ""} — {statusLabels[item.status] || item.status}</option>)}
        </select>
      </label>}
      {draft && (
        <div className="media-prompts">
          {draft.render_plan && <p><strong>Consignes interprétées par l’agent : </strong>{draft.render_plan.summary}</p>}
          {(draft.image_url || draft.video_url) && <div className="media-result-preview">
            {draft.image_url && <img src={assetUrl(draft.image_url) || ""} alt={`Visuel généré pour ${draft.product_name}`} />}
            {draft.video_url && <video key={draft.video_url} src={assetUrl(draft.video_url) || ""} controls preload="metadata" />}
          </div>}
          <div className="media-review-actions">
            {["review", "approved", "needs_changes", "failed"].includes(draft.status) && <button type="button" className="button button-small" disabled={loading || busy} onClick={() => { setRevision(true); setFeedback(""); }}>Améliorer cette version</button>}
            {draft.status === "review" && <button type="button" className="button button-small" onClick={approve} disabled={loading}>Valider et ajouter au produit</button>}
          </div>
          {["queued", "planning", "generating"].includes(draft.status) && <p>Le modèle travaille sur l’ordinateur. Vous pouvez continuer à utiliser l’administration pendant la génération.</p>}
          {["failed", "needs_changes"].includes(draft.status) && <p role="alert">{draft.error_message || "La génération n’a pas abouti."} Modifiez les consignes puis relancez.</p>}
          <small>La vidéo locale anime la photo en 2D (zoom ou déplacement). Une rotation réelle autour du produit ou une scène animée complexe demande un autre moteur.</small>
        </div>
      )}
      {!products.length && <div className="empty-state"><h3>Ajoutez d’abord un produit au catalogue</h3></div>}
    </section>
  );
}
