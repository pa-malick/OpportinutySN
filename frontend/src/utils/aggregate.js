/**
 * Fonctions d'agregation, cote navigateur.
 *
 * Ce sont les memes calculs que la couche analyse Python, mais appliques sur la
 * liste filtree en direct. Comme ca, chaque changement de filtre recalcule tout
 * instantanement, sans rappeler le serveur. Des fonctions pures, faciles a
 * tester et a relire.
 */

// Mediane d'un tableau de nombres.
function mediane(valeurs) {
  const v = valeurs.filter((x) => x != null).sort((a, b) => a - b);
  if (!v.length) return null;
  const milieu = Math.floor(v.length / 2);
  return v.length % 2 ? v[milieu] : (v[milieu - 1] + v[milieu]) / 2;
}

// Salaire de reference d'une offre (deja calcule cote serveur, sinon on refait).
export function salaireRef(offre) {
  if (offre.salaire_ref != null) return offre.salaire_ref;
  if (offre.salaire_min != null && offre.salaire_max != null) {
    return (offre.salaire_min + offre.salaire_max) / 2;
  }
  return offre.salaire_min ?? offre.salaire_max ?? null;
}

// Chiffres cles pour la rangee de KPI.
export function kpis(offres) {
  const entreprises = new Set(offres.map((o) => o.entreprise));
  const salaires = offres.map(salaireRef).filter((x) => x != null);
  return {
    total: offres.length,
    entreprises: entreprises.size,
    anomalies: offres.filter((o) => o.anomalie).length,
    salaireMedian: mediane(salaires),
  };
}

// Salaire moyen par metier, trie du mieux paye au moins bien.
export function salaireParCategorie(offres) {
  const groupes = {};
  for (const o of offres) {
    const cat = o.categorie || "Autre";
    (groupes[cat] ??= []).push(salaireRef(o));
  }
  return Object.entries(groupes)
    .map(([categorie, sals]) => {
      const valides = sals.filter((x) => x != null);
      const moyenne = valides.length
        ? valides.reduce((a, b) => a + b, 0) / valides.length
        : 0;
      return { categorie, salaire_moyen: Math.round(moyenne), nombre: sals.length };
    })
    .sort((a, b) => b.salaire_moyen - a.salaire_moyen);
}

// Competences les plus citees.
export function topCompetences(offres, n = 12) {
  const compteur = {};
  for (const o of offres) {
    for (const c of o.competences || []) {
      compteur[c] = (compteur[c] || 0) + 1;
    }
  }
  return Object.entries(compteur)
    .map(([competence, occurrences]) => ({ competence, occurrences }))
    .sort((a, b) => b.occurrences - a.occurrences)
    .slice(0, n);
}

// Entreprises qui recrutent le plus.
export function topEntreprises(offres, n = 8) {
  const compteur = {};
  for (const o of offres) compteur[o.entreprise] = (compteur[o.entreprise] || 0) + 1;
  return Object.entries(compteur)
    .map(([entreprise, nombre]) => ({ entreprise, nombre }))
    .sort((a, b) => b.nombre - a.nombre)
    .slice(0, n);
}

// Listes de valeurs distinctes, pour alimenter les filtres.
export function valeursDistinctes(offres, cle) {
  return [...new Set(offres.map((o) => o[cle]).filter(Boolean))].sort();
}

// Salaire de reference moyen par metier, sur tout le jeu de donnees.
// Sert de point de comparaison pour dire si une anomalie est haute ou basse.
export function moyennesSalaireParCategorie(offres) {
  const groupes = {};
  for (const o of offres) {
    const cat = o.categorie || "Autre";
    const s = salaireRef(o);
    if (s != null) (groupes[cat] ??= []).push(s);
  }
  const moyennes = {};
  for (const [cat, sals] of Object.entries(groupes)) {
    moyennes[cat] = sals.reduce((a, b) => a + b, 0) / sals.length;
  }
  return moyennes;
}

// Classe une offre en anomalie : "opportunite" si elle paye au-dessus de la
// moyenne de son metier, "piege" si en dessous. null si pas une anomalie.
// C'est ce qui rend visible la moitie positive de la detection.
export function signalOffre(offre, moyennes) {
  if (!offre.anomalie) return null;
  const s = salaireRef(offre);
  const moy = moyennes[offre.categorie || "Autre"];
  if (s == null || moy == null) return "piege"; // prudence : on alerte par defaut
  return s >= moy ? "opportunite" : "piege";
}
