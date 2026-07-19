<script setup>
/**
 * Composant principal : l'outil de veille.
 *
 * Logique simple et lisible : on charge les offres une fois, on tient l'etat
 * des filtres ici, et on recalcule la liste filtree + tous les agregats a
 * chaque changement. La colonne de gauche filtre, la zone de droite affiche.
 */
import { ref, computed } from "vue";
import { useOffres } from "./composables/useOffres";
import {
  kpis,
  salaireParCategorie,
  topCompetences,
  topEntreprises,
  salaireRef,
  moyennesSalaireParCategorie,
} from "./utils/aggregate";
import { fcfa, exporterPdf } from "./utils/format";

import FilterPanel from "./components/FilterPanel.vue";
import KpiRow from "./components/KpiRow.vue";
import BarList from "./components/BarList.vue";
import OffersTable from "./components/OffersTable.vue";
import Logo from "./components/Logo.vue";
import AlertBanner from "./components/AlertBanner.vue";

const { offres, genereLe, source, chargement, erreur, recharger } = useOffres();

// Etat des filtres (source de verite unique).
const fMetiers = ref([]);
const fVille = ref("");
const fRecherche = ref("");
const fSalaireMin = ref(0);

// La liste filtree : c'est le coeur de l'interactivite.
const offresFiltrees = computed(() => {
  const texte = fRecherche.value.trim().toLowerCase();
  return offres.value.filter((o) => {
    if (fMetiers.value.length && !fMetiers.value.includes(o.categorie)) return false;
    if (fVille.value && o.lieu !== fVille.value) return false;
    if (texte) {
      const cible = `${o.titre} ${o.entreprise}`.toLowerCase();
      if (!cible.includes(texte)) return false;
    }
    if (fSalaireMin.value > 0) {
      const ref = salaireRef(o);
      if (ref == null || ref < fSalaireMin.value) return false;
    }
    return true;
  });
});

// Tous les agregats derivent de la liste filtree.
const statsKpi = computed(() => kpis(offresFiltrees.value));
const salaires = computed(() => salaireParCategorie(offresFiltrees.value));
const competences = computed(() => topCompetences(offresFiltrees.value));
const entreprises = computed(() => topEntreprises(offresFiltrees.value));

// Moyennes calculees sur tout le jeu (pas la vue filtree) pour un classement
// opportunite / piege stable quels que soient les filtres.
const moyennes = computed(() => moyennesSalaireParCategorie(offres.value));

// Date de mise a jour, lisible.
const majTexte = computed(() => {
  if (!genereLe.value) return "";
  return new Date(genereLe.value).toLocaleString("fr-FR");
});

const exportEnCours = ref(false);
async function exporter() {
  if (exportEnCours.value) return;
  exportEnCours.value = true;
  try {
    await exporterPdf(offresFiltrees.value);
  } finally {
    exportEnCours.value = false;
  }
}
</script>

<template>
  <div class="lg:flex">
    <!-- Colonne de filtres. -->
    <FilterPanel
      :offres="offres"
      v-model:metiers="fMetiers"
      v-model:ville="fVille"
      v-model:recherche="fRecherche"
      v-model:salaireMin="fSalaireMin"
    />

    <!-- Zone principale. -->
    <main class="flex-1 lg:h-screen lg:overflow-y-auto">
      <!-- Barre du haut. -->
      <header
        class="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-white/90 px-6 py-4 backdrop-blur"
      >
        <div>
          <h1 class="text-lg font-bold text-slate-900">Marché de l'emploi Tech</h1>
          <p class="text-xs text-slate-500">
            <span v-if="source">
              source :
              <span class="font-medium text-accent">{{ source === "api" ? "API live" : "snapshot" }}</span>
              <span v-if="majTexte"> · maj {{ majTexte }}</span>
            </span>
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="recharger"
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-600 transition-colors hover:border-accent hover:text-accent"
          >
            Rafraîchir
          </button>
          <button
            @click="exporter"
            :disabled="exportEnCours || !offresFiltrees.length"
            class="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            {{ exportEnCours ? "Génération..." : "Télécharger PDF" }}
          </button>
        </div>
      </header>

      <!-- Contenu. -->
      <div class="p-6">
        <p v-if="chargement" class="text-sm text-slate-500">Chargement des offres...</p>
        <p v-else-if="erreur" class="text-sm text-rose-600">{{ erreur }}</p>

        <div v-else class="space-y-8">
          <!-- Chiffres cles. -->
          <KpiRow :kpis="statsKpi" />

          <!-- L'action d'abord : la table des offres. -->
          <OffersTable :offres="offresFiltrees" :moyennes="moyennes" />

          <!-- Les statistiques du marche, en bas. -->
          <section>
            <h2 class="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
              Statistiques du marché
            </h2>
            <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <BarList
                titre="Salaire moyen par métier"
                :items="salaires"
                label-key="categorie"
                value-key="salaire_moyen"
                :format="(v) => fcfa(v) + ' FCFA'"
              />
              <BarList
                titre="Compétences les plus demandées"
                :items="competences"
                label-key="competence"
                value-key="occurrences"
              />
              <BarList
                titre="Entreprises qui recrutent le plus"
                :items="entreprises"
                label-key="entreprise"
                value-key="nombre"
              />
            </div>
          </section>

          <!-- Abonnement aux alertes (Make), en bas. -->
          <AlertBanner />
        </div>
      </div>

      <!-- Pied de page : l'auteur du projet. -->
      <footer class="border-t border-slate-200 px-6 py-6">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex items-center gap-3">
            <Logo :size="34" :with-text="false" />
            <div class="text-xs">
              <p class="font-semibold text-slate-700">Papa Malick NDIAYE</p>
              <p class="text-slate-500">
                Master Data Science &amp; Génie Logiciel · Université Alioune Diop de Bambey
              </p>
            </div>
          </div>
          <div class="flex items-center gap-4 text-xs font-medium">
            <a
              href="https://github.com/pa-malick"
              target="_blank"
              rel="noopener"
              class="text-slate-500 transition-colors hover:text-accent"
            >
              GitHub
            </a>
            <a
              href="https://www.linkedin.com/in/papa-malick-ndiaye-b58b22309"
              target="_blank"
              rel="noopener"
              class="text-slate-500 transition-colors hover:text-accent"
            >
              LinkedIn
            </a>
          </div>
        </div>
        <p class="mt-4 text-[11px] text-slate-400">
          OpportunitySN · Veille automatisée du marché de l'emploi Tech au Sénégal.
        </p>
      </footer>
    </main>
  </div>
</template>
