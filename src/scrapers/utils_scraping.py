"""
Petites fonctions utilitaires pour le scraping.

On y met tout ce qui est reutilisable par plusieurs scrapers :
nettoyage de texte, extraction de salaire, verification du robots.txt, etc.
Garder ca a part evite de dupliquer le meme code dans chaque scraper.
"""

import html
import json
import re
import urllib.robotparser
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.logger import get_logger

logger = get_logger(__name__)


def _chercher_jobposting(noeud):
    """
    Cherche recursivement un objet de @type "JobPosting" dans une structure
    JSON-LD. Certains sites le mettent au premier niveau, d'autres l'imbriquent
    (dans "@graph", ou comme "mainEntity" d'une ItemPage). On explore donc tout.
    """
    if isinstance(noeud, dict):
        type_ = noeud.get("@type")
        if type_ == "JobPosting" or (isinstance(type_, list) and "JobPosting" in type_):
            return noeud
        for valeur in noeud.values():
            trouve = _chercher_jobposting(valeur)
            if trouve:
                return trouve
    elif isinstance(noeud, list):
        for item in noeud:
            trouve = _chercher_jobposting(item)
            if trouve:
                return trouve
    return None


def extraire_json_ld_jobposting(html_page):
    """
    Extrait le JSON-LD de type JobPosting d'une page HTML (meme imbrique).

    Beaucoup de sites d'emploi embarquent les donnees de l'offre dans un
    <script type="application/ld+json"> normalise selon schema.org. C'est bien
    plus stable que de parser le HTML a la main : les champs (titre, lieu, date)
    sont deja structures. Renvoie le dict JobPosting, ou None si absent.
    """
    if not html_page:
        return None
    soup = BeautifulSoup(html_page, "lxml")
    for bloc in soup.find_all("script", type="application/ld+json"):
        try:
            donnees = json.loads(bloc.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        trouve = _chercher_jobposting(donnees)
        if trouve:
            return trouve
    return None


def nettoyer_html(brut):
    """
    Transforme un morceau de HTML en texte simple et lisible.

    Les API de jobs renvoient souvent la description en HTML (<strong>, <br>,
    entites comme &amp;). On enleve les balises et on decode les entites pour
    obtenir du texte propre, exploitable par extraire_competences/salaire.
    """
    if not brut:
        return ""
    # On remplace les balises par un espace (evite de coller deux mots).
    decode = re.sub(r"<[^>]+>", " ", brut)
    # On decode les entites HTML (&amp; -> &, &#8211; -> tiret...). Certains
    # sites double-encodent (&amp;#8211;), donc on repete jusqu'a stabilite.
    for _ in range(3):
        suivant = html.unescape(decode)
        if suivant == decode:
            break
        decode = suivant
    return nettoyer_texte(decode)


def nettoyer_texte(texte):
    """
    Nettoie une chaine de caracteres recuperee sur le web.

    On enleve les espaces en trop, les retours a la ligne et les
    caracteres invisibles. Simple mais indispensable, le HTML est
    souvent sale.
    """
    if not texte:
        return ""
    texte = re.sub(r"\s+", " ", texte)
    return texte.strip()


def extraire_salaire(texte):
    """
    Essaie de sortir une fourchette de salaire d'un texte libre.

    Exemples geres :
        "500 000 - 800 000 FCFA"  -> (500000, 800000)
        "Salaire : 1 200 000 CFA" -> (1200000, 1200000)
        "A negocier"              -> (None, None)

    Retourne un tuple (mini, maxi). None quand on ne trouve rien,
    on ne veut surtout pas inventer une valeur.
    """
    if not texte:
        return (None, None)

    # On retire les espaces a l'interieur des nombres (1 200 000 -> 1200000).
    texte_propre = re.sub(r"(?<=\d)\s+(?=\d)", "", texte)
    nombres = re.findall(r"\d{4,}", texte_propre)  # au moins 4 chiffres = un vrai salaire
    nombres = [int(n) for n in nombres]

    if not nombres:
        return (None, None)
    if len(nombres) == 1:
        return (nombres[0], nombres[0])
    return (min(nombres), max(nombres))


def extraire_competences(texte, dictionnaire):
    """
    Detecte les competences citees dans un texte a partir d'un dictionnaire.

    On cherche chaque mot-cle (Python, SQL, Docker...) dans le texte.
    C'est volontairement simple : pas de NLP avance, juste du matching,
    ce qui suffit largement pour une premiere veille.
    """
    if not texte:
        return []
    texte_bas = texte.lower()
    trouvees = []
    for competence in dictionnaire:
        # \b = frontiere de mot, pour eviter que "r" matche dans "recruteur".
        if re.search(r"\b" + re.escape(competence.lower()) + r"\b", texte_bas):
            trouvees.append(competence)
    return trouvees


def est_offre_tech(texte, indicateurs):
    """
    Dit si un texte (titre + tags) correspond a un poste Tech.

    Sert a filtrer les API generalistes qui melangent tous les metiers. On
    cherche un simple mot-cle de la liste d'indicateurs. Volontairement basique,
    mais suffisant pour ecarter les postes de vente, RH, beaute, etc.
    """
    if not texte:
        return False
    bas = texte.lower()
    return any(mot in bas for mot in indicateurs)


def robots_autorise(url, user_agent):
    """
    Verifie que le robots.txt du site autorise le scraping de cette URL.

    C'est une question d'ethique et de respect des regles du site.
    Si on n'arrive pas a lire le robots.txt, on reste prudent mais on
    laisse passer (beaucoup de petits sites n'en ont pas).
    """
    try:
        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{base}/robots.txt")
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:  # noqa: BLE001
        logger.warning("Impossible de lire le robots.txt de %s (%s). On continue.", url, e)
        return True
