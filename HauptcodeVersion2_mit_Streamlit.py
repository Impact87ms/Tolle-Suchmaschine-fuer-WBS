# ==============================================================================
# 1. IMPORTE (Benötigte Module & Bibliotheken laden)
# ==============================================================================
import re  # Modul für "Regular Expressions" (Reguläre Ausdrücke) zur Textsuche/-filterung
from pathlib import Path  # Modernes Modul zum einfachen Arbeiten mit Datei- und Ordnerpfaden
from collections import defaultdict  # Spezielles Dictionary, das automatisch Standardwerte anlegt
from pypdf import PdfReader  # Externe Bibliothek zum Öffnen und Auslesen von PDF-Dateien
import streamlit as st  # Framework zum Erstellen der interaktiven Weboberfläche im Browser


# ==============================================================================
# 2. HILFSFUNKTION: TEXT BEREINIGEN & IN WÖRTER ZERLEGEN (FR002)
# ==============================================================================
def clean_text(text: str) -> list[str]:
    """
    Zerlegt einen beliebigen Text in eine Liste einzelner, kleingeschriebener Wörter (Tokens).
    Satzzeichen und Sonderzeichen werden dabei automatisch herausgefiltert.

    Parameter:
        text (str): Der Rohtext aus einer PDF-Datei oder der Suchanfrage.
    Rückgabe:
        list[str]: Liste aller gefundenen Wörter in Kleinbuchstaben.
    """
    # 1. text.lower() wandelt den gesamten Text in Kleinbuchstaben um, damit die Suche
    #    später unabhängig von Groß- und Kleinschreibung funktioniert ("Tomate" == "tomate").
    # 2. re.findall(...) sucht im Text nach allen Treffern, die zum Muster passen:
    #    - r"..."       : Raw-String (Backslashes werden direkt an Regex übergeben)
    #    - \b           : Wortgrenze (stellt sicher, dass nur ganze Wörter erkannt werden)
    #    - [a-zäöüß0-9]+: Mindestens ein (+) Zeichen aus Buchstaben a-z, Umlauten (äöüß) oder Ziffern (0-9)
    return re.findall(r"\b[a-zäöüß0-9]+\b", text.lower())


# ==============================================================================
# 3. HAUPTFUNKTION: PDF-DATEIEN EINLESEN & SUCHINDEX AUFBAUEN (FR001 & FR003)
# ==============================================================================
# @st.cache_data sorgt dafür, dass Streamlit die PDFs nur EINMAL beim Start einliest
# und das Ergebnis im Speicher behält (erfüllt FR003: Index einmalig beim Start aufbauen).
@st.cache_data
def index_pdfs(folder_path: str) -> tuple[dict[str, set[str]], dict[str, str]]:
    """
    Liest alle PDF-Dateien im angegebenen Ordner ein und baut einen "Invertierten Index" auf.
    Jedem Wort wird die Menge (set) aller Dateinamen zugeordnet, in denen es vorkommt.
    Zusätzlich wird der Volltext jeder PDF gespeichert, um ihn im Browser anzeigen zu können.

    Parameter:
        folder_path (str): Pfad zum Ordner mit den PDF-Dokumenten.
    Rückgabe:
        tuple:
            - dict[str, set[str]]: Wort-Index im Format {"wort": {"Rezept_1.pdf", ...}}
            - dict[str, str]: Volltexte der PDFs im Format {"Rezept_1.pdf": "Schnelle Tomatensuppe ..."}
    """
    source_dir = Path(folder_path)

    # defaultdict(set) erstellt ein Dictionary, bei dem jedes neue Wort automatisch
    # ein leeres Set (Menge) als Startwert bekommt (verhindert doppelte Dateieinträge).
    word_to_pdfs = defaultdict(set)

    # Speichert zusätzlich den lesbaren Text jeder PDF für die Vorschau in Streamlit
    pdf_texts = {}

    # Alle PDF-Dateien im Ordner (und Unterordnern) alphabetisch sortiert suchen
    pdf_files = sorted(source_dir.rglob("*.pdf"))

    for pdf_path in pdf_files:
        try:
            reader = PdfReader(pdf_path)
            full_text = ""

            # Jede Seite der PDF einzeln durchgehen und den Text auslesen
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += " " + page_text

            # Volltext für die spätere Anzeige im Browser speichern
            pdf_texts[pdf_path.name] = full_text.strip()

            # Text in einzelne Wörter zerlegen und im Index verknüpfen
            words = clean_text(full_text)
            for word in words:
                word_to_pdfs[word].add(pdf_path.name)

        except Exception as e:
            st.warning(f"Fehler beim Verarbeiten von {pdf_path.name}: {e}")

    # defaultdict in ein normales dict umwandeln, damit Streamlit es problemlos cachen kann
    return dict(word_to_pdfs), pdf_texts


# ==============================================================================
# 4. SUCHFUNKTIONEN: MEHRERE SUCHWÖRTER KOMBINIEREN (ODER / UND - FR004)
# ==============================================================================
def search_or(index: dict[str, set[str]], query: str) -> set[str]:
    """
    ODER-Suche (Vereinigungsmenge):
    Findet alle PDFs, die MINDESTENS EINES der eingegebenen Suchwörter enthalten.
    """
    # Bindewörter ("und", "oder") bei der Suche ignorieren
    stop_words = {"und", "oder"}
    query_words = [w for w in clean_text(query) if w not in stop_words]

    if not query_words:
        return set()

    # Vereinigungsmenge (|=): Sammelt alle PDFs, in denen mindestens ein Suchwort vorkommt
    matching_pdfs = set()
    for word in query_words:
        matching_pdfs |= index.get(word, set())

    return matching_pdfs


def search_and(index: dict[str, set[str]], query: str) -> set[str]:
    """
    UND-Suche (Schnittmenge):
    Findet nur die PDFs, in denen ALLE eingegebenen Suchwörter GLEICHZEITIG vorkommen.
    """
    stop_words = {"und", "oder"}
    query_words = [w for w in clean_text(query) if w not in stop_words]

    if not query_words:
        return set()

    # Starte mit einer Kopie (.copy()) der PDF-Menge des ersten Suchworts
    matching_pdfs = index.get(query_words[0], set()).copy()

    # Schnittmenge (&=): Behalte nur PDFs, die auch alle weiteren Suchwörter enthalten
    for word in query_words[1:]:
        matching_pdfs &= index.get(word, set())
        if not matching_pdfs:
            break

    return matching_pdfs


# ==============================================================================
# 5. STREAMLIT-WEBOBERFLÄCHE (AUSFÜHRUNG IM BROWSER - FR005, FR006, FR007)
# ==============================================================================
# Grundeinstellungen für den Browser-Tab (Titel und Icon)
st.set_page_config(page_title="Rezept-Suchmaschine", page_icon="🍲", layout="centered")

# Überschrift und kurze Erklärung auf der Webseite
st.title("🍲 PDF-Rezept-Suchmaschine")
st.write(
    "Gib ein oder mehrere Suchwörter ein (z. B. `Tomaten Knoblauch` oder `Butter Milch`), "
    "um alle passenden Rezepte zu durchsuchen."
)

# Pfad zum Rezepteordner automatisch relativ zu dieser Python-Datei bestimmen
PDF_ORDNER = str(Path(__file__).parent / "Rezepteordner")

# 1. Schritt: Suchindex einmalig beim Start laden
index, pdf_texts = index_pdfs(PDF_ORDNER)

# Status-Anzeige in der Seitenleiste (oder oben als Info-Box)
st.caption(
    f"📚 **{len(pdf_texts)} PDF-Rezepte** geladen | "
    f"🔤 **{len(index)} eindeutige Wörter** im Suchindex katalogisiert"
)

# 2. Schritt: Eingabefeld für die Suchanfrage (erlaubt beliebig viele Suchen hintereinander - FR007)
anfrage = st.text_input(
    "🔍 Suchwörter eingeben:",
    placeholder="z. B. Tomaten Knoblauch ...",
)

# Wenn der Nutzer etwas in das Suchfeld eingetippt hat (oder Enter gedrückt hat):
if anfrage != "":
    # Suchbegriffe bereinigen und Bindewörter ("und"/"oder") herausfiltern
    suchbegriffe = [w for w in clean_text(anfrage) if w not in {"und", "oder"}]

    # Leere Eingaben oder reine Sonderzeichen/Leerzeichen abfangen (erfüllt FR006)
    if not suchbegriffe:
        st.warning("Hinweis: Bitte gib mindestens ein gültiges Suchwort ein.")
    else:
        st.divider()

        # --- A) EINZELWORT-ABFRAGEN ---
        st.subheader("1️⃣ Einzelwort-Abfragen")
        for begriff in suchbegriffe:
            treffer = sorted(index.get(begriff, set()))
            if treffer:
                st.success(f"Wort **`'{begriff}'`** gefunden in: {', '.join(treffer)}")
            else:
                st.error(f"Wort **`'{begriff}'`** kommt in keiner PDF vor.")

        # --- B) ODER-SUCHE (MINDESTENS EIN SUCHWORT ENTHALTEN) ---
        ergebnis_oder = sorted(search_or(index, anfrage))
        st.subheader(
            f"2️⃣ Gefundene Rezepte insgesamt – ODER-Suche ({len(ergebnis_oder)} Treffer)"
        )
        if ergebnis_oder:
            for dateiname in ergebnis_oder:
                # Jedes gefundene Rezept als aufklappbare Box anzeigen
                with st.expander(f"📄 {dateiname}"):
                    st.text(pdf_texts.get(dateiname, ""))
        else:
            st.info("Keine passende PDF gefunden.")

        # --- C) UND-SUCHE (ALLE SUCHWÖRTER GLEICHZEITIG ENTHALTEN - FR004 & FR005) ---
        ergebnis_und = sorted(search_and(index, anfrage))
        st.subheader(
            f"3️⃣ Rezepte mit ALLEN Suchwörtern gleichzeitig – UND-Suche ({len(ergebnis_und)} Treffer)"
        )
        if ergebnis_und:
            for dateiname in ergebnis_und:
                with st.expander(f"✅ {dateiname}"):
                    st.text(pdf_texts.get(dateiname, ""))
        else:
            st.info("Keine PDF enthält alle gesuchten Wörter gleichzeitig.")
