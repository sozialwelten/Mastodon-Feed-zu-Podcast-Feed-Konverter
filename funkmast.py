#!/usr/bin/env python3
"""
Mastodon zu Podcast RSS Feed Konverter
Konvertiert einen Mastodon RSS-Feed in einen Podcast-kompatiblen RSS-Feed
"""

import feedparser
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import requests
from datetime import datetime
from html import unescape
import sys


def extract_title_from_content(content):
    """
    Extrahiert den Titel aus dem Mastodon-Post-Inhalt.
    Erwartet Struktur: #Funkmast, dann Titel auf nächster Zeile
    """
    # HTML-Entities dekodieren und HTML-Tags entfernen
    text = unescape(content)
    text = re.sub(r'<[^>]+>', '\n', text)

    # Nach #Funkmast suchen und die nächste nicht-leere Zeile als Titel nehmen
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    for i, line in enumerate(lines):
        if '#Funkmast' in line or 'Funkmast' in line:
            # Nächste Zeile ist der Titel
            if i + 1 < len(lines):
                title = lines[i + 1]
                # "Podcast Feed:" Zeile entfernen falls vorhanden
                if not title.startswith('Podcast Feed:'):
                    return title

    # Fallback: Erste Zeile oder "Unbenannte Episode"
    if lines:
        return lines[0][:100]  # Maximal 100 Zeichen
    return "Unbenannte Episode"


def extract_audio_url(entry):
    """
    Extrahiert die Audio-URL aus den Enclosures
    """
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            # Prüfe ob es eine Audio-Datei ist
            if 'type' in enc and enc['type'].startswith('audio/'):
                return enc.get('href') or enc.get('url')
    return None


def extract_image_url(entry):
    """
    Extrahiert die Bild-URL aus den Enclosures oder Media-Content
    """
    # Versuche aus Enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'type' in enc and enc['type'].startswith('image/'):
                return enc.get('href') or enc.get('url')

    # Versuche aus media_content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if 'type' in media and media['type'].startswith('image/'):
                return media.get('url')

    # Versuche aus media_thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url')

    return None


def get_audio_info(url):
    """
    Holt Informationen über die Audio-Datei (Größe, Typ)
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        content_length = response.headers.get('Content-Length', '0')
        content_type = response.headers.get('Content-Type', 'audio/mpeg')
        return content_length, content_type
    except:
        return '0', 'audio/mpeg'


def extract_avatar_from_feed(feed):
    """
    Extrahiert das Avatar/Profilbild aus dem Feed
    """
    # Versuche aus feed.image
    if hasattr(feed.feed, 'image') and 'href' in feed.feed.image:
        return feed.feed.image['href']

    # Versuche aus feed.logo
    if hasattr(feed.feed, 'logo'):
        return feed.feed.logo

    # Versuche aus feed.icon
    if hasattr(feed.feed, 'icon'):
        return feed.feed.icon

    return None


def create_podcast_feed(mastodon_feed_url, output_file='podcast.rss', podcast_image_url=None):
    """
    Erstellt einen Podcast-RSS-Feed aus einem Mastodon-Feed

    Args:
        mastodon_feed_url: URL des Mastodon RSS-Feeds
        output_file: Ausgabedatei für den Podcast-Feed
        podcast_image_url: URL zum Podcast-Cover-Bild (optional)
    """
    print(f"Lade Feed von: {mastodon_feed_url}")
    feed = feedparser.parse(mastodon_feed_url)

    if not feed.entries:
        print("Fehler: Keine Einträge im Feed gefunden!")
        return

    # Avatar/Profilbild extrahieren (falls nicht manuell angegeben)
    if not podcast_image_url:
        podcast_image_url = extract_avatar_from_feed(feed)
        if podcast_image_url:
            print(f"Verwende Avatar aus Feed: {podcast_image_url}")
        else:
            print("Warnung: Kein Avatar im Feed gefunden")

    # RSS Root Element
    rss = ET.Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')

    channel = ET.SubElement(rss, 'channel')

    # Channel Metadaten
    ET.SubElement(channel, 'title').text = feed.feed.get('title', 'Funkmast Podcast')
    ET.SubElement(channel, 'link').text = 'https://ifwo.eu'
    ET.SubElement(channel, 'description').text = 'IfWO #Funkmast Podcast von Sozialwelten. Funkt von Mastodon aus für das Fediverse und darüber hinaus. Soziologische Perspektive auf Social Media und Gesellschaft'
    ET.SubElement(channel, 'language').text = 'de'
    ET.SubElement(channel, 'managingEditor').text = 'sozialwelten@ifwo.eu (Michael Karbacher)'
    ET.SubElement(channel, 'webMaster').text = 'sozialwelten@ifwo.eu (Michael Karbacher)'

    # iTunes spezifische Tags
    itunes_author = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}author')
    itunes_author.text = 'Michael Karbacher'

    itunes_owner = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}owner')
    itunes_owner_name = ET.SubElement(itunes_owner, '{http://www.itunes.com/dtds/podcast-1.0.dtd}name')
    itunes_owner_name.text = 'Michael Karbacher'
    itunes_owner_email = ET.SubElement(itunes_owner, '{http://www.itunes.com/dtds/podcast-1.0.dtd}email')
    itunes_owner_email.text = 'sozialwelten@ifwo.eu'

    itunes_category = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}category')
    itunes_category.set('text', 'Technology')

    itunes_explicit = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit')
    itunes_explicit.text = 'no'

    # Podcast Cover-Bild
    if podcast_image_url:
        image = ET.SubElement(channel, 'image')
        ET.SubElement(image, 'url').text = podcast_image_url
        ET.SubElement(image, 'title').text = feed.feed.get('title', 'Funkmast Podcast')
        ET.SubElement(image, 'link').text = 'https://ifwo.eu'

        itunes_image = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}image')
        itunes_image.set('href', podcast_image_url)

    # Episoden verarbeiten
    episode_count = 0
    for entry in feed.entries:
        audio_url = extract_audio_url(entry)

        if not audio_url:
            print(f"Überspringe Eintrag ohne Audio: {entry.get('title', 'Unbekannt')}")
            continue

        episode_count += 1
        print(f"Verarbeite Episode {episode_count}: {entry.get('title', 'Unbekannt')}")

        item = ET.SubElement(channel, 'item')

        # Titel extrahieren
        title = extract_title_from_content(entry.get('summary', ''))
        ET.SubElement(item, 'title').text = title

        # Link zum Original-Post
        ET.SubElement(item, 'link').text = entry.get('link', '')

        # Beschreibung
        description = entry.get('summary', '')
        ET.SubElement(item, 'description').text = description

        # Datum
        pub_date = entry.get('published', datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000'))
        ET.SubElement(item, 'pubDate').text = pub_date

        # GUID
        ET.SubElement(item, 'guid').text = entry.get('id', entry.get('link', ''))

        # Audio Enclosure
        print(f"  Audio URL: {audio_url}")
        length, content_type = get_audio_info(audio_url)

        enclosure = ET.SubElement(item, 'enclosure')
        enclosure.set('url', audio_url)
        enclosure.set('length', length)
        enclosure.set('type', content_type)

        # iTunes Episode Metadaten
        itunes_title = ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}title')
        itunes_title.text = title

        itunes_summary = ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}summary')
        itunes_summary.text = description

        # Episodenbild (falls vorhanden)
        image_url = extract_image_url(entry)
        if image_url:
            print(f"  Bild URL: {image_url}")
            itunes_episode_image = ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}image')
            itunes_episode_image.set('href', image_url)
        elif podcast_image_url:
            # Fallback auf Podcast-Cover (Avatar)
            itunes_episode_image = ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}image')
            itunes_episode_image.set('href', podcast_image_url)

    # XML formatieren und speichern
    xml_string = ET.tostring(rss, encoding='unicode')
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent='  ')

    # XML-Deklaration bereinigen (nur eine)
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)

    print(f"\n✓ Podcast-Feed erstellt: {output_file}")
    print(f"✓ {episode_count} Episoden verarbeitet")


if __name__ == '__main__':
    # Standard-URL (korrigiert)
    feed_url = 'https://ifwo.eu/@funkmast/tagged/funkmast.rss'
    output = 'funkmast_podcast.rss'
    podcast_image = None  # Optional: URL zu einem alternativen Cover-Bild

    # Kommandozeilenargumente erlauben
    if len(sys.argv) > 1:
        feed_url = sys.argv[1]
    if len(sys.argv) > 2:
        output = sys.argv[2]
    if len(sys.argv) > 3:
        podcast_image = sys.argv[3]

    # Beispiele:
    # python script.py (nutzt Avatar aus Feed automatisch)
    # python script.py feed.rss output.rss (nutzt Avatar aus Feed)
    # python script.py feed.rss output.rss https://example.com/cover.jpg (nutzt angegebenes Bild)

    create_podcast_feed(feed_url, output, podcast_image)