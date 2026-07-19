<script setup>
/**
 * Logo du projet.
 *
 * Symbolique : des barres qui montent (le marche de l'emploi qui evolue) et une
 * courbe avec une etincelle (la veille qui repere l'opportunite). Le tout dans
 * un badge teal, la couleur d'accent du projet. SVG inline : net a toute taille,
 * aucune dependance, aucune requete reseau.
 */
defineProps({
  size: { type: Number, default: 36 },
  withText: { type: Boolean, default: true },
});
</script>

<template>
  <div class="flex items-center gap-2.5">
    <svg
      :width="size"
      :height="size"
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Logo OpportunitySN"
      class="shrink-0"
    >
      <rect width="40" height="40" rx="10" fill="url(#osn-grad)" />
      <!-- Barres ascendantes : le marche qui evolue. -->
      <rect x="9.5" y="23" width="4.6" height="7.5" rx="1.6" fill="#ffffff" fill-opacity="0.82" />
      <rect x="17.7" y="18" width="4.6" height="12.5" rx="1.6" fill="#ffffff" fill-opacity="0.9" />
      <rect x="25.9" y="13" width="4.6" height="17.5" rx="1.6" fill="#ffffff" />
      <!-- Courbe de veille + etincelle : l'opportunite reperee. -->
      <path
        d="M10.5 20 L19.8 15 L28.2 10"
        stroke="#5eead4"
        stroke-width="2.1"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <circle cx="28.4" cy="9.8" r="2.5" fill="#5eead4" />
      <defs>
        <linearGradient id="osn-grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop stop-color="#0f766e" />
          <stop offset="1" stop-color="#0b4f49" />
        </linearGradient>
      </defs>
    </svg>

    <div v-if="withText" class="leading-none">
      <p class="text-[15px] font-bold tracking-tight text-slate-900">
        Opportunity<span class="text-accent">SN</span>
      </p>
      <p class="mt-1 text-[10px] font-medium uppercase tracking-wider text-slate-400">
        Veille emploi Tech
      </p>
    </div>
  </div>
</template>
