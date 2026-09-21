export type EditorialPageConfig = {
  eyebrow: string;
  summary: string;
  image: string;
  imageAlt: string;
  highlights: string[];
  steps: Array<{ title: string; text: string }>;
  ctaHref: string;
  ctaLabel: string;
};

export const EDITORIAL_PAGE_CONTENT: Record<string, EditorialPageConfig> = {
  laboratoire: {
    eyebrow: "Savoir-faire MIELMAR",
    summary: "Un espace dédié à la préparation, au suivi et à la qualité de chaque projet cosmétique.",
    image: "/editorial/laboratory-manufacturing.png",
    imageAlt: "Préparation d’une crème cosmétique dans un laboratoire moderne",
    highlights: ["Fabrication maîtrisée", "Matières suivies", "Contrôles adaptés"],
    steps: [
      { title: "Cadrer", text: "Définir le produit, son usage et les attentes." },
      { title: "Formuler", text: "Sélectionner les matières et préparer la formule." },
      { title: "Contrôler", text: "Planifier les essais et vérifier la stabilité." },
    ],
    ctaHref: "/sur-mesure", ctaLabel: "Démarrer un projet",
  },
  "formule-cle-en-main": {
    eyebrow: "Développement maîtrisé",
    summary: "Une base déjà structurée, personnalisée pour construire votre gamme plus rapidement.",
    image: "/editorial/laboratory-manufacturing.png",
    imageAlt: "Fabrication professionnelle d’un soin cosmétique",
    highlights: ["Base structurée", "Personnalisation", "Validation avant production"],
    steps: [
      { title: "Choisir", text: "Sélectionner le type de produit et la base adaptée." },
      { title: "Adapter", text: "Ajuster texture, actifs, parfum et présentation." },
      { title: "Valider", text: "Confirmer la formule, le packaging et la quantité." },
    ],
    ctaHref: "/informations/contact", ctaLabel: "Parler de mon projet",
  },
  "formule-sur-mesure": {
    eyebrow: "Votre formule unique",
    summary: "Un parcours construit autour de votre cahier des charges et des matières disponibles.",
    image: "/editorial/custom-formulation.png",
    imageAlt: "Cahier des charges et ingrédients pour une formule cosmétique personnalisée",
    highlights: ["Cahier des charges", "Formule expliquée", "Validation humaine"],
    steps: [
      { title: "Votre besoin", text: "Vous précisez le produit, le public et le résultat recherché." },
      { title: "La proposition", text: "Le laboratoire prépare une formule complète et justifiée." },
      { title: "Votre validation", text: "Vous confirmez la proposition avant la suite du projet." },
    ],
    ctaHref: "/sur-mesure", ctaLabel: "Remplir le cahier des charges",
  },
  accompagnement: {
    eyebrow: "À vos côtés",
    summary: "Des décisions claires et un suivi organisé depuis l’idée jusqu’au lancement.",
    image: "/editorial/accompaniment.png",
    imageAlt: "Séance d’accompagnement autour d’échantillons cosmétiques",
    highlights: ["Écoute du besoin", "Conseils à chaque étape", "Suivi du projet"],
    steps: [
      { title: "Échanger", text: "Comprendre votre cible, vos priorités et votre budget." },
      { title: "Planifier", text: "Poser les étapes, les choix à valider et le calendrier." },
      { title: "Avancer", text: "Suivre les décisions jusqu’à la préparation du lancement." },
    ],
    ctaHref: "/informations/contact", ctaLabel: "Être accompagné",
  },
  ingredients: {
    eyebrow: "Matières premières",
    summary: "Une sélection organisée entre richesse botanique et exigences de formulation.",
    image: "/editorial/ingredients.png",
    imageAlt: "Huiles, miel, aloe et extraits utilisés en formulation cosmétique",
    highlights: ["Familles organisées", "Fonction identifiée", "Stock suivi"],
    steps: [
      { title: "Sélectionner", text: "Choisir les matières selon l’objectif du produit." },
      { title: "Vérifier", text: "Contrôler disponibilité, rôle et compatibilité." },
      { title: "Justifier", text: "Expliquer le choix et la proportion de chaque matière." },
    ],
    ctaHref: "/sur-mesure", ctaLabel: "Créer une formule",
  },
  packaging: {
    eyebrow: "Forme & usage",
    summary: "Le bon contenant pour protéger la formule et valoriser l’expérience du produit.",
    image: "/editorial/packaging.png",
    imageAlt: "Sélection de flacons, pots et étuis pour produits cosmétiques",
    highlights: ["Format adapté", "Compatibilité formule", "Gamme cohérente"],
    steps: [
      { title: "Définir", text: "Choisir contenance, usage et niveau de finition." },
      { title: "Comparer", text: "Évaluer flacons, pots, pompes et étuis." },
      { title: "Harmoniser", text: "Construire une famille de produits cohérente." },
    ],
    ctaHref: "/informations/contact", ctaLabel: "Choisir mon packaging",
  },
  branding: {
    eyebrow: "Identité de marque",
    summary: "Un univers visuel cohérent pour rendre votre gamme claire et reconnaissable.",
    image: "/editorial/branding.png",
    imageAlt: "Moodboard de branding pour une marque cosmétique premium",
    highlights: ["Positionnement", "Identité visuelle", "Supports cohérents"],
    steps: [
      { title: "Positionner", text: "Définir la promesse, le public et la personnalité." },
      { title: "Créer", text: "Composer couleurs, logo, typographies et étiquettes." },
      { title: "Déployer", text: "Adapter l’identité au site et aux campagnes." },
    ],
    ctaHref: "/informations/contact", ctaLabel: "Construire ma marque",
  },
  reglementaire: {
    eyebrow: "Qualité & conformité",
    summary: "Des informations structurées et des contrôles adaptés avant la mise sur le marché.",
    image: "/editorial/quality-regulatory.png",
    imageAlt: "Contrôle qualité et dossier de suivi d’un produit cosmétique",
    highlights: ["Traçabilité", "Tests recommandés", "Dossier organisé"],
    steps: [
      { title: "Documenter", text: "Rassembler formule, matières et informations produit." },
      { title: "Contrôler", text: "Planifier stabilité, compatibilité et vérifications utiles." },
      { title: "Préparer", text: "Structurer les éléments nécessaires au marché visé." },
    ],
    ctaHref: "/informations/contact", ctaLabel: "Préparer mon dossier",
  },
  "a-propos": {
    eyebrow: "Notre univers",
    summary: "La nature marocaine, la création cosmétique et une expérience digitale plus simple.",
    image: "/mielmar-hero-reference-v3.png",
    imageAlt: "Univers naturel et produits MIELMAR inspirés du Maroc",
    highlights: ["Inspiration marocaine", "Beauté & bien-être", "Création accompagnée"],
    steps: [
      { title: "Nature", text: "Valoriser des matières et des rituels familiers." },
      { title: "Expertise", text: "Organiser chaque choix dans un parcours compréhensible." },
      { title: "Proximité", text: "Garder l’échange et la validation au centre du projet." },
    ],
    ctaHref: "/epicerie", ctaLabel: "Découvrir MIELMAR",
  },
};

export const HOME_SERVICES = ["accompagnement", "ingredients", "packaging", "branding", "reglementaire"] as const;
