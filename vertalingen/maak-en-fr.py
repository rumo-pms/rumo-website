#!/usr/bin/env python3
"""Maakt de Engelse en Franse pagina's uit de Nederlandse.

WAAROM DIT BESTAAT
------------------
en/ en fr/ zijn een half jaar lang los bijgehouden en liepen daardoor achter:
de navigatie had nog acht items terwijl de Nederlandse er vijf had, de
prijzenpagina toonde vijf modules terwijl er acht bestonden, en de
features-pagina had de hele integratielijst niet. Elke keer dat er iets aan de
Nederlandse kant veranderde, moest iemand eraan denken. Dat gebeurde niet.

Nu zijn ze uitvoer. De Nederlandse pagina is de bron, per pagina staat er een
vertaaltabel naast, en dit script zet die twee samen. Verandert er iets in het
Nederlands, dan draai je dit opnieuw. Blijft er een Nederlandse zin staan, dan
zegt het script dat met naam en toenaam in plaats van hem stilletjes te laten
staan.

DRAAIEN
-------
    cd /Users/jeffrey/Projecten/rumo-website
    python3 vertalingen/maak-en-fr.py            # alles
    python3 vertalingen/maak-en-fr.py pms.html   # één pagina

DE TABELLEN
-----------
vertalingen/<naam>.json is een woordenboek van {Nederlandse tekst: {en, fr}}.
Die maak je niet met de hand:

    python3 vertalingen/haal-teksten.py pms.html   -> genummerde lijst
    (vul _werk/pms.en.txt en _werk/pms.fr.txt)
    python3 vertalingen/vul-in.py pms              -> vertalingen/pms.json

De sleutel is de tekst zoals die in de HTML staat, met de inline-opmaak
erbinnen. Witruimte doet er niet toe: het script zoekt met \\s+ tussen de
woorden, zodat een zin die in de bron over twee regels loopt gewoon matcht.

DE LINKS
--------
Die worden berekend, niet opgezocht. Elke href en src wordt opgelost ten
opzichte van de bronmap, door VERTAALD gehaald (staat er een Engelse versie
van die pagina, dan gaat de link daarheen) en daarna teruggerekend naar de map
waar het doelbestand staat. Zo werkt en/uitgelegd/ met twee mappen diep even
goed als en/ met één, zonder een lijst met ../ die iemand moet bijhouden.

WAT DIT SCRIPT NIET DOET
------------------------
faq, over-ons/about/a-propos en prijzen/pricing/tarifs staan er niet in. Die
zijn nog met de hand vertaald en lopen dus opnieuw het risico achter te raken.
Wie ze hierin trekt, moet er alleen een tabel bij schrijven.
"""
import io
import json
import os
import posixpath
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(WORTEL)


def pagina(bron, en=None, fr=None, tabel=None, actief=None):
    """Eén regel in de lijst hieronder, met de saaie afleidingen erin."""
    naam = bron.replace('.html', '').replace('/', '-')
    return {
        'bron': bron,
        'tabel': tabel or 'vertalingen/%s.json' % naam,
        'doel': {'en': en or 'en/' + bron, 'fr': fr or 'fr/' + bron},
        'actief': actief,
    }


PAGINAS = [
    pagina('index.html'),
    pagina('features.html', actief='features.html'),
    pagina('wat-drijft-ons.html', en='en/what-drives-us.html',
           fr='fr/ce-qui-nous-anime.html', actief='wat-drijft-ons.html'),

    # De productpagina's.
    pagina('pms.html'),
    pagina('rudy.html'),
    pagina('handbook.html'),
    pagina('channel-manager.html'),
    pagina('guest-portal.html'),
    pagina('prevention.html'),
    pagina('veiligheid.html', en='en/security.html', fr='fr/securite.html'),
    pagina('advanced-housekeeping.html'),

    # Kennis.
    pagina('kb.html'),
    pagina('uitgelegd/index.html', en='en/explained/index.html',
           fr='fr/explique/index.html'),
    pagina('uitgelegd/opleiden.html', en='en/explained/training.html',
           fr='fr/explique/formation.html'),
    pagina('uitgelegd/draaiboek.html', en='en/explained/handbook.html',
           fr='fr/explique/manuel.html'),
    pagina('uitgelegd/gebouwbeheer.html', en='en/explained/building.html',
           fr='fr/explique/batiment.html'),
    pagina('uitgelegd/allotments.html', en='en/explained/allotments.html',
           fr='fr/explique/allotements.html'),
    pagina('uitgelegd/ota-commissie.html', en='en/explained/ota-commission.html',
           fr='fr/explique/commission-ota.html'),

    # De rest.
    pagina('overstappen.html', en='en/switching.html', fr='fr/migration.html'),
    pagina('coming-soon.html'),
    pagina('sign.html'),
    pagina('privacy.html'),
    pagina('cookies.html'),
    pagina('privacy-staff.html'),
    pagina('voorwaarden.html', en='en/generalterms.html',
           fr='fr/conditions-generales.html'),
    pagina('dpa.html'),
]

# Welke Nederlandse pagina hoort bij welk vertaald bestand. Dit is de lijst
# waarop de links steunen. De vier onderaan worden niet gegenereerd maar
# bestaan wel, dus daar moet een link ook heen kunnen.
VERTAALD = {}
for p in PAGINAS:
    VERTAALD[p['bron']] = p['doel']
VERTAALD.update({
    'prijzen.html': {'en': 'en/pricing.html', 'fr': 'fr/tarifs.html'},
    'over-ons.html': {'en': 'en/about.html', 'fr': 'fr/a-propos.html'},
    'faq.html': {'en': 'en/faq.html', 'fr': 'fr/faq.html'},
    'integraties.html': {'en': 'en/integrations.html', 'fr': 'fr/integrations.html'},
})

# De actieve regel in het menu verschilt per taal. Alleen de pagina's die in
# het hoofdmenu staan hebben er een.
# De hrefs hierin blijven Nederlands: de paden worden berekend, net als
# overal elders. Stond hier what-drives-us.html, dan zou de omleiding er
# ../what-drives-us.html van maken en dat bestand bestaat niet.
ACTIEF = {
    'features.html': {
        'nl': '<li><a href="features.html" class="active">Wat doen we?</a></li>',
        'en': '<li><a href="features.html" class="active">What do we do?</a></li>',
        'fr': '<li><a href="features.html" class="active">Que faisons-nous&nbsp;?</a></li>',
    },
    'wat-drijft-ons.html': {
        'nl': '<li><a href="wat-drijft-ons.html" class="active">Wat drijft ons?</a></li>',
        'en': '<li><a href="wat-drijft-ons.html" class="active">What drives us?</a></li>',
        'fr': '<li><a href="wat-drijft-ons.html" class="active">Ce qui nous anime</a></li>',
    },
}

VERWIJZING = re.compile(r'(href|src)="([^":#][^":]*?)"')

# Woorden die alleen in het Nederlands voorkomen. Staat er zo een in een tekst
# die nog letterlijk op de Engelse of Franse pagina staat, dan is die tekst
# vergeten. Zonder zo'n woord is het waarschijnlijk een naam of een merk, en
# dan hoort hij er net wel zo te staan.
# ("onze" en "ons" staan er bewust niet in: onze is Frans voor elf.)
NEDERLANDS = re.compile(
    r'\b(het|een|dat|niet|geen|wordt|worden|zijn|maar|omdat|zodat|elke|deze|'
    r'jouw|jij|jullie|wat|hoe|waar|welke|meer|nog|ook|wel|naar|'
    r'moet|kan|kun|gaat|staat|komt|krijgt|heeft|hebben|zie|zit|doe|doet)\b',
    re.I)

_HAAL = []


def haal_module():
    """haal-teksten.py als module, één keer geladen."""
    if not _HAAL:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'haal', os.path.join(WORTEL, 'vertalingen/haal-teksten.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _HAAL.append(mod)
    return _HAAL[0]


def leid_om(waarde, bronmap, doelmap, taal):
    """Rekent één href of src om naar het pad dat vanaf de doelmap klopt."""
    pad, staart = waarde, ''
    for teken in ('#', '?'):
        if teken in pad:
            pad, rest = pad.split(teken, 1)
            staart = teken + rest + staart
    if not pad:
        return waarde  # puur een anker of een querystring
    doelbestand = posixpath.normpath(posixpath.join(bronmap, pad))
    doelbestand = VERTAALD.get(doelbestand, {}).get(taal, doelbestand)
    nieuw = posixpath.relpath(doelbestand, doelmap or '.')
    return nieuw + staart


def taalkiezer(taal, pag):
    """De NL/EN/FR-knopjes rechtsboven, met de juiste actief."""
    doelmap = posixpath.dirname(pag['doel'][taal])
    rijen = {}
    for t, bestand in (('nl', pag['bron']),
                       ('en', pag['doel']['en']),
                       ('fr', pag['doel']['fr'])):
        rijen[t] = '<a href="%s">%s</a>' % (
            posixpath.relpath(bestand, doelmap or '.'), t.upper())
    rijen[taal] = rijen[taal].replace('">', '" class="active">')
    return '<li class="nav-lang">\n      %s\n      %s\n      %s\n    </li>' % (
        rijen['nl'], rijen['en'], rijen['fr'])


DIEPER = re.compile(r'href="(?!\.\./|https?:|mailto:|#)')


def een_map_dieper(tabel):
    """Dezelfde regels, maar met ../ voor elke interne link.

    De pagina's in uitgelegd/ staan een map dieper en schrijven hun menu dus
    als ../features.html. Zonder deze variant zou de hele navigatie een tweede
    keer in elke tabel moeten staan, en dat is precies het soort dubbele lijst
    dat na twee maanden uit elkaar loopt.
    """
    uit = {}
    for nl, vert in tabel.items():
        if 'href="' not in nl:
            continue
        nieuw = DIEPER.sub('href="../', nl)
        if nieuw != nl:
            uit[nieuw] = dict((t, DIEPER.sub('href="../', v)) for t, v in vert.items())
    return uit


def als_patroon(sleutel):
    """Zoekt de zin terug ook als hij in de bron over meerdere regels loopt."""
    return re.compile(r'\s+'.join(re.escape(w) for w in sleutel.split()))


def nl_taalkiezer(pag):
    """Zet de NL/EN/FR-knopjes in de Nederlandse bron zelf goed.

    Die stonden met de hand geschreven op elke pagina, en verwezen naar
    en/index.html omdat er nog geen Engelse productpagina's waren. Nu die er
    wel zijn, hoort de knop naar de vertaling van díé pagina te wijzen. Dat
    hier laten gebeuren is de enige manier om het gelijk te houden: het is een
    lijst van 26 stukjes die anders per pagina met de hand moet volgen.
    """
    s = io.open(pag['bron'], encoding='utf-8').read()
    m = re.search(r'<li class="nav-lang">[\s\S]*?</li>', s)
    if not m:
        return False
    bronmap = posixpath.dirname(pag['bron'])
    rijen = {
        'nl': '<a href="%s" class="active">NL</a>' % posixpath.basename(pag['bron']),
        'en': '<a href="%s">EN</a>' % posixpath.relpath(pag['doel']['en'], bronmap or '.'),
        'fr': '<a href="%s">FR</a>' % posixpath.relpath(pag['doel']['fr'], bronmap or '.'),
    }
    nieuw = '<li class="nav-lang">\n      %s\n      %s\n      %s\n    </li>' % (
        rijen['nl'], rijen['en'], rijen['fr'])
    if s[m.start():m.end()] == nieuw:
        return False
    io.open(pag['bron'], 'w', encoding='utf-8').write(s[:m.start()] + nieuw + s[m.end():])
    return True


def bouw(pag, taal):
    bron = io.open(pag['bron'], encoding='utf-8').read()
    bronmap = posixpath.dirname(pag['bron'])
    doelmap = posixpath.dirname(pag['doel'][taal])

    # gedeeld.json houdt de navigatie en de voettekst bij, want die staan op
    # elke pagina en hoefden niet vijfentwintig keer vertaald te worden.
    tabel = json.load(io.open('vertalingen/gedeeld.json', encoding='utf-8'))
    if os.path.exists(pag['tabel']):
        tabel.update(json.load(io.open(pag['tabel'], encoding='utf-8')))
    if bronmap:
        tabel.update(een_map_dieper(tabel))

    s = bron

    # De taalkiezer eerst: daar staan paden in die de omleiding hieronder
    # anders nog eens zou omrekenen.
    # Niet elke pagina heeft een menu: het contractscherm en de placeholders
    # staan op zichzelf. Die krijgen ook geen taalkeuze.
    m = re.search(r'<li class="nav-lang">[\s\S]*?</li>', s)
    kiezer = ''
    if m:
        kiezer = taalkiezer(taal, pag)
        s = s[:m.start()] + '\x00KIEZER\x00' + s[m.end():]

    if pag['actief'] and pag['actief'] in ACTIEF:
        regel = ACTIEF[pag['actief']]
        s = s.replace(regel['nl'], regel[taal])

    # Dan de teksten. Langste eerst, zodat een kort woord niet middenin een
    # langere zin toeslaat die nog vertaald moet worden.
    for nl in sorted(tabel, key=len, reverse=True):
        s = als_patroon(nl).sub(lambda _m, v=tabel[nl][taal]: v, s)

    # En pas daarna de paden: eerder zouden de Nederlandse zinnen mét een link
    # erin niet meer matchen.
    s = VERWIJZING.sub(
        lambda m: '%s="%s"' % (m.group(1), leid_om(m.group(2), bronmap, doelmap, taal)), s)

    s = s.replace('\x00KIEZER\x00', kiezer)
    s = s.replace('<html lang="nl">', '<html lang="%s">' % taal)

    map_ = posixpath.dirname(pag['doel'][taal])
    if map_:
        os.makedirs(map_, exist_ok=True)
    io.open(pag['doel'][taal], 'w', encoding='utf-8').write(s)
    return tabel


def controleer(pag, taal, tabel):
    """Zoekt Nederlandse zinnen die op de vertaalde pagina blijven staan.

    Deze controle leest de UITVOER, niet de bron. Dat is met opzet: leest ze
    dezelfde lijst als haal-teksten.py, dan is ze blind voor precies datgene
    wat dat script mist, en dat is het soort controle dat altijd groen staat.

    Elk stukje tekst tussen twee tags wordt bekeken. Zit er een woord in dat
    alleen in het Nederlands bestaat, en staat dat stukje niet in de tabel
    (waar het ook met dezelfde tekst in mag staan, voor namen en merken), dan
    is het een vergeten zin.
    """
    dekking = '\n'.join(tabel)
    uit = io.open(pag['doel'][taal], encoding='utf-8').read()
    uit = re.sub(r'<script[\s\S]*?</script>', '', uit)
    uit = re.sub(r'<style[\s\S]*?</style>', '', uit)
    uit = re.sub(r'<!--[\s\S]*?-->', '', uit)

    blijft = []
    gezien = set()
    for stuk in re.findall(r'>([^<>]+)<', uit) + re.findall(
            r'(?:alt|title|placeholder|aria-label|content)="([^"]{20,})"', uit):
        t = re.sub(r'\s+', ' ', stuk).strip()
        if not t or t in gezien or not NEDERLANDS.search(t):
            continue
        gezien.add(t)
        if t in dekking:
            continue
        blijft.append(t)
    return blijft


def main():
    keuze = sys.argv[1:]
    lijst = [p for p in PAGINAS if not keuze or p['bron'] in keuze]
    if keuze and not lijst:
        raise SystemExit('geen pagina met die naam: ' + ', '.join(keuze))

    fouten = 0
    for pag in lijst:
        if not os.path.exists(pag['tabel']):
            print('%-34s GEEN TABEL (%s)' % (pag['bron'], pag['tabel']))
            fouten += 1
            continue
        if nl_taalkiezer(pag):
            print('%-34s taalkiezer in de bron bijgewerkt' % pag['bron'])
        for taal in ('en', 'fr'):
            tabel = bouw(pag, taal)
            blijft = controleer(pag, taal, tabel)
            merk = '' if not blijft else '  <- %d zinnen nog Nederlands' % len(blijft)
            print('%-34s -> %s%s' % (pag['bron'], pag['doel'][taal], merk))
            for t in blijft[:8]:
                print('      %s' % t[:100])
            if blijft:
                fouten += 1
    sys.exit(1 if fouten else 0)


if __name__ == '__main__':
    main()
