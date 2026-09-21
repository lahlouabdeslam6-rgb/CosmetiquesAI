"use client";
import { useEffect,useState } from "react";
import Link from "next/link";
import { api } from "../lib/api";
import { ProductRail } from "../components/ProductRail";
import { PackRail } from "../components/PackRail";
import { SiteFooter } from "../components/SiteFooter";
import type {Product,PackList} from "../types";
export default function Promotions(){
 const [offers,setOffers]=useState<{id:number;title:string;message:string;products:Product[]}[]|null>(null),[packs,setPacks]=useState<PackList|null>(null),[error,setError]=useState("");
 useEffect(()=>{let active=true;Promise.all([api<{id:number;title:string;message:string;products:Product[]}[]>("/api/marketing/promotions/active/all"),api<PackList>("/api/packs")]).then(([o,p])=>{if(active){setOffers(o);setPacks(p);}}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[]);
 return <><section className="page-section shell"><p className="kicker">La sélection MIELMAR</p><h1>Promotions &amp; idées cadeaux</h1>{error?<div role="alert" className="alert alert-error">{error}</div>:!offers||!packs?<p>Chargement…</p>:<>{offers.map(o=><ProductRail key={o.id} eyebrow="Offre en cours" title={o.title} subtitle={o.message} products={o.products}/>)}<PackRail packs={packs.items}/>{!offers.length&&!packs.items.length&&<div className="empty-state"><h2>Aucune offre pour le moment</h2><p>Les offres validées apparaîtront ici.</p><Link href="/#catalogue" className="button button-outline">Voir le catalogue</Link></div>}</>}</section><SiteFooter/></>;
}
