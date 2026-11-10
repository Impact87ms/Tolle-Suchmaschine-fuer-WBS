# ==============================================================================
# 1. IMPORTE (Benötigte Module & Bibliotheken laden)
# ==============================================================================
import re  # Modul für "Regular Expressions" (Reguläre Ausdrücke) zur Textsuche/-filterung
from pathlib import (
    Path,
)  # Modernes Modul zum einfachen Arbeiten mit Datei- und Ordnerpfaden
from collections import (
    defaultdict,
)  # Spezielles Dictionary, das automatisch Standardwerte anlegt
from pypdf import (
    PdfReader,
)  # Externe Bibliothek zum Öffnen und Auslesen von PDF-Dateien


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
                    full_text += (
                        " " + page_text
                    )  # Seitentext mit Leerzeichen an den Gesamttext anhängen

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
# 4. SUCHFUNKTIONEN: MEHRERE SUCHWÖRTER KOMBINIEREN (ODER / UND)
# ==============================================================================
def search_or(index: dict[str, set[str]], query: str) -> set[str]:
    """
    ODER-Suche (Vereinigungsmenge):
    Findet alle PDFs, die MINDESTENS EINES der eingegebenen Suchwörter enthalten.
    Beispiel: Bei "Tomaten Knoblauch" werden alle Rezepte mit Tomaten PLUS alle
    Rezepte mit Knoblauch zurückgegeben.

    Parameter:
        index (dict[str, set[str]]): Der zuvor aufgebaute Wort-Index.
        query (str): Die gesamte Benutzereingabe (z. B. "Tomaten und Knoblauch").
    Rückgabe:
        set[str]: Menge aller passenden PDF-Dateinamen (ohne Duplikate).
    """
    # Füllwörter ("und", "oder") definieren, die bei der Suche ignoriert werden sollen,
    # falls der Nutzer z. B. "Tomaten und Knoblauch" eintippt.
    stop_words = {"und", "oder"}

    # 1. clean_text(query) zerlegt die Eingabe in einzelne, kleingeschriebene Wörter.
    # 2. Die List Comprehension [w for w in ... if w not in stop_words] filtert "und"/"oder" heraus.
    query_words = [w for w in clean_text(query) if w not in stop_words]

    # Falls die Eingabe leer war (oder nur aus Leerzeichen/Sonderzeichen bestand),
    # geben wir sofort ein leeres Set (keine Treffer) zurück.
    if not query_words:
        return set()

    # Leeres Set erstellen, in dem wir alle gefundenen PDF-Dateinamen sammeln
    matching_pdfs = set()

    # Jedes Suchwort einzeln im Index nachschlagen
    for word in query_words:
        # Der Operator |= bildet die Vereinigungsmenge (Union) zweier Sets:
        # Alle PDFs, in denen das aktuelle Wort vorkommt, werden zu matching_pdfs hinzugefügt.
        # Da matching_pdfs ein Set ist, kommt jede PDF-Datei darin trotzdem nur maximal einmal vor.
        matching_pdfs |= index.get(word, set())

    return matching_pdfs


def search_and(index: dict[str, set[str]], query: str) -> set[str]:
    """
    UND-Suche (Schnittmenge):
    Findet nur die PDFs, in denen ALLE eingegebenen Suchwörter GLEICHZEITIG vorkommen.
    Beispiel: Bei "Tomaten Knoblauch" wird nur ein Rezept zurückgegeben, wenn
    sowohl "Tomaten" als auch "Knoblauch" im selben Rezept stehen.

    Parameter:
        index (dict[str, set[str]]): Der zuvor aufgebaute Wort-Index.
        query (str): Die gesamte Benutzereingabe (z. B. "Tomaten Knoblauch").
    Rückgabe:
        set[str]: Menge der PDF-Dateinamen, die alle Suchwörter enthalten.
    """
    # Bindewörter wie "und" / "oder" aus der Suchanfrage herausfiltern
    stop_words = {"und", "oder"}
    query_words = [w for w in clean_text(query) if w not in stop_words]

    # Bei leerer Anfrage sofort ein leeres Set zurückgeben
    if not query_words:
        return set()

    # Wir starten mit den PDF-Dateien des allerersten Suchworts (query_words[0]).
    # WICHTIG: .copy() erstellt eine Kopie des Sets, damit wir nicht aus Versehen
    # den Original-Index verändern, wenn wir gleich Elemente daraus filtern!
    matching_pdfs = index.get(query_words[0], set()).copy()

    # Jetzt gehen wir alle weiteren Suchwörter ab dem zweiten Wort (query_words[1:]) durch
    for word in query_words[1:]:
        # Der Operator &= bildet die Schnittmenge (Intersection) zweier Sets:
        # Es bleiben in matching_pdfs nur die PDFs übrig, die AUCH beim aktuellen Wort vorkommen.
        matching_pdfs &= index.get(word, set())

        # Vorzeitiger Abbruch (Optimierung): Wenn die Schnittmenge bereits leer ist,
        # kann auch mit weiteren Wörtern kein gemeinsamer Treffer mehr entstehen.
        if not matching_pdfs:
            break

    return matching_pdfs


# ==============================================================================
# 5. PROGRAMMSTART: AUSFÜHRUNG & BENUTZERABFRAGE
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

    # 2. Schritt: Benutzereingabe im Terminal abfragen (ein oder mehrere Wörter möglich)
    anfrage = input("Suchwörter eingeben (z. B. Tomaten Knoblauch): ")

    # Zerlegt die Eingabe in einzelne, kleingeschriebene Suchwörter (ohne "und"/"oder")
    suchbegriffe = [w for w in clean_text(anfrage) if w not in {"und", "oder"}]

    print("\n--- Einzelwort-Abfragen ---")
    # Jeden eingegebenen Suchbegriff einzeln im Index nachschlagen und ausgeben
    for begriff in suchbegriffe:
        # index.get(begriff, set()) sucht das Wort im Index; falls es nicht existiert,
        # wird ein leeres Set zurückgegeben (verhindert einen KeyError-Absturz).
        treffer = index.get(begriff, set())

        # Prüfen, ob mindestens eine PDF-Datei für diesen einzelnen Begriff gefunden wurde
        if treffer:
            # sorted(treffer) sortiert die Dateinamen alphabetisch,
            # ', '.join(...) verbindet sie zu einem lesbaren Text mit Kommas.
            print(f"Wort '{begriff}' gefunden in: {', '.join(sorted(treffer))}")
        else:
            print(f"Wort '{begriff}' kommt in keiner PDF vor.")

    # 3. Schritt: ODER-Suche (alle Rezepte, die mindestens eines der Suchwörter enthalten)
    # sorted(...) macht aus dem Ergebnis-Set eine alphabetisch sortierte Liste.
    ergebnis_oder = sorted(search_or(index, anfrage))
    print(f"\n--- Gefundene Rezepte insgesamt ({len(ergebnis_oder)} Treffer) ---")
    if ergebnis_oder:
        # "\n".join(...) gibt jeden gefundenen Dateinamen in einer eigenen Zeile aus
        print("\n".join(ergebnis_oder))
    else:
        print("Keine passende PDF gefunden.")

    # 4. Schritt: UND-Suche (nur Rezepte, die ALLE Suchwörter gleichzeitig enthalten)
    ergebnis_und = sorted(search_and(index, anfrage))
    print(
        f"\n--- Rezepte, die ALLE Suchwörter gleichzeitig enthalten ({len(ergebnis_und)} Treffer) ---"
    )
    if ergebnis_und:
        print("\n".join(ergebnis_und))
    else:
        print("Keine PDF enthält alle gesuchten Wörter gleichzeitig.")
