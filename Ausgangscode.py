# ==============================================================================
# 1. IMPORTE (Benötigte Module & Bibliotheken laden)
# ==============================================================================
import re  # Modul für "Regular Expressions" (Reguläre Ausdrücke) zur Textsuche/-filterung
from pathlib import Path  # Modernes Modul zum einfachen Arbeiten mit Datei- und Ordnerpfaden
from collections import defaultdict  # Spezielles Dictionary, das automatisch Standardwerte anlegt
from pypdf import PdfReader  # Externe Bibliothek zum Öffnen und Auslesen von PDF-Dateien


# ==============================================================================
# 2. HILFSFUNKTION: TEXT BEREINIGEN & IN WÖRTER ZERLEGEN
# ==============================================================================
def clean_text(text: str) -> list[str]:
    """
    Zerlegt einen beliebigen Text in eine Liste einzelner, kleingeschriebener Wörter (Tokens).
    Satzzeichen und Sonderzeichen werden dabei automatisch herausgefiltert.

    Parameter:
        text (str): Der Rohtext aus einer PDF-Datei.
    Rückgabe:
        list[str]: Liste aller gefundenen Wörter in Kleinbuchstaben.
    """
    # 1. text.lower() wandelt den gesamten Text in Kleinbuchstaben um, damit die Suche
    #    später unabhängig von Groß- und Kleinschreibung funktioniert ("Tomate" == "tomate").
    # 2. re.findall(...) sucht im Text nach allen Treffern, die zum Muster passen:
    #    - r"..."       : Raw-String (Backslashes werden direkt an Regex übergeben)
    #    - \b           : Wortgrenze (stellt sicher, dass nur ganze Wörter erkannt werden)
    #    - [a-zäöüß0-9]+: Mindestens ein (+) Zeichen aus den Buchstaben a-z, Umlauten (äöüß) oder Ziffern (0-9)
    return re.findall(r"\b[a-zäöüß0-9]+\b", text.lower())


# ==============================================================================
# 3. HAUPTFUNKTION: PDF-DATEIEN EINLESEN & SUCHINDEX AUFBAUEN
# ==============================================================================
def index_pdfs(folder_path: str) -> dict[str, set[str]]:
    """
    Liest alle PDF-Dateien im angegebenen Ordner (inkl. Unterordner) ein und baut
    einen sogenannten "Invertierten Index" auf.
    Jedem Wort wird die Menge (set) aller Dateinamen zugeordnet, in denen es vorkommt.

    Parameter:
        folder_path (str): Pfad zum Ordner mit den PDF-Dokumenten.
    Rückgabe:
        dict[str, set[str]]: Wörterbuch im Format {"wort": {"Rezept_1.pdf", "Rezept_4.pdf"}}
    """
    # Wandelt den Text-Pfad (String) in ein Path-Objekt um, mit dem man leicht nach Dateien suchen kann
    source_dir = Path(folder_path)

    # defaultdict(set) erstellt ein Dictionary, bei dem jeder neue Schlüssel (jedes neue Wort)
    # automatisch ein leeres Set (Menge) als Startwert bekommt.
    # Vorteil eines Sets: Jede PDF-Datei wird pro Wort maximal einmal gespeichert (keine Duplikate),
    # auch wenn das Wort im selben Rezept mehrfach vorkommt.
    word_to_pdfs = defaultdict(set)

    # .rglob("*.pdf") durchsucht den Ordner (und alle Unterordner) nach Dateien, die auf ".pdf" enden.
    # list(...) macht daraus eine feste Liste aller gefundenen PDF-Pfade.
    pdf_files = list(source_dir.rglob("*.pdf"))

    print(f"Gefundene PDF-Dateien: {len(pdf_files)}")

    # Schleife über jede einzelne gefundene PDF-Datei
    for pdf_path in pdf_files:
        # try-except-Block: Fängt Fehler ab (z. B. falls eine PDF beschädigt ist),
        # damit das Programm nicht komplett abstürzt, sondern mit der nächsten PDF weitermacht.
        try:
            # Öffnet die aktuelle PDF-Datei mit dem PdfReader
            reader = PdfReader(pdf_path)

            # Variable für den gesamten Text dieser PDF-Datei (startet als leerer String)
            full_text = ""

            # Jede Seite der PDF einzeln durchgehen und den Text auslesen
            for page in reader.pages:
                page_text = page.extract_text()  # Text der aktuellen Seite extrahieren
                if page_text:  # Prüfen, ob auf der Seite überhaupt Text gefunden wurde
                    full_text += " " + page_text  # Seitentext mit Leerzeichen an den Gesamttext anhängen

            # Den gesammelten Text der PDF mithilfe unserer Funktion in einzelne Wörter zerlegen
            words = clean_text(full_text)

            # Jedes gefundene Wort im Index eintragen und mit dem Dateinamen der PDF verknüpfen
            for word in words:
                # .add() fügt den Dateinamen (pdf_path.name, z. B. "Rezept_1_Tomatensuppe.pdf")
                # zur Menge (Set) dieses Wortes hinzu.
                word_to_pdfs[word].add(
                    pdf_path.name
                )  # Alternativ: str(pdf_path) für den kompletten Dateipfad

        except Exception as e:
            # Falls beim Lesen einer Datei ein Fehler auftritt, wird eine Meldung ausgegeben
            print(f"Fehler beim Verarbeiten von {pdf_path.name}: {e}")

    # Gibt den fertig aufgebauten Wort-Index zurück
    return word_to_pdfs


# ==============================================================================
# 4. PROGRAMMSTART: AUSFÜHRUNG & BEISPIEL-SUCHE
# ==============================================================================
# Dieser Block wird nur ausgeführt, wenn die Datei direkt gestartet wird
# (und nicht, wenn sie als Modul in eine andere Python-Datei importiert wird).
if __name__ == "__main__":
    # Pfad zum Ordner, in dem die Rezept-PDFs gespeichert sind:
    PDF_ORDNER = "/Users/manus./Documents/WBS_Coding_School/My_Project/Gruppenarbeit_Suchmaschine/Rezepteordner"

    # 1. Schritt: Einmalig beim Start den Suchindex über alle PDFs aufbauen
    index = index_pdfs(PDF_ORDNER)

    # len(index) zeigt, wie viele unterschiedliche Wörter insgesamt in allen PDFs gefunden wurden
    print(
        f"\nIndizierung abgeschlossen. {len(index)} eindeutige Wörter katalogisiert.\n"
    )

    # 2. Schritt: Liste mit Beispiel-Suchbegriffen zum Testen des Index
    suchbegriffe = ["Tomate", "Knoblauch", "Pasta", "Hafer"]

    print("--- Test-Abfragen ---")
    # Jeden Suchbegriff nacheinander im Index nachschlagen
    for begriff in suchbegriffe:
        # begriff.lower() sorgt dafür, dass auch großgeschriebene Suchbegriffe (wie "Tomate")
        # im kleingeschriebenen Index ("tomate") gefunden werden.
        # index.get(..., set()) gibt die Menge der passenden PDFs zurück – oder ein leeres Set,
        # falls das Wort in keiner einzigen PDF vorkommt.
        treffer = index.get(begriff.lower(), set())

        # Prüfen, ob mindestens eine PDF-Datei für den Begriff gefunden wurde
        if treffer:
            # ', '.join(treffer) verbindet alle gefundenen Dateinamen schön mit Komma getrennt
            print(f"Wort '{begriff}' gefunden in: {', '.join(treffer)}")
        else:
            # Hinweis ausgeben, wenn die Menge (treffer) leer ist
            print(f"Wort '{begriff}' kommt in keiner PDF vor.")
