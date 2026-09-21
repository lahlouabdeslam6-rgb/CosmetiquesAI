"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { INFORMATION_PAGES } from "../../lib/storefront-navigation";
import { SiteFooter } from "../../components/SiteFooter";
import { EDITORIAL_PAGE_CONTENT } from "../../lib/editorial-content";

export default function InformationPage() {
  const { slug } = useParams<{slug:string}>();
  const [page,setPage] = useState<{title:string;body:string}|null>(null);
  const [error,setError] = useState("");
  useEffect(() => { let active=true; setPage(null); setError(""); api<{title:string;body:string}>(`/api/site/pages/${encodeURIComponent(slug)}`).then(p => {if(active)setPage(p);}).catch(e=>{if(active)setError(e.message);}); return ()=>{active=false;}; },[slug]);
  const content = EDITORIAL_PAGE_CONTENT[slug];
  const title = page?.title || INFORMATION_PAGES[slug] || "Page introuvable";
  return <>
    <main className="service-editorial-page">
      <section className="service-editorial-hero shell">
        <div className="service-editorial-copy">
          <p className="kicker">{content?.eyebrow || "MIELMAR"}</p>
          <h1>{title}</h1>
          {content?.summary && <p className="service-editorial-summary">{content.summary}</p>}
          {error ? <div role="alert" className="alert alert-error">{error}</div> : !page ? <p>Chargement…</p> : page.body.trim() ? <div className="editorial-body">{page.body.split(/\n\s*\n/).map((p,i)=><p key={i}>{p}</p>)}</div> : <div className="editorial-empty"><h2>Cette page se prépare.</h2><p>Les informations seront disponibles prochainement.</p></div>}
          <div className="service-editorial-actions">
            <Link href={content?.ctaHref || "/#catalogue"} className="button">{content?.ctaLabel || "Découvrir le catalogue"}</Link>
            <Link href="/#catalogue" className="text-link">Voir les produits</Link>
          </div>
        </div>
        {content && <figure className="service-editorial-visual"><img src={content.image} alt={content.imageAlt}/></figure>}
      </section>
      {content && <>
        <section className="service-highlights shell" aria-label="Points essentiels">
          {content.highlights.map((item,index)=><div key={item}><span>0{index+1}</span><strong>{item}</strong></div>)}
        </section>
        <section className="service-steps shell">
          <div className="service-steps-heading"><p className="kicker">Un parcours clair</p><h2>De votre idée à la prochaine étape.</h2></div>
          <div className="service-steps-grid">{content.steps.map((step,index)=><article key={step.title}><span>0{index+1}</span><h3>{step.title}</h3><p>{step.text}</p></article>)}</div>
        </section>
      </>}
    </main>
    <SiteFooter/>
  </>;
}
