# Mastodon-Feed zu Podcast-Feed Konverter

Konvertiert Mastodon RSS-Feeds in Podcast-kompatible RSS-Feeds für Podcatcher wie Apple Podcasts, Spotify, etc.
Mastodon erlaubt das Hochladen von Audio-Dateien und generiert sowohl für Einzelaccounts als auch für Hashtags RSS-Feeds. Was noch fehlt, um den RSS-Feed mit Audio-Files kompatibel zu Podcasts zu machen, so dass der Feed in einem Podcatcher korrekt angezeigt wird, liefert dieses Script.

## Features

- ✅ Automatische Titel-Extraktion aus strukturierten Mastodon-Posts
- ✅ Verwendet Profilbild als Podcast-Cover
- ✅ Vollständige iTunes/Podcast-Metadaten
- ✅ Stable GUIDs für Episode-Tracking

## Installation

```bash
pip install feedparser requests
```

## Verwendung

```bash
# Einfach ausführen
python funkmast.py

# Mit eigener Feed-URL
python funkmast.py https://example.com/feed.rss output.rss

# Mit eigenem Cover-Bild
python funkmast.py feed.rss output.rss https://example.com/cover.jpg
```

## Post-Struktur

Damit die Titel korrekt extrahiert werden, sollten Mastodon-Posts diesem Muster folgen:

```
#Funkmast

Hier kommt der Titel der Episode

Podcast Feed: https://example.com/podcast.rss
```

## Ausgabe

Das Script erstellt eine `funkmast_podcast.rss` Datei, die auf einem Webserver gehostet werden kann.

## Autor

Michael Karbacher

## Lizenz

GPL-3.0