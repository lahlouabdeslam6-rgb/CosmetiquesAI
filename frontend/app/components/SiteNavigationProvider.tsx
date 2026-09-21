"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../lib/api";
import { PRODUCT_CATEGORIES } from "../lib/storefront-navigation";
export type CategoryEntry = { label:string; value:string };
type NavigationContextValue = { categories:CategoryEntry[]; ready:boolean; error:string; update:(categories:CategoryEntry[])=>void };
const defaults=PRODUCT_CATEGORIES.map(value=>({label:value,value}));
const NavigationContext=createContext<NavigationContextValue>({categories:defaults,ready:false,error:"",update:()=>{}});
export function SiteNavigationProvider({children}:{children:ReactNode}){
 const [categories,setCategories]=useState(defaults),[ready,setReady]=useState(false),[error,setError]=useState("");
 useEffect(()=>{let active=true;api<{categories:CategoryEntry[]}>("/api/site/navigation").then(n=>{if(active){setCategories(n.categories);setReady(true);}}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[]);
 return <NavigationContext.Provider value={{categories,ready,error,update:setCategories}}>{children}</NavigationContext.Provider>;
}
export const useSiteNavigation=()=>useContext(NavigationContext);
