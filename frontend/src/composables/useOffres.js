import { ref, onMounted } from "vue";

/**
 * Charge la liste des offres.
 *
 * On tente l'API FastAPI en direct, puis on se rabat sur le snapshot JSON.
 * L'outil affiche donc toujours de vraies donnees, avec ou sans backend lance.
 */
const API_URL = "http://localhost:8000/api/offres";
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

    // 1. API en direct (timeout court).
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
      // Pas d'API, on passe au snapshot.
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
