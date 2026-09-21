"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { useSiteNavigation } from "./SiteNavigationProvider";
import { INFORMATION_PAGES, categoryHref } from "../lib/storefront-navigation";

type Menu = "cosmetics" | "laboratory" | "services";
type StorefrontNavigationProps = {
  variant?: "desktop" | "mobile";
  onNavigate?: () => void;
};
const groups: {id:Menu;label:string;title:string;slugs?:string[]}[] = [
  {id:"cosmetics",label:"Cosmétique",title:"Visage, corps & cheveux."},
  {id:"laboratory",label:"Laboratoire",title:"Votre projet de formulation.",slugs:["formule-cle-en-main","formule-sur-mesure"]},
  {id:"services",label:"Nos services",title:"Les services MIELMAR.",slugs:["accompagnement","ingredients","packaging","branding","reglementaire"]},
];
export function StorefrontNavigation({ variant = "desktop", onNavigate }: StorefrontNavigationProps) {
  const {categories} = useSiteNavigation();
  const [open,setOpen] = useState<Menu|null>(null);
  const wrapper = useRef<HTMLElement>(null);
  const pathname = usePathname();
  useEffect(()=>setOpen(null),[pathname]);
  useEffect(()=>{
    const outside=(event:PointerEvent)=>{if(!wrapper.current?.contains(event.target as Node))setOpen(null);};
    const escape=(event:KeyboardEvent)=>{if(event.key==="Escape"){wrapper.current?.querySelector<HTMLButtonElement>("button[aria-expanded=true]")?.focus();setOpen(null);}};
    document.addEventListener("pointerdown",outside);document.addEventListener("keydown",escape);
    return()=>{document.removeEventListener("pointerdown",outside);document.removeEventListener("keydown",escape);};
  },[]);
  const close=()=>{setOpen(null);onNavigate?.();};
  const labelFor=(value:string)=>categories.find(c=>c.value===value)?.label||value;
  const idPrefix = variant === "mobile" ? "mobile-beauty" : "beauty";
  return <nav ref={wrapper} className={`beauty-navigation beauty-navigation-${variant}`} aria-label="Navigation boutique">
    <div className="beauty-nav-links">
      <Link href="/" onClick={close}>Accueil</Link>
      <Link href={categoryHref("Épicerie")} onClick={close}>{labelFor("Épicerie")}</Link>
      <Link href={categoryHref("Forme et bien-être")} onClick={close}>{labelFor("Forme et bien-être")}</Link>
      {groups.map(group=><div className="beauty-nav-entry" key={group.id}>
        <button type="button" aria-expanded={open===group.id} aria-controls={`${idPrefix}-${group.id}`} onClick={()=>setOpen(open===group.id?null:group.id)}>{group.label} <span aria-hidden="true">⌄</span></button>
        {open===group.id && <div id={`${idPrefix}-${group.id}`} className="beauty-megamenu">
          <div className="beauty-menu-categories">{group.id==="cosmetics"
            ? ["Visage","Corps","Cheveux"].map(value=><Link key={value} href={categoryHref(value)} onClick={close}>{labelFor(value)}</Link>)
            : group.slugs?.map(slug=><Link key={slug} href={slug==="formule-sur-mesure"?"/sur-mesure":`/informations/${slug}`} onClick={close}>{INFORMATION_PAGES[slug]}</Link>)}</div>
        </div>}
      </div>)}
      <Link href="/informations/a-propos" onClick={close}>À propos</Link>
    </div>
  </nav>;
}
