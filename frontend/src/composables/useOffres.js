import { ref, onMounted } from "vue";

/**
 * Charge la liste des offres.
 *
 * Deux modes :
 *   - Si VITE_API_URL est defini (dev avec le backend lance), on interroge
 *     l'API FastAPI, et on se rabat sur le snapshot en cas d'echec.
 *   - Sinon (front statique deploye, sans backend), on charge directement le
 *     snapshot JSON, sans tenter d'API (pas d'attente inutile).
 * L'outil affiche donc toujours de vraies donnees, en local comme en ligne.
 */
const API_URL = import.meta.env.VITE_API_URL || "";
const SNAPSHOT_URL = "/offres.json";

export function useOffres() {
  const offres = ref([]);
  const genereLe = ref(null);
  const source = ref("");
  const chargement = ref(true);
  const erreur = ref(null);

  async function charger() {
    chargement.value = true;
    erreur.value = null;

    // 1. API en direct (seulement si une URL est configuree ; timeout court).
    if (API_URL) {
      try {
        const controleur = new AbortController();
        const minuteur = setTimeout(() => controleur.abort(), 1500);
        const rep = await fetch(API_URL, { signal: controleur.signal });
        clearTimeout(minuteur);
        if (rep.ok) {
          const json = await rep.json();
          offres.value = json.offres;
          genereLe.value = json.generated_at;
          source.value = "api";
          chargement.value = false;
          return;
        }
      } catch (e) {
        // Pas d'API joignable, on passe au snapshot.
      }
    }

    // 2. Snapshot embarque.
    try {
      const rep = await fetch(SNAPSHOT_URL);
      if (!rep.ok) throw new Error("snapshot introuvable");
      const json = await rep.json();
      offres.value = json.offres;
      genereLe.value = json.generated_at;
      source.value = "snapshot";
    } catch (e) {
      erreur.value = "Aucune donnee. Lance la pipeline puis l'export du snapshot.";
    } finally {
      chargement.value = false;
    }
  }

  onMounted(charger);

  return { offres, genereLe, source, chargement, erreur, recharger: charger };
}
