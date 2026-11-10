import re
from pathlib import Path
from collections import defaultdict
from pypdf import PdfReader


def clean_text(text: str | list[str]) -> list[str]:
    """Zerlegt Text in normalisierte Kleinbuchstaben-Tokens (nur Wörter)."""
    if isinstance(text, list):
        text = " ".join(str(item) for item in text)
    # Findet alle zusammenhängenden Buchstaben-/Zahlenfolgen inklusive deutscher Umlaute
    return re.findall(r"\b[a-zäöüß0-9]+\b", text.lower())


def index_pdfs(folder_path: str) -> dict[str, set[str]]:
    """
    Liest alle PDFs rekursiv ein und ordnet jedem Wort die Pfade
    der Dokumente zu, in denen es vorkommt.
    """
    source_dir = Path(folder_path)

    # defaultdict(set) verhindert doppelte Dateieinträge für dasselbe Wort
    word_to_pdfs = defaultdict(set)
    pdf_files = list(source_dir.rglob("*.pdf"))

    print(f"Gefundene PDF-Dateien: {len(pdf_files)}")

    for pdf_path in pdf_files:
        try:
            reader = PdfReader(pdf_path)
            # Text aller Seiten im Dokument zusammenfügen
            full_text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += " " + page_text

            # Wörter extrahieren
            words = clean_text(full_text)

            # Jedes gefundene Wort mit dem aktuellen Dateinamen verknüpfen
            for word in words:
                word_to_pdfs[word].add(
                    pdf_path.name
                )  # oder str(pdf_path) für den vollen Pfad

        except Exception as e:
            print(f"Fehler beim Verarbeiten von {pdf_path.name}: {e}")

    return word_to_pdfs


def search_and(index: dict[str, set[str]], query: str) -> set[str] | None:
    """Findet alle PDFs, die ALLE Wörter der Anfrage enthalten."""
    # Wörter aus der Anfrage extrahieren
    query_words = clean_text(query)
    if not query_words:
        return None

    # Starte mit den Dokumenten des ersten Worts
    matching_pdfs = index.get(query_words[0], set()).copy()

    # Bilde die Schnittmenge (&) mit den Dokumenten aller weiteren Wörter
    for word in query_words[1:]:
        matching_pdfs &= index.get(word, set())
        # Wenn die Schnittmenge zwischendurch leer ist, gibt es keinen Treffer
        if not matching_pdfs:
            break

    return matching_pdfs


# ==============================================================================
# Ausführung & Suche
# ==============================================================================
if __name__ == "__main__":
    # Pfad zum Ordner mit Ihren PDF-Dateien anpassen:
    PDF_ORDNER = "./meine_pdfs"

    # Index erstellen
    index = index_pdfs(PDF_ORDNER)

    print(
        f"\nIndizierung abgeschlossen. {len(index)} eindeutige Wörter katalogisiert.\n"
    )

    # Suchabfrage (für ein oder mehrere Wörter)
    suchanfrage = input("Suchbegriff(e) eingeben: ")
    ergebnis = search_and(index, suchanfrage)

    if ergebnis is None:
        print("\nKein Suchbegriff eingegeben")
    elif ergebnis:
        print("\nGefundene PDFs:\n" + "\n".join(sorted(ergebnis)))
    else:
        print("\nKeine passende PDF gefunden.")
