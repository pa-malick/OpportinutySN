<script setup>
/**
 * Carte d'abonnement aux alertes.
 *
 * L'utilisateur saisit son email pour recevoir les alertes (anomalies,
 * nouvelles opportunites). Le formulaire POST l'email vers un webhook Make
 * dedie a l'abonnement, qui se charge de l'enregistrer (Google Sheet, email de
 * confirmation, etc.). L'URL du webhook vient de la variable d'environnement
 * VITE_MAKE_SUBSCRIBE_URL (voir frontend/.env).
 *
 * On envoie en mode "no-cors" : le webhook Make ne renvoie pas d'en-tetes CORS,
 * donc on ne peut pas lire sa reponse. On considere donc l'envoi reussi tant
 * qu'il n'y a pas d'erreur reseau (comportement classique d'un formulaire vers
 * un webhook no-code).
 */
import { ref } from "vue";

const URL_ABONNEMENT = import.meta.env.VITE_MAKE_SUBSCRIBE_URL || "";

const email = ref("");
const etat = ref("idle"); // idle | envoi | ok | erreur
const message = ref("");

const canaux = ["Email", "Slack", "WhatsApp"];

function emailValide(valeur) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valeur);
}

async function sabonner() {
  message.value = "";
  if (!emailValide(email.value)) {
    etat.value = "erreur";
    message.value = "Merci d'entrer une adresse email valide.";
    return;
  }
  if (!URL_ABONNEMENT) {
    etat.value = "erreur";
    message.value = "Abonnement non configuré (webhook Make manquant).";
    return;
  }

  etat.value = "envoi";
  try {
    // On envoie en format formulaire (x-www-form-urlencoded) : Make le decoupe
    // automatiquement en champs nommes (email, source, date). En JSON brut sans
    // en-tete, Make recevrait un seul bloc de texte non exploitable.
    await fetch(URL_ABONNEMENT, {
      method: "POST",
      mode: "no-cors",
      body: new URLSearchParams({
        email: email.value.trim(),
        source: "opportunitysn-front",
        date: new Date().toISOString(),
      }),
    });
    etat.value = "ok";
  } catch (e) {
    etat.value = "erreur";
    message.value = "Échec de l'envoi, réessaie dans un instant.";
  }
}
</script>

<template>
  <div class="rounded-xl border border-teal-200 bg-teal-50 p-5">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <!-- Presentation. -->
      <div class="flex items-start gap-3">
        <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent text-white">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
            <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
          </svg>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-slate-900">Recevez les alertes automatiques</h3>
          <p class="mt-1 text-xs text-slate-600">
            Anomalies de salaire et nouvelles opportunités, chaque matin.
            <span class="whitespace-nowrap text-slate-400">via Make ·
              {{ canaux.join(" · ") }}</span>
          </p>
        </div>
      </div>

      <!-- Formulaire d'abonnement. -->
      <form
        v-if="etat !== 'ok'"
        @submit.prevent="sabonner"
        class="flex w-full flex-col gap-2 sm:flex-row lg:w-auto"
      >
        <input
          v-model="email"
          type="email"
          placeholder="votre@email.com"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition-colors focus:border-accent focus:ring-1 focus:ring-accent sm:w-56"
        />
        <button
          type="submit"
          :disabled="etat === 'envoi'"
          class="shrink-0 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-60"
        >
          {{ etat === "envoi" ? "Envoi..." : "S'abonner" }}
        </button>
      </form>

      <!-- Confirmation. -->
      <div
        v-else
        class="flex items-center gap-2 rounded-lg bg-emerald-100 px-4 py-2 text-sm font-medium text-emerald-700"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        Inscrit ! Vous recevrez les alertes.
      </div>
    </div>

    <!-- Message d'erreur eventuel. -->
    <p v-if="etat === 'erreur' && message" class="mt-2 text-xs text-rose-600">
      {{ message }}
    </p>
  </div>
</template>
