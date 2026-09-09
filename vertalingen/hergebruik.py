#!/usr/bin/env python3
"""Maakt de invulbestanden opnieuw, met wat al vertaald was er alvast in.

WAAROM
------
Verandert er één zin in het Nederlands, dan verschuift de hele nummering van
haal-teksten.py. Zonder dit script betekent dat: alles opnieuw overtikken, of
zelf gaan tellen. Beide gaan mis.

Dit script legt de nieuwe lijst naast de bestaande tabel. Wat er al in stond
komt er gewoon weer in; wat nieuw is krijgt TODO en de Nederlandse zin erbij,
zodat je meteen ziet wat er te doen is.

DRAAIEN
-------
    python3 vertalingen/haal-teksten.py pms.html      # nieuwe lijst
    python3 vertalingen/hergebruik.py pms             # invulbestanden
    (vul de TODO-regels aan)
    python3 vertalingen/vul-in.py pms
"""
import io
import json
import os
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(WORTEL)


def main():
    if len(sys.argv) < 2:
        raise SystemExit('gebruik: python3 vertalingen/hergebruik.py <naam>')
    naam = sys.argv[1]

    tabel = {}
    pad_json = 'vertalingen/%s.json' % naam
    if os.path.exists(pad_json):
        tabel = json.load(io.open(pad_json, encoding='utf-8'))

    sleutels = []
    for regel in io.open('vertalingen/_werk/%s.keys.tsv' % naam, encoding='utf-8'):
        regel = regel.rstrip('\n')
        if regel.strip():
            nr, nl = regel.split('\t', 1)
            sleutels.append((nr, nl))

    for taal in ('en', 'fr'):
        pad = 'vertalingen/_werk/%s.%s.txt' % (naam, taal)
        nieuw = 0
        with io.open(pad, 'w', encoding='utf-8') as f:
            for nr, nl in sleutels:
                if nl in tabel:
                    f.write('%s|%s\n' % (nr, tabel[nl][taal]))
                else:
                    f.write('%s|TODO %s\n' % (nr, nl))
                    nieuw += 1
        print('%s: %d regels, %d nog te vertalen' % (pad, len(sleutels), nieuw))


if __name__ == '__main__':
    main()
