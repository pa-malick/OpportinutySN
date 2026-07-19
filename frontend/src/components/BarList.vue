<script setup>
/**
 * Petit graphique a barres horizontales, reutilisable.
 *
 * On lui passe une liste d'objets, la cle du libelle, la cle de la valeur, et
 * (option) une fonction de formatage de la valeur affichee. Il met les barres a
 * l'echelle tout seul. Sert pour les salaires, les competences, les entreprises.
 */
import { computed } from "vue";

const props = defineProps({
  titre: { type: String, default: "" },
  items: { type: Array, default: () => [] },
  labelKey: { type: String, required: true },
  valueKey: { type: String, required: true },
  format: { type: Function, default: (v) => v },
});

const maxi = computed(() => {
  const valeurs = props.items.map((i) => i[props.valueKey] || 0);
  return valeurs.length ? Math.max(...valeurs) : 1;
});

function largeur(item) {
  return ((item[props.valueKey] || 0) / maxi.value) * 100 + "%";
}
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-5">
    <h3 class="mb-4 text-sm font-semibold text-slate-700">{{ titre }}</h3>

    <p v-if="!items.length" class="text-xs text-slate-400">Aucune donnée.</p>

    <div v-else class="space-y-3">
      <div v-for="item in items" :key="item[labelKey]">
        <div class="mb-1 flex items-center justify-between gap-3 text-xs">
          <span class="truncate text-slate-600">{{ item[labelKey] }}</span>
          <span class="tabular shrink-0 font-medium text-slate-800">
            {{ format(item[valueKey]) }}
          </span>
        </div>
        <div class="h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            class="h-full rounded-full bg-accent transition-all duration-500 ease-out"
            :style="{ width: largeur(item) }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>
