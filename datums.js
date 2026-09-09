/* datums.js — vult de datums in de nagebouwde schermen in met de dag van vandaag.
 *
 * WAAROM
 * De previews stonden allemaal op "2 april". Voor een bezoeker in september
 * leest dat als een oude schermafbeelding. Nu volgen ze mee.
 *
 * HOE
 * Zet een attribuut op het element; de tekst die er al staat blijft het
 * antwoord voor wie geen JavaScript heeft.
 *
 *   <span data-datum="vandaag">2 april</span>            -> 8 september
 *   <span data-datum="vandaag-jaar">2 april 2026</span>  -> 8 september 2026
 *   <span data-datum="morgen">3 april</span>             -> 9 september
 *   <span data-datum="dag-vandaag">do</span>             -> ma
 *   <span data-datum="maand">1 - 30 april 2026</span>    -> 1 - 30 september 2026
 *   <span data-datum="maand-naam">april 2026</span>        -> september 2026
 *   <span data-datum="over-een-maand">12 mei</span>      -> 8 oktober
 *
 * En voor de kalender, waar zeven kolommen tegelijk moeten kloppen:
 *
 *   <div class="av-dagen" data-kalender>
 *     <span></span><span>wo<b>1</b></span>... zeven stuks
 *   </div>
 *
 * De week begint bewust op gisteren, zodat vandaag de tweede kolom is. Dat is
 * ook hoe de balken in de kalender geplaatst staan: die rekenen in kolommen,
 * niet in datums. Verschuif je de week, dan kloppen de boekingen niet meer.
 */
(function () {
  /* De taal komt uit <html lang>. Zonder dit stond er "september" op de
     Engelse en de Franse pagina, want dit bestand wordt gedeeld. */
  var NAMEN = {
    nl: {
      maanden: ['januari', 'februari', 'maart', 'april', 'mei', 'juni',
                'juli', 'augustus', 'september', 'oktober', 'november', 'december'],
      dagen: ['zo', 'ma', 'di', 'wo', 'do', 'vr', 'za']
    },
    en: {
      maanden: ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'],
      dagen: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
    },
    fr: {
      maanden: ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
      dagen: ['di', 'lu', 'ma', 'me', 'je', 've', 'sa']
    }
  };
  var TAAL = (document.documentElement.lang || 'nl').slice(0, 2);
  var MAANDEN = (NAMEN[TAAL] || NAMEN.nl).maanden;
  var DAGEN = (NAMEN[TAAL] || NAMEN.nl).dagen;

  function plus(d, n) {
    var x = new Date(d.getTime());
    x.setDate(x.getDate() + n);
    return x;
  }
  function kort(d)  { return d.getDate() + ' ' + MAANDEN[d.getMonth()]; }
  function lang(d)  { return kort(d) + ' ' + d.getFullYear(); }

  var vandaag = new Date();

  var tekst = {
    'vandaag':        function () { return kort(vandaag); },
    'vandaag-jaar':   function () { return lang(vandaag); },
    'morgen':         function () { return kort(plus(vandaag, 1)); },
    'dag-vandaag':    function () { return DAGEN[vandaag.getDay()]; },
    'over-een-maand': function () { return kort(plus(vandaag, 30)); },
    'maand-naam':     function () { return MAANDEN[vandaag.getMonth()] + ' ' + vandaag.getFullYear(); },
    'maand':          function () {
      var eerste = new Date(vandaag.getFullYear(), vandaag.getMonth(), 1);
      var laatste = new Date(vandaag.getFullYear(), vandaag.getMonth() + 1, 0);
      return '1 – ' + laatste.getDate() + ' ' + MAANDEN[eerste.getMonth()] + ' ' + eerste.getFullYear();
    }
  };

  try {
    document.querySelectorAll('[data-datum]').forEach(function (el) {
      var f = tekst[el.getAttribute('data-datum')];
      if (f) el.textContent = f();
    });

    document.querySelectorAll('[data-kalender]').forEach(function (rij) {
      // De eerste span is de lege hoek boven de kamerkolom.
      var kolommen = Array.prototype.slice.call(rij.children, 1);
      var start = plus(vandaag, -1);
      kolommen.forEach(function (kol, i) {
        var d = plus(start, i);
        kol.innerHTML = DAGEN[d.getDay()] + '<b>' + d.getDate() + '</b>';
        kol.classList.toggle('nu', i === 1);
      });
    });
  } catch (e) {
    /* Gaat er iets mis, dan blijft de datum staan die in de HTML stond. Een
       preview met een oude datum is minder erg dan een lege kolomkop. */
  }
})();
