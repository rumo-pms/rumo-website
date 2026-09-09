#!/usr/bin/env python3
"""Zet de genummerde lijsten om in een vertaaltabel.

DRAAIEN
-------
    python3 vertalingen/vul-in.py pms

Leest:
    vertalingen/_werk/pms.keys.tsv   (uit haal-teksten.py: nummer <tab> NL)
    vertalingen/_werk/pms.en.txt     (nummer|Engelse tekst)
    vertalingen/_werk/pms.fr.txt     (nummer|Franse tekst)

Schrijft:
    vertalingen/pms.json

WAAROM MET NUMMERS
------------------
Zo hoeft de Nederlandse zin maar één keer te bestaan. Wie hem in drie
bestanden overtikt, tikt hem ergens anders over, en dan matcht de tabel niet
meer op de pagina zonder dat iemand het merkt.

Het script weigert als er een nummer ontbreekt of als er een nummer in staat
dat niet in de lijst voorkomt. Een halve tabel is erger dan geen tabel: die
laat losse Nederlandse zinnen op een Franse pagina staan.
"""
import io
import json
import os
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(WORTEL)


def lees_vertaling(pad):
    uit = {}
    for regel in io.open(pad, encoding='utf-8'):
        regel = regel.rstrip('\n')
        if not regel.strip():
            continue
        if '|' not in regel:
            raise SystemExit('%s: regel zonder | -> %s' % (pad, regel[:60]))
        nr, tekst = regel.split('|', 1)
        nr = nr.strip()
        if not nr.isdigit():
            raise SystemExit('%s: regel begint niet met een nummer -> %s' % (pad, regel[:60]))
        if nr in uit:
            raise SystemExit('%s: nummer %s staat er twee keer in' % (pad, nr))
        uit[nr] = tekst.strip()
    return uit


def main():
    if len(sys.argv) < 2:
        raise SystemExit('gebruik: python3 vertalingen/vul-in.py <naam>')
    naam = sys.argv[1]

    sleutels = []
    for regel in io.open('vertalingen/_werk/%s.keys.tsv' % naam, encoding='utf-8'):
        regel = regel.rstrip('\n')
        if not regel.strip():
            continue
        nr, nl = regel.split('\t', 1)
        sleutels.append((nr, nl))

    en = lees_vertaling('vertalingen/_werk/%s.en.txt' % naam)
    fr = lees_vertaling('vertalingen/_werk/%s.fr.txt' % naam)

    nummers = set(nr for nr, _ in sleutels)
    for taal, tabel in (('en', en), ('fr', fr)):
        ontbreekt = sorted(nummers - set(tabel), key=int)
        teveel = sorted(set(tabel) - nummers, key=int)
        if ontbreekt:
            raise SystemExit('%s: %d nummers ontbreken, o.a. %s'
                             % (taal, len(ontbreekt), ', '.join(ontbreekt[:12])))
        if teveel:
            raise SystemExit('%s: nummers die niet bestaan: %s' % (taal, ', '.join(teveel[:12])))

    tabel = {}
    for nr, nl in sleutels:
        if nl in tabel:
            continue
        tabel[nl] = {'en': en[nr], 'fr': fr[nr]}

    pad = 'vertalingen/%s.json' % naam
    io.open(pad, 'w', encoding='utf-8').write(
        json.dumps(tabel, ensure_ascii=False, indent=2) + '\n')
    print('%s: %d teksten' % (pad, len(tabel)))


if __name__ == '__main__':
    main()
