"""Default client brief, transcribed from MIELMAR's cosmetic specification document."""

PRODUCT_TYPES = [
    "Crème", "Lotion", "Sérum", "Gel / Gel-crème", "Huile", "Baume",
    "Mousse", "Shampooing", "Savon", "Autre",
]


def q(identifier: str, label: str, section: str, kind: str = "text", *, options=None, required=False):
    return {
        "id": identifier,
        "label": label,
        "section": section,
        "type": kind,
        "options": options or [],
        "required": required,
    }


DEFAULT_QUESTIONNAIRE = [
    q("objective", "Objectif principal du produit", "1. Produit et objectif", "multiselect", options=["Hydratation", "Anti-âge", "Éclaircissant / Anti-taches", "Anti-acné / Purifiant", "Protection UV", "Anti-chute", "Exfoliant", "Apaisant / Anti-rougeurs", "Autre"], required=True),
    q("application_zone", "Zone d’application", "1. Produit et objectif", "multiselect", options=["Visage", "Corps", "Contour des yeux", "Lèvres", "Cheveux", "Cuir chevelu"], required=True),
    q("target", "Public et type de peau ou cheveux", "1. Produit et objectif", "multiselect", options=["Enfants / Bébés", "Adultes", "Homme", "Femme", "Peaux sensibles", "Peaux grasses / à problèmes", "Peaux / Cheveux secs", "Autre"], required=True),
    q("efficacy_level", "Niveau d’efficacité et résultat attendu", "1. Produit et objectif", "textarea", required=True),
    q("texture", "Texture souhaitée", "2. Sensorialité", "multiselect", options=["Légère / Aqueuse", "Fluide", "Riche / Onctueuse", "Non grasse", "Mousse dense", "Autre"]),
    q("finish", "Fini recherché", "2. Sensorialité", "multiselect", options=["Mat", "Brillant / Glowy", "Toucher sec", "Soyeux", "Poudreux"]),
    q("absorption", "Absorption", "2. Sensorialité", "select", options=["Rapide", "Moyenne", "Lente"]),
    q("odor", "Parfum / odeur", "2. Sensorialité", "select", options=["Sans parfum", "Hypoallergénique", "Parfum spécifique"]),
    q("odor_details", "Précisions sur le parfum", "2. Sensorialité"),
    q("color", "Couleur souhaitée", "2. Sensorialité", "select", options=["Naturelle", "Blanche / Opaque", "Teintée"]),
    q("required_ingredients", "Actifs ou ingrédients obligatoires", "3. Formulation", "textarea"),
    q("blacklist", "Ingrédients à exclure", "3. Formulation", "multiselect", options=["Parabènes", "Sulfates", "Silicones", "PEG", "Huiles minérales", "Allergènes précisés ci-dessous"]),
    q("blacklist_details", "Autres exclusions ou allergènes", "3. Formulation", "textarea"),
    q("target_ph", "pH cible", "3. Formulation", "text"),
    q("viscosity", "Viscosité souhaitée", "3. Formulation", "text"),
    q("emulsion", "Type d’émulsion", "3. Formulation", "select", options=["Huile dans eau (H/E)", "Eau dans huile (E/H)", "Sans émulsion", "À proposer"]),
    q("packaging_type", "Type de packaging", "4. Packaging", "multiselect", options=["Tube", "Pot", "Flacon", "Airless", "Pompe", "Autre"], required=True),
    q("packaging_material", "Matière du packaging", "4. Packaging", "select", options=["Plastique", "Verre", "Aluminium", "À proposer"]),
    q("packaging_constraints", "Contraintes de packaging", "4. Packaging", "textarea"),
    q("markets", "Marchés et réglementations visés", "5. Conformité", "multiselect", options=["Maroc", "Union européenne – Règlement 1223/2009", "États-Unis – FDA", "Autre"], required=True),
    q("positioning", "Positionnement et charte de marque", "5. Conformité", "textarea"),
    q("labels", "Labels et allégations souhaités", "5. Conformité", "multiselect", options=["Bio", "Naturel", "Vegan", "Halal", "Dermatologique", "Sans conservateur"]),
    q("certifications", "Certifications souhaitées", "5. Conformité", "multiselect", options=["ECOCERT", "COSMOS", "Autre"]),
    q("tests", "Tests souhaités", "6. Tests et preuves", "multiselect", options=["Challenge test", "Stabilité", "Compatibilité contenu / contenant", "Patch / Dermatologique", "Oculaire", "Test d’usage sous contrôle dermatologique", "SPF", "Hydratation / Cornéométrie", "Autre"], required=True),
    q("claims", "Allégations à justifier", "6. Tests et preuves", "textarea"),
    q("max_raw_material_cost", "Coût maximal des matières premières (MAD / kg)", "7. Budget et délai", "number"),
    q("target_industrial_cost", "Coût industriel cible (MAD / unité)", "7. Budget et délai", "number"),
    q("priority", "Priorité", "7. Budget et délai", "select", options=["Prix", "Performance", "Équilibre prix / performance"]),
    q("prototype_deadline", "Date souhaitée du premier prototype", "7. Budget et délai", "date"),
    q("max_iterations", "Nombre maximal d’itérations", "7. Budget et délai", "number"),
    q("final_deadline", "Date finale souhaitée", "7. Budget et délai", "date"),
    q("deliverables", "Livrables attendus", "8. Livrables", "multiselect", options=["Prototypes", "Formule quantitative / INCI", "Mode opératoire laboratoire / industriel", "Rapports de tests", "Dossiers techniques des matières premières", "DIP", "Échantillons conditionnés"], required=True),
    q("additional_notes", "Informations complémentaires", "8. Livrables", "textarea"),
]

QUESTION_LABELS = {item["id"]: item["label"] for item in DEFAULT_QUESTIONNAIRE}
