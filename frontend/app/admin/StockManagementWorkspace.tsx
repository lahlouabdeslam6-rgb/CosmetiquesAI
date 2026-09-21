"use client";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../lib/api";
import { StockForecastWorkspace } from "./StockForecastWorkspace";

type Catalog = {
  inci_name?:string|null; common_name?:string|null; categories?:string[]; functions?:string[];
  aliases?:string[]; indicative_usage?:string|null; identity_status?:string; notes?:string[];
  essential_rank?:number; dosage_references?:{source:string;value:string}[]; usage_examples?:string[];
  source_records?:{source:string;page?:number;usage?:string}[];
};
type Material = {
  id:number; name:string; reference:string|null; unit:string; quantity:number; reserved_quantity:number;
  available_quantity:number; minimum_quantity:number; cost_per_unit:number|null; supplier:string|null;
  expires_on:string|null; is_active:boolean; stock_status:"low"|"healthy"|"unrecorded"; catalog:Catalog;
};
type MaterialList={items:Material[];total:number;low_stock:number;unrecorded_stock:number};
type Guide={product_type:string;composition_outline:string};
type CatalogInfo={categories:{id:number;name:string}[];product_guides:Guide[];pdf_product_guides:Guide[];essentials:{rank:number;name:string;reason:string}[]};
type MaterialForm={name:string;reference:string;unit:string;quantity:string;minimum_quantity:string;cost_per_unit:string;supplier:string;expires_on:string};
const empty:MaterialForm={name:"",reference:"",unit:"g",quantity:"",minimum_quantity:"0",cost_per_unit:"",supplier:"",expires_on:""};
const normalize=(value:string)=>value.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
const PAGE_SIZE=15;

function RawMaterialStock(){
  const [data,setData]=useState<MaterialList|null>(null),[info,setInfo]=useState<CatalogInfo|null>(null);
  const [query,setQuery]=useState(""),[category,setCategory]=useState(""),[stock,setStock]=useState(""),[essential,setEssential]=useState(false),[page,setPage]=useState(1);
  const [form,setForm]=useState<MaterialForm>(empty),[editing,setEditing]=useState<Material|null>(null),[formOpen,setFormOpen]=useState(false);
  const [error,setError]=useState(""),[message,setMessage]=useState(""),[saving,setSaving]=useState(false),[expanded,setExpanded]=useState<number|null>(null);
  const editor=useRef<HTMLFormElement>(null);
  const load=async()=>{const result=await api<MaterialList>("/api/admin/raw-materials?include_inactive=true",{},true);setData(result);};
  useEffect(()=>{void Promise.all([load(),api<CatalogInfo>("/api/admin/raw-materials/catalogue",{},true).then(setInfo)]).catch((e:Error)=>setError(e.message));},[]);
  useEffect(()=>{setPage(1);},[query,category,stock,essential]);
  useEffect(()=>{if(formOpen)editor.current?.scrollIntoView({behavior:"smooth",block:"start"});},[formOpen,editing]);
  const filtered=useMemo(()=>{
    const term=normalize(query.trim());
    return (data?.items||[]).filter(item=>{
      const c=item.catalog||{};
      const haystack=[item.name,item.reference,c.inci_name,c.common_name,item.supplier,...(c.categories||[]),...(c.functions||[]),...(c.aliases||[])].filter(Boolean).join(" ");
      return (!term||normalize(haystack).includes(term))&&(!category||(c.categories||[]).includes(category))&&(!essential||!!c.essential_rank)&&(!stock||(stock==="inactive"?!item.is_active:stock==="available"?item.is_active&&item.stock_status!=="unrecorded"&&item.available_quantity>0:item.is_active&&item.stock_status===stock));
    });
  },[data,query,category,stock,essential]);
  const pages=Math.max(1,Math.ceil(filtered.length/PAGE_SIZE)),currentPage=Math.min(page,pages);
  const visible=filtered.slice((currentPage-1)*PAGE_SIZE,currentPage*PAGE_SIZE);
  const edit=(item:Material)=>{setEditing(item);setForm({name:item.name,reference:item.reference||"",unit:item.unit,quantity:item.stock_status==="unrecorded"?"":String(item.quantity),minimum_quantity:String(item.minimum_quantity),cost_per_unit:item.cost_per_unit===null?"":String(item.cost_per_unit),supplier:item.supplier||"",expires_on:item.expires_on||""});setFormOpen(true);setMessage("");};
  async function save(event:FormEvent){
    event.preventDefault();setSaving(true);setError("");setMessage("");
    try{
      const body={...form,quantity:form.quantity===""?undefined:Number(form.quantity),minimum_quantity:Number(form.minimum_quantity),reference:form.reference||null,supplier:form.supplier||null,expires_on:form.expires_on||null,cost_per_unit:form.cost_per_unit===""?null:Number(form.cost_per_unit)};
      await api(editing?`/api/admin/raw-materials/${editing.id}`:"/api/admin/raw-materials",{method:editing?"PATCH":"POST",body:JSON.stringify(body)},true);
      setMessage(editing?"Fiche et stock enregistrés.":"Matière ajoutée.");setFormOpen(false);setEditing(null);setForm(empty);await load();
    }catch(e){setError((e as Error).message);}finally{setSaving(false);}
  }
  async function toggle(item:Material){setSaving(true);setError("");try{await api(`/api/admin/raw-materials/${item.id}`,{method:"PATCH",body:JSON.stringify({is_active:!item.is_active})},true);await load();}catch(e){setError((e as Error).message);}finally{setSaving(false);}}
  return <section className="raw-material-workspace material-catalog-workspace">
    <div className="page-title"><div><p className="kicker">Stock Agent · Laboratoire</p><h2>Matières premières</h2></div><button className="button button-small" onClick={()=>{setEditing(null);setForm(empty);setFormOpen(true);}}>Ajouter une matière</button></div>
    <div className="material-catalog-summary"><span><b>{data?.total||0}</b> références</span><span><b>{info?.categories.length||0}</b> familles</span><span><b>{data?.unrecorded_stock||0}</b> stocks à renseigner</span><span><b>{data?.low_stock||0}</b> stocks bas</span></div>
    <p className="section-intro">Répertoire et PDF regroupés par matière. Recherchez un nom, un INCI, une fonction ou une référence pour consulter et modifier son stock.</p>
    {error&&<div className="alert alert-error">{error}</div>}{message&&<div className="alert alert-success">{message}</div>}
    <div className="panel material-catalog-filters"><label>Rechercher<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ex. argan, Glycerin, hydratant, SLES…"/></label><label>Famille<select value={category} onChange={e=>setCategory(e.target.value)}><option value="">Toutes les familles</option>{info?.categories.map(c=><option key={c.id} value={c.name}>{c.name}</option>)}</select></label><label>Stock<select value={stock} onChange={e=>setStock(e.target.value)}><option value="">Tous les stocks</option><option value="available">Disponible</option><option value="unrecorded">À renseigner</option><option value="low">Stock bas / épuisé</option><option value="inactive">Désactivé</option></select></label><label className="material-essential-filter"><input type="checkbox" checked={essential} onChange={e=>setEssential(e.target.checked)}/>Sélection essentielle du PDF</label></div>
    {formOpen&&<form ref={editor} className="panel material-catalog-editor" onSubmit={save}><div className="page-title"><h3>{editing?editing.name:"Nouvelle matière"}</h3><button type="button" className="text-link" onClick={()=>setFormOpen(false)}>Fermer</button></div><div className="form-grid"><label>Nom de la matière<input required maxLength={180} value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label><label>Référence<input value={form.reference} onChange={e=>setForm({...form,reference:e.target.value})}/></label><label>Quantité réelle en stock<input type="number" step="0.001" min={editing?.reserved_quantity||0} required={!editing} value={form.quantity} placeholder="À renseigner" onChange={e=>setForm({...form,quantity:e.target.value})}/></label><label>Unité<select value={form.unit} onChange={e=>setForm({...form,unit:e.target.value})}>{["g","kg","ml","l","unité"].map(unit=><option key={unit}>{unit}</option>)}</select></label><label>Seuil minimum<input type="number" step="0.001" min="0" value={form.minimum_quantity} onChange={e=>setForm({...form,minimum_quantity:e.target.value})}/></label><label>Coût par unité (MAD)<input type="number" step="0.01" min="0" value={form.cost_per_unit} onChange={e=>setForm({...form,cost_per_unit:e.target.value})}/></label><label>Fournisseur<input value={form.supplier} onChange={e=>setForm({...form,supplier:e.target.value})}/></label><label>Expiration<input type="date" value={form.expires_on} onChange={e=>setForm({...form,expires_on:e.target.value})}/></label></div>{editing&&<p>{editing.reserved_quantity} {editing.unit} réservé(s). Laissez la quantité vide pour conserver le statut « À renseigner ».</p>}<button className="button" disabled={saving}>{saving?"Enregistrement…":"Enregistrer la fiche et le stock"}</button></form>}
    <section className="panel material-catalog-results"><div className="material-results-heading"><h3>{filtered.length} résultat(s)</h3><small>Les dosages des documents restent indicatifs.</small></div>
      {!data?<p>Chargement…</p>:!visible.length?<p className="empty-state">Aucune matière ne correspond à votre recherche.</p>:<div className="material-table-scroll"><table className="material-catalog-table"><thead><tr><th>Matière / INCI</th><th>Famille et fonction</th><th>Stock disponible</th><th>Actions</th></tr></thead><tbody>{visible.map(item=><MaterialRows key={item.id} item={item} expanded={expanded===item.id} onExpand={()=>setExpanded(expanded===item.id?null:item.id)} onEdit={()=>edit(item)} onToggle={()=>toggle(item)} disabled={saving}/>)}</tbody></table></div>}
      <div className="material-pagination"><button className="button button-small button-outline" disabled={currentPage<=1} onClick={()=>setPage(currentPage-1)}>Précédent</button><span>Page {currentPage} / {pages}</span><button className="button button-small button-outline" disabled={currentPage>=pages} onClick={()=>setPage(currentPage+1)}>Suivant</button></div>
    </section>
    <details className="panel material-reference-guide"><summary>Guide du laboratoire · familles de formules et sélection essentielle</summary><p>Ces architectures décrivent les familles de composants. Elles ne sont pas des formules dosées validées.</p><div className="material-guide-grid">{info?.pdf_product_guides.map(g=><section key={g.product_type}><h4>{g.product_type}</h4><p>{g.composition_outline}</p></section>)}</div><details><summary>Les 50 choix de démarrage du PDF</summary><ol>{info?.essentials.map(x=><li key={x.rank}><strong>{x.name}</strong> — {x.reason}</li>)}</ol><small>Certains choix regroupent un système ou plusieurs alternatives.</small></details></details>
  </section>;
}

function MaterialRows({item,expanded,onExpand,onEdit,onToggle,disabled}:{item:Material;expanded:boolean;onExpand:()=>void;onEdit:()=>void;onToggle:()=>void;disabled:boolean}){
  const c=item.catalog||{};
  return <><tr className={!item.is_active?"material-row-inactive":""}><td><strong>{c.common_name||item.name}</strong>{c.common_name&&<span>{item.name}</span>}<small>{item.reference||"Sans référence"}{c.essential_rank?` · Essentiel #${c.essential_rank}`:""}</small>{c.identity_status==="to_specify"&&<small className="material-identity-note">INCI / identité à préciser</small>}</td><td><span>{c.categories?.join(" · ")||"Non classée"}</span><small>{c.functions?.join(" · ")||"Fonction à renseigner"}</small></td><td><strong className="material-stock-number">{item.stock_status==="unrecorded"?"À renseigner":`${item.available_quantity} ${item.unit}`}</strong><small>{item.stock_status!=="unrecorded"?`${item.reserved_quantity} réservé · seuil ${item.minimum_quantity} ${item.unit}`:"Aucune quantité fournie"}</small>{!item.is_active?<small>Désactivée</small>:item.stock_status==="low"&&<small className="material-identity-note">Stock bas / épuisé</small>}</td><td><button className="button button-small" onClick={onEdit}>Modifier stock</button><button className="text-link" aria-expanded={expanded} onClick={onExpand}>{expanded?"Fermer la fiche":"Voir la fiche"}</button></td></tr>{expanded&&<tr className="material-detail-row"><td colSpan={4}><div className="material-detail-grid"><section><h4>Informations de la matière</h4><p><b>INCI :</b> {c.inci_name||"À préciser avec le fournisseur"}</p><p><b>Autres noms :</b> {c.aliases?.join(", ")||"—"}</p><p><b>Fournisseur :</b> {item.supplier||"À renseigner"}</p><p><b>Coût :</b> {item.cost_per_unit===null?"À renseigner":`${item.cost_per_unit} MAD / ${item.unit}`}</p><p><b>Expiration :</b> {item.expires_on||"À renseigner"}</p></section><section><h4>Dosages indicatifs des sources</h4>{c.dosage_references?.length?c.dosage_references.map((d,i)=><p key={i}><strong>{d.value}</strong> <small>{d.source}</small></p>):<p>Dosage non fourni.</p>}<p>{c.usage_examples?.join(" · ")}</p><small>À adapter aux données fournisseur et à la formule. Les plages ne définissent pas le stock.</small></section></div>{c.notes?.map((note,i)=><p className="material-source-note" key={i}>{note}</p>)}<button className="text-link" disabled={disabled} onClick={onToggle}>{item.is_active?"Désactiver cette matière":"Réactiver cette matière"}</button></td></tr>}</>;
}

export function StockManagementWorkspace(){
  const [view,setView]=useState<"products"|"materials">("products");
  useEffect(()=>{if(new URLSearchParams(window.location.search).get("stock")==="materials")setView("materials");},[]);
  return <><div className="stock-kind-tabs" role="tablist" aria-label="Type de stock"><button role="tab" aria-selected={view==="products"} className={view==="products"?"active":""} onClick={()=>setView("products")}>Stock des produits</button><button role="tab" aria-selected={view==="materials"} className={view==="materials"?"active":""} onClick={()=>setView("materials")}>Stock des matières premières</button></div>{view==="products"?<StockForecastWorkspace/>:<RawMaterialStock/>}</>;
}
