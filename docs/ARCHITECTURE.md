# Architecture et choix techniques

Ce document explique le "pourquoi" derriere le projet. Le "comment" fichier par
fichier est dans `ARCHITECTURE_FICHIERS.txt` a la racine.

## L'idee de depart

Je voulais un projet qui ressemble a ce qu'on fait vraiment en entreprise :
pas un notebook Jupyter isole, mais une vraie pipeline de bout en bout, qui
tourne toute seule et qui produit quelque chose d'utile pour un decideur.

Le fil rouge : de la donnee brute vers une decision. On scrape, on nettoie, on
analyse, on alerte. Chaque etape a sa couche, et les couches sont independantes.

## Une architecture en couches

J'ai decoupe le projet en 5 couches. Chacune a une seule responsabilite :

1. **Scraping** : recuperer les offres. Ne sait rien du reste.
2. **Pipeline (ETL)** : nettoyer, valider, stocker.
3. **Analyse** : detecter anomalies et tendances.
4. **Notification** : diffuser (email, webhook Make).
5. **Dashboard** : afficher.

Pourquoi ce decoupage ? Parce qu'on peut changer une couche sans toucher aux
autres. Envie de passer de SQLite a PostgreSQL ? On change une ligne dans la
couche stockage. Envie d'ajouter Indeed comme source ? On cree un nouveau
scraper, le reste ne bouge pas.

## Le patron "Template Method" pour les scrapers

Tous les scrapers heritent de `BaseScraper`. La classe mere gere le code
commun et penible : les requetes HTTP, les retries, le respect du `robots.txt`,
le delai entre requetes. Chaque scraper enfant n'implemente qu'une methode :
`parse()`.

Resultat concret : ajouter une source prend quelques lignes, sans copier-coller
la gestion d'erreur a chaque fois. C'est un patron de conception classique et
il colle parfaitement au probleme.

## La validation avant tout : Pydantic

Le web est sale. Une offre peut arriver sans titre, avec un salaire negatif, ou
un min superieur au max. Plutot que de gerer ces cas partout, je les gere une
seule fois : a l'entree, dans la couche validation.

Chaque offre passe par un schema Pydantic. Ce qui est recuperable est corrige
(salaire inverse remis dans l'ordre), ce qui est inutilisable est rejete et
loggue. Apres cette etape, je sais que toutes mes donnees ont la meme forme.
Tout le code en aval devient plus simple.

## La detection d'anomalies : Z-score + IQR

Pour reperer les salaires anormaux, j'utilise deux methodes statistiques
complementaires :

- **Z-score** : mesure de combien d'ecarts-types une valeur s'eloigne de la
  moyenne. Simple, mais sensible aux valeurs extremes.
- **IQR (ecart interquartile)** : basee sur les quartiles, la meme logique que
  le boxplot. Plus robuste quand la distribution n'est pas symetrique.

Je calcule tout **par categorie de metier**, car un salaire normal pour un Data
Engineer n'a rien a voir avec celui d'un comptable junior. Une offre est
signalee si au moins une des deux methodes la detecte. Croiser les deux limite
les faux negatifs.

## Code + no-code : le pont Make

Le point que je trouve le plus interessant cote "vraie vie" : la pipeline Python
envoie ses alertes a un webhook Make. Ensuite, Make s'occupe de router vers
Slack, Google Sheets ou WhatsApp, sans que j'ecrive une ligne de code pour
chaque canal.

C'est exactement la facon de faire en entreprise : le code fait le travail lourd
et fiable, l'outil no-code gere la distribution et les integrations metier. Ca
me permet aussi d'ajouter un nouveau canal en 2 minutes cote Make.

## Pourquoi une source de demonstration

Les sites d'emploi changent leur HTML, bloquent les robots, ou demandent un
login. Si mon projet dependait a 100% d'un site externe, il pourrait tomber en
panne du jour au lendemain, y compris en pleine demo d'entretien.

J'ai donc ajoute un `demo_scraper` qui genere un jeu de donnees realiste du
marche senegalais. Ce n'est pas de la triche : c'est une source parmi d'autres,
qui garantit que toute la chaine (ETL, analyse, dashboard) est toujours
demontrable. Les vrais scrapers HTML restent la et fonctionnent.

## Observabilite : logging partout

Pas de `print()`. Un vrai logger, configure une fois, ecrit a la fois dans la
console et dans un fichier avec rotation. Quand quelque chose casse en prod, je
peux relire les logs et comprendre. C'est un reflexe "ops" que je voulais avoir.

## Ce que je ferais avec plus de temps

- Ajouter 2 ou 3 vraies sources supplementaires avec Scrapy.
- Un modele simple de prediction de salaire par competences.
- Un historique versionne pour comparer semaine apres semaine.
- Des tests d'integration en plus des tests unitaires.
