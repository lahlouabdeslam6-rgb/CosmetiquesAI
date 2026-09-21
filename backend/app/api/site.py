from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import require_roles
from app.db.sqlite import get_sqlite_session
from app.models.site_page import SitePage
from app.models.user import User
from app.models.operations import AuditLog

router = APIRouter(prefix="/site", tags=["Pages du site"])
PAGE_TITLES = {
    "formule-cle-en-main": "Formule clé en main",
    "formule-sur-mesure": "Formule sur mesure",
    "accompagnement": "Accompagnement",
    "ingredients": "Ingrédients",
    "packaging": "Packaging",
    "branding": "Branding",
    "reglementaire": "Réglementaire",

    "laboratoire": "Notre laboratoire", "a-propos": "À propos",
    "marque-blanche": "Marque blanche", "professionnels": "Professionnels",
    "references": "Références", "temoignages": "Témoignages et expériences",
    "magazine": "Magazine", "franchise": "Franchise", "carte-cadeau": "Carte cadeau", "contact": "Contact",
}

PAGE_DEFAULT_BODIES = {
    "laboratoire": "Notre laboratoire réunit formulation, préparation et contrôle dans un parcours clair. Chaque projet avance à partir d’un besoin défini, de matières premières disponibles et d’une validation avant fabrication.\n\nLes étapes sont suivies depuis la sélection des ingrédients jusqu’aux essais de stabilité, au conditionnement et à la préparation du dossier produit.",
    "formule-cle-en-main": "Choisissez une base de formule déjà structurée puis adaptez-la à votre univers, à votre cible et au positionnement souhaité. Cette voie permet de construire une gamme cohérente avec un développement plus direct.\n\nLe projet est revu avec vous avant validation : texture, parfum, actifs, format, quantité, emballage et présentation de la marque.",
    "formule-sur-mesure": "Le projet commence par votre cahier des charges : type de produit, zone d’application, public, texture, parfum, objectifs et contraintes. Ces informations permettent de préparer une proposition adaptée à votre demande.\n\nLa formule est construite à partir des matières premières disponibles. Le choix des ingrédients, leurs pourcentages, le procédé de fabrication et les tests recommandés sont expliqués avant votre validation.",
    "accompagnement": "Vous avancez avec un interlocuteur clair depuis l’idée jusqu’au produit final. Nous cadrons le besoin, les priorités, le format, le calendrier et les prochaines décisions à prendre.\n\nChaque étape reste lisible : formulation, disponibilité des matières, essais, packaging, identité et préparation de la mise sur le marché.",
    "ingredients": "Les matières premières sont organisées par famille et par fonction : huiles, beurres, hydrolats, actifs, émulsifiants, texturants, conservateurs, parfums et autres composants utiles à la formulation.\n\nPour chaque projet, la sélection tient compte de l’usage recherché, de la compatibilité de la formule et du stock réellement disponible.",
    "packaging": "Le packaging protège le produit et traduit son positionnement. Nous orientons le choix du flacon, du pot, de la pompe, du compte-gouttes, de l’étui et des finitions selon la texture et l’usage.\n\nLa proposition tient compte de la compatibilité avec la formule, de la contenance, de l’expérience d’utilisation et de la cohérence visuelle de la gamme.",
    "branding": "Votre identité donne une direction commune au nom, au logo, aux couleurs, aux étiquettes et aux supports de communication. L’objectif est de créer une marque claire, reconnaissable et adaptée à son public.\n\nNous préparons un univers cohérent pour le site, les fiches produits, les visuels et les campagnes de lancement.",
    "reglementaire": "La préparation réglementaire accompagne le produit avant sa mise sur le marché : informations de formule, éléments d’étiquetage, traçabilité, documents techniques et contrôles attendus.\n\nLes vérifications et tests proposés sont adaptés au type de produit. La validation finale reste réalisée avec les professionnels et organismes compétents pour le marché visé.",
    "a-propos": "MIELMAR relie les richesses naturelles du Maroc à une approche moderne de la beauté, du bien-être et de la création cosmétique. Notre univers réunit produits sélectionnés, accompagnement et solutions de développement sur mesure.\n\nNous privilégions une expérience claire, des choix expliqués et une identité chaleureuse inspirée du miel, de l’argan et du savoir-faire marocain.",
}
class PageWrite(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    body: str = Field(max_length=20000)

def check_slug(slug: str):
    if slug not in PAGE_TITLES:
        raise HTTPException(404, "Page introuvable")

@router.get("/pages/{slug}")
async def read_page(slug: str, session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    check_slug(slug)
    page = await session.get(SitePage, slug)
    body = page.body if page and page.body.strip() else PAGE_DEFAULT_BODIES.get(slug, "")
    return {"slug": slug, "title": page.title if page else PAGE_TITLES[slug], "body": body}

@router.put("/pages/{slug}")
async def update_page(slug: str, data: PageWrite, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    check_slug(slug)
    page = await session.get(SitePage, slug)
    if page is None:
        page = SitePage(slug=slug, title=data.title, body=data.body)
        session.add(page)
    else:
        page.title, page.body = data.title, data.body
    session.add(AuditLog(actor_id=user.id, actor_role=user.role, action="site_page_updated", entity_type="site_page", entity_id=slug, details="Modification manuelle du contenu public"))
    await session.commit()
    return {"slug": slug, "title": page.title, "body": page.body}
