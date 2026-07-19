<script setup>
/**
 * Table des offres filtrees.
 *
 * Volontairement sobre : on trie en cliquant sur les entetes, on signale d'un
 * seul badge colore les offres qui sortent du lot (vert = opportunite bien
 * payee, rouge = piege sous-paye), et un clic sur la ligne ouvre le detail
 * avec le lien pour postuler. Rien de plus.
 */
import { ref, computed } from "vue";
import { fcfa } from "../utils/format";
import { salaireRef, signalOffre } from "../utils/aggregate";

const props = defineProps({
  offres: { type: Array, default: () => [] },
  // Moyenne de salaire par metier, pour classer opportunite vs piege.
  moyennes: { type: Object, default: () => ({}) },
});

// Etat du tri : quelle colonne, quel sens.
const triCle = ref("salaire");
const triSens = ref("desc");

// Offre ouverte dans le panneau de detail (null = panneau ferme).
const selection = ref(null);

function trierPar(cle) {
  if (triCle.value === cle) {
    triSens.value = triSens.value === "asc" ? "desc" : "asc";
  } else {
    triCle.value = cle;
    triSens.value = "asc";
  }
}

// Renvoie la valeur a comparer selon la colonne triee.
function valeurTri(o) {
  if (triCle.value === "salaire") return salaireRef(o) || 0;
  if (triCle.value === "titre") return (o.titre || "").toLowerCase();
  if (triCle.value === "entreprise") return (o.entreprise || "").toLowerCase();
  if (triCle.value === "date") return o.date_publication || "";
  return "";
}

const offresTriees = computed(() => {
  const copie = [...props.offres];
  copie.sort((a, b) => {
    const va = valeurTri(a);
    const vb = valeurTri(b);
    if (va < vb) return triSens.value === "asc" ? -1 : 1;
    if (va > vb) return triSens.value === "asc" ? 1 : -1;
    return 0;
  });
  return copie;
});

// Petite fleche indiquant le sens du tri sur la colonne active.
function fleche(cle) {
  if (triCle.value !== cle) return "";
  return triSens.value === "asc" ? " ↑" : " ↓";
}

// Signal de l'offre : "opportunite", "piege" ou null.
function signal(o) {
  return signalOffre(o, props.moyennes);
}
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
    <div class="flex items-center justify-between border-b border-slate-200 px-5 py-3">
      <h3 class="text-sm font-semibold text-slate-700">
        Offres ({{ offres.length }})
      </h3>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-slate-200 text-left text-xs text-slate-500">
            <th
              class="cursor-pointer px-5 py-3 font-medium hover:text-accent"
              @click="trierPar('titre')"
            >
              Poste{{ fleche("titre") }}
            </th>
            <th
              class="cursor-pointer px-5 py-3 font-medium hover:text-accent"
              @click="trierPar('entreprise')"
            >
              Entreprise{{ fleche("entreprise") }}
            </th>
            <th class="px-5 py-3 font-medium">Métier</th>
            <th class="px-5 py-3 font-medium">Ville</th>
            <th
              class="cursor-pointer px-5 py-3 text-right font-medium hover:text-accent"
              @click="trierPar('salaire')"
            >
              Salaire{{ fleche("salaire") }}
            </th>
            <th
              class="cursor-pointer px-5 py-3 font-medium hover:text-accent"
              @click="trierPar('date')"
            >
              Publiée{{ fleche("date") }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(o, i) in offresTriees"
            :key="i"
            class="cursor-pointer border-b border-slate-100 hover:bg-slate-50 last:border-0"
            @click="selection = o"
          >
            <td class="px-5 py-3 text-slate-800">
              {{ o.titre }}
              <span
                v-if="signal(o) === 'opportunite'"
                class="ml-2 rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700"
                >opportunité</span
              >
              <span
                v-else-if="signal(o) === 'piege'"
                class="ml-2 rounded bg-rose-100 px-1.5 py-0.5 text-[10px] font-medium text-rose-600"
                >piège</span
              >
            </td>
            <td class="px-5 py-3 text-slate-600">{{ o.entreprise }}</td>
            <td class="px-5 py-3 text-slate-600">{{ o.categorie }}</td>
            <td class="px-5 py-3 text-slate-600">{{ o.lieu }}</td>
            <td class="tabular px-5 py-3 text-right text-slate-800">
              {{ fcfa(o.salaire_min) }} - {{ fcfa(o.salaire_max) }}
            </td>
            <td class="tabular px-5 py-3 text-slate-500">
              {{ o.date_publication || "n/d" }}
            </td>
          </tr>
          <tr v-if="!offres.length">
            <td colspan="6" class="px-5 py-8 text-center text-slate-400">
              Aucune offre ne correspond aux filtres.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Panneau de detail, ouvert au clic sur une ligne. -->
  <div
    v-if="selection"
    class="fixed inset-0 z-30 flex bg-slate-900/30"
    @click.self="selection = null"
  >
    <aside
      class="ml-auto flex h-full w-full max-w-md flex-col overflow-y-auto bg-white shadow-xl"
    >
      <div class="flex items-start justify-between gap-4 border-b border-slate-200 px-6 py-4">
        <div>
          <span
            v-if="signal(selection) === 'opportunite'"
            class="mb-2 inline-block rounded bg-emerald-100 px-2 py-0.5 text-[11px] font-medium text-emerald-700"
            >Top opportunité</span
          >
          <span
            v-else-if="signal(selection) === 'piege'"
            class="mb-2 inline-block rounded bg-rose-100 px-2 py-0.5 text-[11px] font-medium text-rose-600"
            >Salaire suspect</span
          >
          <h3 class="text-base font-bold text-slate-900">{{ selection.titre }}</h3>
          <p class="text-sm text-slate-500">
            {{ selection.entreprise }} · {{ selection.lieu }}
          </p>
        </div>
        <button
          @click="selection = null"
          class="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          aria-label="Fermer"
        >
          ✕
        </button>
      </div>

      <div class="space-y-5 px-6 py-5 text-sm">
        <!-- Infos cles. -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="text-xs text-slate-400">Métier</p>
            <p class="text-slate-800">{{ selection.categorie || "n/d" }}</p>
          </div>
          <div>
            <p class="text-xs text-slate-400">Salaire</p>
            <p class="tabular text-slate-800">
              {{ fcfa(selection.salaire_min) }} - {{ fcfa(selection.salaire_max) }} FCFA
            </p>
          </div>
          <div>
            <p class="text-xs text-slate-400">Publiée le</p>
            <p class="text-slate-800">{{ selection.date_publication || "n/d" }}</p>
          </div>
          <div>
            <p class="text-xs text-slate-400">Source</p>
            <p class="text-slate-800">{{ selection.source || "n/d" }}</p>
          </div>
        </div>

        <!-- Competences requises. -->
        <div v-if="selection.competences && selection.competences.length">
          <p class="mb-2 text-xs text-slate-400">Compétences requises</p>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="c in selection.competences"
              :key="c"
              class="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700"
              >{{ c }}</span
            >
          </div>
        </div>
      </div>

      <!-- Action principale : postuler / voir l'annonce. -->
      <div class="mt-auto border-t border-slate-200 px-6 py-4">
        <a
          v-if="selection.url"
          :href="selection.url"
          target="_blank"
          rel="noopener"
          class="block rounded-lg bg-accent px-4 py-3 text-center text-sm font-medium text-white transition-opacity hover:opacity-90"
        >
          Voir l'offre et postuler
        </a>
        <p v-else class="text-center text-xs text-slate-400">
          Lien vers l'annonce indisponible pour cette offre.
        </p>
      </div>
    </aside>
  </div>
</template>
