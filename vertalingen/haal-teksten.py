#!/usr/bin/env python3
"""Haalt de vertaalbare teksten uit een Nederlandse pagina.

WAAROM DIT BESTAAT
------------------
maak-en-fr.py zet een Nederlandse pagina en een vertaaltabel samen. Die tabel
met de hand samenstellen is het soort werk waarbij je zinnen vergeet, en een
vergeten zin blijft gewoon in het Nederlands op een Engelse pagina staan.

Dit script leest de pagina en schrijft elke tekst die een bezoeker ziet naar
een genummerde lijst. Daarna vul je per taal een bestand met dezelfde nummers,
en zet vul-in.py die twee samen tot de tabel.

DRAAIEN
-------
    python3 vertalingen/haal-teksten.py pms.html

Dat schrijft vertalingen/_werk/pms.keys.tsv en toont de lijst op het scherm.

WAT ER UITGEHAALD WORDT
-----------------------
De inhoud van de kleinste blokjes: een <p>, een <li>, een <h2>, een <span>.
Kleinste, want een <p> met een <em> erin komt er als één zin uit en niet als
drie stukjes. Een halve zin vertalen loopt in het Frans altijd fout af.

Daarnaast: de paginatitel, de omschrijving voor Google, en de teksten in
alt-, title-, placeholder- en aria-label-attributen. Die ziet een bezoeker
ook, alleen niet altijd met zijn ogen.

WAT ER NIET UITGEHAALD WORDT
----------------------------
Scripts, stijlen, HTML-commentaar, en alles wat al in gedeeld.json staat
(de navigatie en de voettekst, die op elke pagina hetzelfde zijn). En strings
zonder letters: een bedrag, een huisnummer, een pijltje.
"""
import io
import json
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(WORTEL)

# Blokjes waarvan we de inhoud nemen, op voorwaarde dat er alleen tekst en
# inline-opmaak in zit. Zit er een ander blok in, dan pakken we dat blok apart.
# div staat er bewust bij. Veel van de nagebouwde schermen zetten hun tekst
# los in een div met een paar spans ernaast; zonder div bleef die tekst
# onzichtbaar voor dit script, en dus onvertaald op de pagina.
BLOK = r'p|li|h1|h2|h3|h4|h5|h6|span|a|div|button|td|th|figcaption|small|label|dt|dd|summary|blockquote|strong|em|b'
INLINE = r'b|i|em|strong|a|span|br|sup|sub|code|u|abbr|nobr'
PATROON = re.compile(
    r'<(%s)(\s[^>]*)?>((?:[^<]|<(?:%s)(?:\s[^>]*)?>|</(?:%s)>)*?)</\1>' % (BLOK, INLINE, INLINE),
    re.S)

ATTRIBUUT = re.compile(r'(?:alt|title|placeholder|aria-label)="([^"]{2,})"')
OMSCHRIJVING = re.compile(r'<meta name="description" content="([^"]+)"')
TITEL = re.compile(r'<title>([^<]+)</title>')

HEEFT_LETTER = re.compile(r'[a-zA-Z]')

# Dingen die er als tekst uitzien maar niet vertaald worden: het logo en de
# taalknopjes. Die laatste zet maak-en-fr.py zelf, per pagina.
NOOIT = {'rumo', 'rumo.', 'NL', 'EN', 'FR', 'rumo .'}


def schoon(s):
    """Vervangt een rij witruimte door een spatie en trimt de randen."""
    return re.sub(r'\s+', ' ', s).strip()


def teksten(bestand):
    ruw = io.open(bestand, encoding='utf-8').read()

    # De kop houden we apart: daar zitten titel en omschrijving in, maar ook
    # scripts die we niet willen.
    kop = ruw[:ruw.index('</head>')] if '</head>' in ruw else ''
    romp = ruw[ruw.index('<body'):] if '<body' in ruw else ruw
    romp = re.sub(r'<script[\s\S]*?</script>', '', romp)
    romp = re.sub(r'<style[\s\S]*?</style>', '', romp)
    romp = re.sub(r'<!--[\s\S]*?-->', '', romp)
    # Icoontjes eruit. Een <span> met een svg en een woord erin telt anders
    # niet als "alleen tekst en opmaak", en dan blijft dat woord onzichtbaar
    # voor dit script. Dat patroon (icoon + label) staat overal.
    romp = re.sub(r'<svg[\s\S]*?</svg>', '', romp)

    gevonden = []

    for m in TITEL.finditer(kop):
        gevonden.append(m.group(1))
    for m in OMSCHRIJVING.finditer(kop):
        gevonden.append(m.group(1))

    # De blokjes van binnen naar buiten: het patroon vindt de kleinste eerst
    # omdat het geen ander blok in zijn inhoud toelaat.
    for m in PATROON.finditer(romp):
        gevonden.append(m.group(3))
    for m in ATTRIBUUT.finditer(romp):
        gevonden.append(m.group(1))

    # Blijft er ergens losse tekst over die in geen blokje zat, dan vangt de
    # controle in maak-en-fr.py dat. Hier houden we het bij wat we zeker weten.
    uit = []
    gezien = set()
    for t in gevonden:
        t = schoon(t)
        kaal = schoon(re.sub(r'<[^>]+>', ' ', t))
        if not t or not HEEFT_LETTER.search(kaal):
            continue
        if kaal in NOOIT or 'class="active">NL<' in t:
            continue
        if t in gezien:
            continue
        gezien.add(t)
        uit.append(t)
    return uit


def main():
    if len(sys.argv) < 2:
        raise SystemExit('gebruik: python3 vertalingen/haal-teksten.py <pagina.html>')
    bestand = sys.argv[1]
    # De naam draagt de map mee: uitgelegd/index.html wordt uitgelegd-index,
    # anders overschrijft die de tabel van de startpagina.
    naam = bestand.replace('.html', '').replace('/', '-')

    gedeeld = json.load(io.open('vertalingen/gedeeld.json', encoding='utf-8'))
    # Als tekst: de sleutels van gedeeld.json staan mét hun <li> eromheen,
    # terwijl wij de <a> erbinnen vinden. Een substring-test vangt allebei.
    # Ook de variant met ../ ervoor: pagina's in een submap schrijven hun menu
    # zo, en maak-en-fr.py maakt daar zelf regels voor.
    dieper = re.compile(r'href="(?!\.\./|https?:|mailto:|#)')
    gedeeld_blok = '\n'.join(
        [schoon(k) for k in gedeeld] + [dieper.sub('href="../', schoon(k)) for k in gedeeld])

    lijst = [t for t in teksten(bestand) if t not in gedeeld_blok]

    os.makedirs('vertalingen/_werk', exist_ok=True)
    pad = 'vertalingen/_werk/%s.keys.tsv' % naam
    with io.open(pad, 'w', encoding='utf-8') as f:
        for i, t in enumerate(lijst, 1):
            f.write('%d\t%s\n' % (i, t))
            print('%d\t%s' % (i, t))
    print('\n%d teksten -> %s' % (len(lijst), pad), file=sys.stderr)


if __name__ == '__main__':
    main()
