import re
from pathlib import Path
from collections import defaultdict
from pypdf import PdfReader


def clean_text(text: str) -> list[str]:
    """Zerlegt Text in normalisierte Kleinbuchstaben-Tokens (nur Wörter)."""
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
                word_to_pdfs[word].add(pdf_path.name)  # oder str(pdf_path) für den vollen Pfad

        except Exception as e:
            print(f"Fehler beim Verarbeiten von {pdf_path.name}: {e}")

    return word_to_pdfs


# # ==============================================================================
# # Ausführung & Suche
# # ==============================================================================
# if __name__ == "__main__":
#     # Pfad zum Ordner mit Ihren PDF-Dateien anpassen:
#     PDF_ORDNER = "/Users/s-kuemmel/Documents/WBS coding /Präsentationen/MeinePDFs"

#     # Index erstellen
#     index = index_pdfs(PDF_ORDNER)

#     print(f"\nIndizierung abgeschlossen. {len(index)} eindeutige Wörter katalogisiert.\n")

#     # Beispiel-Abfrage
#     suchbegriffe = ["vertrag", "rechnung", "python", "analyse"]

#     print("--- Test-Abfragen ---")
#     for begriff in suchbegriffe:
#         treffer = index.get(begriff.lower(), set())
#         if treffer:
#             print(f"Wort '{begriff}' gefunden in: {', '.join(treffer)}")
#         else:
#             print(f"Wort '{begriff}' kommt in keiner PDF vor.")
            
# ==============================================================================
# Ausführung & Interaktive Suche
# ==============================================================================
if __name__ == "__main__":
    # Pfad zum Ordner mit deinen PDF-Dateien
    PDF_ORDNER = "/Users/s-kuemmel/Documents/WBS coding /Präsentationen/MeinePDFs"

    # Index erstellen
    index = index_pdfs(PDF_ORDNER)
    print(f"\nIndizierung abgeschlossen. {len(index)} eindeutige Wörter katalogisiert.\n")

    # Interaktive Suchabfrage
    if index:
        print("--- Interaktive PDF-Suche gestartet ---")
        print("Gib ein Wort ein, um nach PDFs zu suchen. Tippe 'exit' zum Beenden.")
        
        while True:
            suchbegriff = input("\nSuchwort: ").strip().lower()
            
            if suchbegriff == 'exit':
                print("Suche beendet.")
                break
                
            if not suchbegriff:
                continue
                
            # Im Index nachschlagen
            treffer = index.get(suchbegriff)
            
            if treffer:
                print(f"Das Wort '{suchbegriff}' wurde in {len(treffer)} Datei(en) gefunden:")
                for dateiname in sorted(treffer):
                    print(f" 📄 {dateiname}")
            else:
                print(f"Das Wort '{suchbegriff}' wurde in keiner PDF gefunden.")
                
                
