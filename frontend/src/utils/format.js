/** Formatage partage par toute l'interface. */

// 1200000 -> "1 200 000". Renvoie "n/d" si la valeur manque.
export function fcfa(v) {
  if (v == null) return "n/d";
  return Math.round(v).toLocaleString("fr-FR").replace(/ |,/g, " ");
}

// Groupe les milliers avec une espace NORMALE. On evite toLocaleString ici car
// il utilise une espace insecable etroite que jsPDF n'affiche pas (chiffres
// bizarres dans le PDF).
function grouper(n) {
  return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

// Fourchette de salaire lisible pour le PDF.
function salaireTexte(o) {
  if (o.salaire_min == null && o.salaire_max == null) return "n/d";
  const a = o.salaire_min != null ? grouper(o.salaire_min) : "?";
  const b = o.salaire_max != null ? grouper(o.salaire_max) : "?";
  return a === b ? a : `${a} - ${b}`;
}

/**
 * Telecharge la liste d'offres filtree en PDF.
 *
 * Plus sympa qu'un CSV pour un candidat : un document propre, avec l'en-tete
 * du projet, la liste des offres et de quoi l'imprimer ou le partager. Tout est
 * genere cote navigateur avec jsPDF, aucun serveur.
 */
export async function exporterPdf(offres, nomFichier = "mes-offres-opportunitysn.pdf") {
  // Import a la demande : jsPDF n'est telecharge que si on exporte vraiment,
  // ce qui garde le chargement initial du site leger.
  const { jsPDF } = await import("jspdf");
  const autoTable = (await import("jspdf-autotable")).default;

  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const W = doc.internal.pageSize.getWidth();
  const H = doc.internal.pageSize.getHeight();
  const teal = [15, 118, 110];
  const dark = [15, 23, 42];
  const gris = [100, 116, 139];

  // --- Bandeau d'en-tete ---
  doc.setFillColor(teal[0], teal[1], teal[2]);
  doc.rect(0, 0, W, 74, "F");

  // Petit logo dessine (les trois barres ascendantes).
  doc.setFillColor(255, 255, 255);
  doc.roundedRect(40, 44, 6, 14, 2, 2, "F");
  doc.roundedRect(51, 37, 6, 21, 2, 2, "F");
  doc.roundedRect(62, 30, 6, 28, 2, 2, "F");

  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.text("OpportunitySN", 86, 42);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.text("Veille du marché de l'emploi Tech au Sénégal", 87, 57);

  // --- Sous-titre ---
  doc.setTextColor(dark[0], dark[1], dark[2]);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.text("Mes offres sélectionnées", 40, 104);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(gris[0], gris[1], gris[2]);
  const date = new Date().toLocaleDateString("fr-FR");
  doc.text(`${offres.length} offre(s) - exporté le ${date}`, 40, 118);

  // --- Table des offres ---
  autoTable(doc, {
    startY: 132,
    head: [["Poste", "Entreprise", "Ville", "Salaire (FCFA)", "Postuler"]],
    // (accents geres par jsPDF via l'encodage WinAnsi)
    body: offres.map((o) => [
      o.titre || "",
      o.entreprise || "",
      o.lieu || "",
      salaireTexte(o),
      o.url ? "Voir l'offre" : "n/d",
    ]),
    styles: { fontSize: 8, cellPadding: 5, overflow: "linebreak", valign: "middle" },
    headStyles: { fillColor: teal, textColor: 255, fontStyle: "bold" },
    alternateRowStyles: { fillColor: [241, 245, 249] },
    columnStyles: {
      0: { cellWidth: 145 },
      3: { halign: "right" },
      // La colonne "Postuler" est stylee comme un lien (teal, souligne).
      4: { textColor: teal, fontStyle: "bold" },
    },
    margin: { left: 40, right: 40 },
    // On rend la cellule "Postuler" reellement cliquable vers l'annonce.
    didDrawCell: (data) => {
      if (data.section === "body" && data.column.index === 4) {
        const offre = offres[data.row.index];
        if (offre && offre.url) {
          doc.link(data.cell.x, data.cell.y, data.cell.width, data.cell.height, {
            url: offre.url,
          });
        }
      }
    },
    didDrawPage: () => {
      const n = doc.internal.getNumberOfPages();
      doc.setFontSize(8);
      doc.setTextColor(gris[0], gris[1], gris[2]);
      doc.text("OpportunitySN - Papa Malick NDIAYE", 40, H - 20);
      doc.text(`Page ${n}`, W - 60, H - 20);
    },
  });

  doc.save(nomFichier);
}
