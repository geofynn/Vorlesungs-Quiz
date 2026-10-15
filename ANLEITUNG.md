# Mehrspieler-Ziegenquiz

Das Quiz läuft vollständig im lokalen WLAN. Es braucht während der Veranstaltung kein Internet und installiert keine zusätzlichen Bibliotheken. Voraussetzung ist nur Python 3 auf dem Mini-PC.

## Vor der Veranstaltung testen

1. Den gesamten Ordner `Mehrspieler-Ziegenquiz` auf den Mini-PC kopieren.
2. Unter Windows `Quiz starten.bat` doppelt anklicken. Unter Linux oder auf einem Raspberry Pi im Ordner `python3 server.py` ausführen.
3. Beim ersten Start unter Windows den Netzwerkzugriff für **private Netzwerke** erlauben, falls die Firewall danach fragt.
4. Im Fenster erscheint eine Adresse wie `http://192.168.1.23:8000`. Diese Adresse auf zwei Handys öffnen, die mit demselben WLAN verbunden sind.
5. Auf beiden Geräten unterschiedliche Namen eingeben. Nun sollten beide Ziegen auf beiden Bildschirmen sichtbar sein.

## Am Freitag

1. Mini-PC und Geräte der Studierenden mit demselben WLAN verbinden. Alternativ kann der Mini-PC einen eigenen WLAN-Hotspot bereitstellen.
2. `Quiz starten.bat` starten und das schwarze Fenster während des Quiz geöffnet lassen.
3. Die angezeigte Adresse an die Studierenden geben, zum Beispiel `http://192.168.1.23:8000`.
4. Alle öffnen die Adresse im Browser und geben einen Anzeigenamen ein.

Bei der Namenswahl kann jede Person außerdem Fellfarbe und Accessoire ihrer Ziege auswählen. Die Gestaltung wird auf dem jeweiligen Gerät gespeichert und erscheint für alle Teilnehmenden am Berg.

Die Anzeige wird mehrmals pro Sekunde abgeglichen. Eine falsche Antwort setzt die betreffende Ziege auf Stufe 0 zurück, spielt die Fallanimation auch auf den anderen Geräten ab und startet für diese Person nach kurzer Pause wieder bei Frage 1. Personen, deren Browser länger als 30 Sekunden nicht mehr erreichbar ist, verschwinden automatisch vom Berg.

## Fragen ändern

`index.html` mit einem Texteditor öffnen. Der Fragenblock steht weit unten bei `const questions = [...]`. Für `correct` gilt:

- `0` = erste Antwort
- `1` = zweite Antwort
- `2` = dritte Antwort
- `3` = vierte Antwort

Die Zahl der Fragen darf geändert werden. Alle Browser verwenden automatisch die neue Zahl als Gipfelhöhe. Nach Änderungen den Server neu starten und die Seite auf den Geräten neu laden.

## Falls die Adresse nicht erreichbar ist

- Prüfen, ob alle Geräte wirklich im selben WLAN sind.
- Unter Windows das Netzwerk als **privat** einstellen und Python in der Firewall für private Netzwerke zulassen.
- Manche Gast-WLANs blockieren Verbindungen zwischen Teilnehmergeräten. In diesem Fall einen normalen Router oder den Hotspot des Mini-PCs verwenden.
- Mit `ipconfig` unter Windows beziehungsweise `hostname -I` unter Linux lässt sich die aktuelle IPv4-Adresse des Mini-PCs prüfen. Danach `:8000` anhängen.
- Falls Port 8000 belegt ist, kann der Server mit `python server.py --port 8080` auf einem anderen Port gestartet werden.

## Technischer Hinweis

Der Server speichert Namen und Spielstände nur im Arbeitsspeicher. Beim Beenden des Serverfensters werden alle Stände gelöscht. Das ist für die Veranstaltung beabsichtigt und es werden keine Daten in eine Cloud übertragen.
