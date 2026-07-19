/**
 * Config Tailwind : theme sobre, pense pour un outil de travail.
 *
 * Fond clair et neutre, texte lisible, un accent teal discret (repris du
 * dashboard Streamlit du projet). Pas d'effet inutile : ici on veut lire des
 * chiffres vite et bien.
 */
export default {
  content: ["./index.html", "./src/**/*.{vue,js}"],
  theme: {
    extend: {
      colors: {
        // Accent teal, sobre et professionnel.
        accent: {
          DEFAULT: "#0f766e",
          soft: "#ccfbf1",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        // Chiffres alignes pour les tableaux.
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
