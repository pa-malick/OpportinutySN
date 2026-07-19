<script setup>
/**
 * Rangee de chiffres cles.
 *
 * Quatre indicateurs en haut de l'ecran : combien d'offres, combien
 * d'entreprises, le salaire median, et le nombre d'anomalies detectees.
 * Se met a jour a chaque changement de filtre.
 */
import { fcfa } from "../utils/format";

defineProps({
  kpis: { type: Object, required: true },
});
</script>

<template>
  <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
    <div class="rounded-xl border border-slate-200 bg-white p-5">
      <p class="tabular text-3xl font-bold text-slate-900">{{ kpis.total }}</p>
      <p class="mt-1 text-xs text-slate-500">offres</p>
    </div>
    <div class="rounded-xl border border-slate-200 bg-white p-5">
      <p class="tabular text-3xl font-bold text-slate-900">{{ kpis.entreprises }}</p>
      <p class="mt-1 text-xs text-slate-500">entreprises</p>
    </div>
    <div class="rounded-xl border border-slate-200 bg-white p-5">
      <p class="tabular text-3xl font-bold text-slate-900">{{ fcfa(kpis.salaireMedian) }}</p>
      <p class="mt-1 text-xs text-slate-500">salaire médian (FCFA)</p>
    </div>
    <div class="rounded-xl border border-slate-200 bg-white p-5">
      <p class="tabular text-3xl font-bold" :class="kpis.anomalies ? 'text-rose-600' : 'text-slate-900'">
        {{ kpis.anomalies }}
      </p>
      <p class="mt-1 text-xs text-slate-500">anomalies de salaire</p>
    </div>
  </div>
</template>
