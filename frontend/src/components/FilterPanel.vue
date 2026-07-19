<script setup>
/**
 * Panneau de filtres (colonne de gauche).
 *
 * Toute l'interaction de l'outil part d'ici : metier, ville, recherche texte,
 * salaire minimum. Les valeurs sont liees a l'App via v-model ; des qu'elles
 * changent, l'App recalcule tout. On expose aussi un bouton de reinitialisation.
 */
import { valeursDistinctes } from "../utils/aggregate";
import { computed, ref } from "vue";
import Logo from "./Logo.vue";

// Etat du menu deroulant (utile seulement sur mobile ; sur desktop la barre
// reste toujours affichee). Replie par defaut pour ne pas manger l'ecran.
const ouvert = ref(false);

const props = defineProps({
  offres: { type: Array, default: () => [] },
});

// Deux valeurs liees a l'App (Vue 3.4+ : plusieurs defineModel).
const metiers = defineModel("metiers", { default: () => [] });
const ville = defineModel("ville", { default: "" });
const recherche = defineModel("recherche", { default: "" });
const salaireMin = defineModel("salaireMin", { default: 0 });

// Options disponibles, deduites des donnees reelles.
const optionsMetiers = computed(() => valeursDistinctes(props.offres, "categorie"));
const optionsVilles = computed(() => valeursDistinctes(props.offres, "lieu"));

function basculerMetier(m) {
  const liste = metiers.value;
  metiers.value = liste.includes(m)
    ? liste.filter((x) => x !== m)
    : [...liste, m];
}

// Nombre de filtres actifs, pour un petit badge (touche pro).
const nbFiltresActifs = computed(() => {
  let n = metiers.value.length;
  if (ville.value) n += 1;
  if (recherche.value.trim()) n += 1;
  if (salaireMin.value > 0) n += 1;
  return n;
});

function reinitialiser() {
  metiers.value = [];
  ville.value = "";
  recherche.value = "";
  salaireMin.value = 0;
}
</script>

<template>
  <aside
    class="flex w-full flex-col border-b border-slate-200 bg-white lg:h-screen lg:w-72 lg:shrink-0 lg:overflow-y-auto lg:border-b-0 lg:border-r"
  >
    <!-- Bloc de marque : logo + bouton deroulant (mobile uniquement). -->
    <div class="flex items-center justify-between gap-3 border-b border-slate-200 px-6 py-4 lg:py-5">
      <Logo :size="38" />
      <button
        @click="ouvert = !ouvert"
        :aria-expanded="ouvert"
        class="flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:border-accent hover:text-accent lg:hidden"
      >
        Filtres
        <span
          v-if="nbFiltresActifs"
          class="rounded-full bg-accent-soft px-1.5 py-0.5 text-[10px] font-semibold text-accent"
        >
          {{ nbFiltresActifs }}
        </span>
        <svg
          class="h-4 w-4 transition-transform"
          :class="{ 'rotate-180': ouvert }"
          viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
    </div>

    <!-- Filtres : deroulant sur mobile, toujours visibles sur desktop. -->
    <div
      :class="ouvert ? 'block' : 'hidden'"
      class="space-y-6 p-6 lg:block"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Filtres
          </h2>
          <span
            v-if="nbFiltresActifs"
            class="rounded-full bg-accent-soft px-1.5 py-0.5 text-[10px] font-semibold text-accent"
          >
            {{ nbFiltresActifs }}
          </span>
        </div>
        <button
          @click="reinitialiser"
          :disabled="!nbFiltresActifs"
          class="text-xs font-medium text-accent transition-opacity hover:underline disabled:opacity-40"
        >
          Réinitialiser
        </button>
      </div>

      <!-- Recherche texte. -->
      <div>
        <label class="mb-2 block text-xs font-medium text-slate-500">Recherche</label>
        <div class="relative">
          <svg
            class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m21 21-4.3-4.3" stroke-linecap="round" />
          </svg>
          <input
            v-model="recherche"
            type="text"
            placeholder="Poste, entreprise..."
            class="w-full rounded-lg border border-slate-300 bg-slate-50 py-2 pl-9 pr-3 text-sm outline-none transition-colors focus:border-accent focus:bg-white focus:ring-1 focus:ring-accent"
          />
        </div>
      </div>

      <!-- Metiers (cases a cocher). -->
      <div>
        <label class="mb-2 block text-xs font-medium text-slate-500">Métier</label>
        <div class="space-y-1">
          <label
            v-for="m in optionsMetiers"
            :key="m"
            class="flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm text-slate-700 transition-colors hover:bg-slate-50"
          >
            <input
              type="checkbox"
              :checked="metiers.includes(m)"
              @change="basculerMetier(m)"
              class="h-4 w-4 rounded border-slate-300 text-accent focus:ring-accent"
            />
            {{ m }}
          </label>
        </div>
      </div>

      <!-- Ville. -->
      <div>
        <label class="mb-2 block text-xs font-medium text-slate-500">Ville</label>
        <select
          v-model="ville"
          class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm outline-none transition-colors focus:border-accent focus:bg-white focus:ring-1 focus:ring-accent"
        >
          <option value="">Toutes les villes</option>
          <option v-for="v in optionsVilles" :key="v" :value="v">{{ v }}</option>
        </select>
      </div>

      <!-- Salaire minimum. -->
      <div>
        <div class="mb-2 flex items-baseline justify-between">
          <label class="text-xs font-medium text-slate-500">Salaire minimum</label>
          <span class="tabular text-xs font-semibold text-accent">
            {{ Number(salaireMin).toLocaleString("fr-FR") }} FCFA
          </span>
        </div>
        <input
          v-model.number="salaireMin"
          type="range"
          min="0"
          max="2000000"
          step="50000"
          class="w-full accent-accent"
        />
      </div>
    </div>
  </aside>
</template>
