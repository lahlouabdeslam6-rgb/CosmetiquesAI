"use client";
import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "../lib/api";
import { SiteFooter } from "../components/SiteFooter";
import { Protected } from "../components/Protected";
import { useAuth } from "../components/AuthProvider";

type QuestionType="text"|"textarea"|"select"|"multiselect"|"number"|"date";
type Question={id:string;label:string;section:string;type?:QuestionType;required?:boolean;options?:string[]};
type Answer=string|number|string[];
type Form={project_name:string;phone:string;product_type:string;needs:string;answers:Record<string,Answer>};
const empty:Form={project_name:"",phone:"",product_type:"",needs:"",answers:{}};

function Questionnaire(){
  const {user}=useAuth();
  const [questions,setQuestions]=useState<Question[]>([]),[productTypes,setProductTypes]=useState<string[]>([]),[form,setForm]=useState<Form>(empty),[reference,setReference]=useState(""),[error,setError]=useState(""),[saving,setSaving]=useState(false);
  useEffect(()=>{api<{questions:Question[];product_types:string[]}>('/api/cosmetic-requests/config').then(data=>{setQuestions(data.questions);setProductTypes(data.product_types);}).catch((e:Error)=>setError(e.message));},[]);
  const sections=useMemo(()=>Array.from(new Set(questions.map(q=>q.section))),[questions]);
  const setAnswer=(id:string,value:Answer)=>setForm(current=>({...current,answers:{...current.answers,[id]:value}}));
  const toggle=(id:string,option:string)=>{const current=Array.isArray(form.answers[id])?form.answers[id] as string[]:[];setAnswer(id,current.includes(option)?current.filter(x=>x!==option):[...current,option]);};
  async function submit(event:FormEvent){event.preventDefault();setError("");const missing=questions.find(q=>q.required&&(Array.isArray(form.answers[q.id])?!(form.answers[q.id] as string[]).length:!form.answers[q.id]));if(missing){setError(`Complétez le champ obligatoire : ${missing.label}`);return;}setSaving(true);try{const result=await api<{reference:string}>('/api/cosmetic-requests',{method:'POST',body:JSON.stringify(form)},true);setReference(result.reference);setForm(empty);}catch(e){setError((e as Error).message);}finally{setSaving(false);}}
  const field=(question:Question)=>{
    const value=form.answers[question.id]??"";
    if(question.type==='textarea')return <textarea rows={4} required={question.required} value={String(value)} onChange={e=>setAnswer(question.id,e.target.value)}/>;
    if(question.type==='select')return <select required={question.required} value={String(value)} onChange={e=>setAnswer(question.id,e.target.value)}><option value="">Choisir</option>{question.options?.map(o=><option key={o}>{o}</option>)}</select>;
    if(question.type==='multiselect')return <div className="question-options">{question.options?.map(o=><label key={o}><input type="checkbox" checked={Array.isArray(value)&&value.includes(o)} onChange={()=>toggle(question.id,o)}/><span>{o}</span></label>)}</div>;
    return <input type={question.type==='number'?'number':question.type==='date'?'date':'text'} required={question.required} value={String(value)} onChange={e=>setAnswer(question.id,question.type==='number'&&e.target.value!==''?Number(e.target.value):e.target.value)}/>;
  };
  return <><section className="page-section shell custom-cosmetic-page"><div className="custom-cosmetic-intro"><p className="kicker">Formule sur mesure</p><h1>Votre cahier des charges cosmétique</h1><p>Connecté comme <strong>{user?.full_name||user?.email}</strong>. Vos coordonnées et vos réponses seront transmises ensemble à l’administration, sans modification.</p></div>
      {reference?<div className="panel request-success"><p className="kicker">Cahier des charges envoyé</p><h2>Votre référence : {reference}</h2><p>Le Laboratory Agent analysera vos réponses pour créer une proposition unique avec les matières disponibles. L’administrateur contrôlera et validera la formule finale.</p><button className="button" onClick={()=>setReference("")}>Nouvelle demande</button></div>:<form className="panel custom-cosmetic-form" onSubmit={submit}>{error&&<div className="alert alert-error">{error}</div>}<section className="questionnaire-section"><h2>Informations du projet</h2><div className="form-grid"><label>Nom du projet<input value={form.project_name} onChange={e=>setForm({...form,project_name:e.target.value})}/></label><label>Téléphone<input required minLength={6} value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})}/></label><label>Produit souhaité / idée à créer<input required list="product-idea-suggestions" placeholder="Ex. soin visage apaisant personnalisé" value={form.product_type} onChange={e=>setForm({...form,product_type:e.target.value})}/><datalist id="product-idea-suggestions">{productTypes.map(x=><option key={x} value={x}/>)}</datalist></label><label className="full-field">Besoin et résultat attendu<textarea required rows={4} value={form.needs} onChange={e=>setForm({...form,needs:e.target.value})}/></label></div></section>
      {sections.map(section=><section className="questionnaire-section" key={section}><h2>{section}</h2><div className="form-grid">{questions.filter(q=>q.section===section).map(question=><div className={question.type==='textarea'||question.type==='multiselect'?'full-field question-field':'question-field'} key={question.id}><label>{question.label}{question.required&&<b> *</b>}</label>{field(question)}</div>)}</div></section>)}
      <div className="questionnaire-submit"><p>En envoyant ce formulaire, vous confirmez que les informations sont exactes. Une validation laboratoire reste obligatoire.</p><button className="button" disabled={saving}>{saving?'Envoi…':'Envoyer mon cahier des charges'}</button></div></form>}
    <Link className="text-link" href="/">← Retour à la boutique</Link></section><SiteFooter/></>;
}

export default function CustomCosmeticPage(){return <Protected roles={['customer']}><Questionnaire/></Protected>;}
