# PRODUCT MAP — Token Hunter

## 1. Celková architektura produktu

### Vrstva 1 — Source Ingestion
Sbírá data a evidence.

Moduly:
- source registry
- scheduler fetchů
- fetchers/connectors
- HTML/doc parsers
- feed ingest
- changelog ingest
- source health monitor
- robots/ToS notes

### Vrstva 2 — Normalization
Překládá chaos do jedné řeči.

Moduly:
- provider normalizer
- model normalizer
- pricing normalizer
- promo/trial normalizer
- region/eligibility normalizer
- unit converter
- canonical matcher
- evidence linker

### Vrstva 3 — Verification
Hlídá pravdu a konflikty.

Moduly:
- source trust ranking
- official-first resolver
- conflict detector
- stale data detector
- manual review queue
- last-verified tracker

### Vrstva 4 — Scoring
Dělá verdicty.

Moduly:
- best-buy score
- savings score
- friction score
- confidence score
- relevance score
- novelty score
- game-changer classifier

### Vrstva 5 — User Experience
Zobrazuje rozhodnutí.

Moduly:
- home radar
- compare
- alerts
- watchlist
- deal detail
- search
- digest
- saved picks
- today widget model

### Vrstva 6 — Admin & Quality
Drží produkt při životě.

Moduly:
- parser QA
- source audit
- failed fetch review
- suspicious offer review
- stale item cleanup
- alert quality analytics
- taxonomy management

## 2. Informační model

### Provider
- id
- name
- category
- official site
- billing style
- direct API flag
- partner routes flag
- region notes
- support notes
- trust baseline

### Model
- id
- canonical name
- family
- provider id
- capability tags
- coding relevance
- reasoning relevance
- modality
- launch status
- sunset status

### Access Route
- id
- model id
- route type (direct / gateway / partner / host)
- route owner
- pricing reference
- friction flags
- setup complexity
- availability
- rate-limit summary

### Offer
- id
- offer type (free tier / promo / credit / bundle / cheaper route)
- title
- headline value
- start date
- end date
- eligibility
- terms summary
- verification status
- evidence pointers

### Price Snapshot
- id
- route id
- input price
- output price
- cached price
- subscription price if relevant
- included credits/quota
- unit
- observed at
- effective at

### Deal Verdict
- id
- headline
- verdict
- who it is for
- why it matters
- savings estimate
- confidence
- risks/limitations
- alternatives
- expiry pressure

### Source Evidence
- id
- source type
- source url
- title
- excerpt
- captured at
- parser version
- trust tier

### Watch Rule
- id
- user id
- watch type
- watch target
- thresholds
- frequency
- delivery channel
- mute rules

### Research Item
- id
- item type (model / app / library / provider / release)
- novelty
- evidence
- hype flag
- watch-worthy flag
- game-changer flag
- savings relevance

## 3. Klíčové obrazovky

### Home — Savings Radar
Sekce:
- top best buys today
- new free/free-ish options
- cheaper route found
- expiring soon
- watch-worthy launches
- quick compare entry

### Compare
Vstup:
- use-case
- budget
- tolerance to friction
- preference for official vs aggregator route
- preview/beta tolerance
- open-source bias

Výstup:
- #1 doporučení
- 3 alternativy
- tabulka výhod/nevýhod
- estimated monthly cost
- why this wins

### Deal Detail
Musí ukázat:
- co to je,
- proč je to výhodné,
- pro koho to je,
- kdo se tomu má vyhnout,
- kolik to stojí,
- jaké jsou limity,
- odkazy na evidence,
- last verified,
- související alternativy.

### Watchlist
Uživatel sleduje:
- model,
- provider,
- category,
- use-case,
- typ nabídky.

### Research / Discovery
Vedlejší vrstva:
- nové modely,
- nové knihovny,
- nové AI appky,
- nové providery,
- zásadní pricing změny,
- novinky s vysokou savings relevancí.

## 4. Hlavní user flows

### Flow A — „Chci nejlevnější coding setup“
1. Uživatel otevře Compare.
2. Zvolí coding cheap.
3. Nastaví budget a toleranci k frikci.
4. Dostane shortlist + verdict + alternatives + caveats.
5. Uloží watchlist.

### Flow B — „Chci vědět, jestli se objevil lepší deal“
1. Uživatel nastaví use-case watch.
2. Backend sleduje změny.
3. Při zlepšení thresholdu pošle alert.
4. Uživatel otevře deal detail a rozhodne se.

### Flow C — „Je tahle novinka fakt game changer?“
1. Discovery zachytí release.
2. Verification dohledá oficiální důkazy.
3. Scoring dopočítá novelty, relevance, confidence.
4. Výstup dostane badge: hype/watch/relevant/game changer.

## 5. Alert systém

Typy alertů:
- new best buy in your category
- price drop
- free tier appeared
- free tier ended
- cheaper route found
- deal expiring
- new model worth watching
- game changer candidate

Každý alert musí obsahovat:
- co se změnilo,
- proti čemu je to lepší,
- proč to má význam,
- jaká je confidence,
- co má uživatel udělat.

## 6. Personalizace

Lehká a vysvětlitelná.

Uživatel nastaví:
- use-cases,
- měsíční budget,
- preferované ekosystémy,
- averzi k preview/beta,
- ochotu řešit frikci,
- zájem o open-source/local stack,
- mód: only-free / mostly-free / best-value / premium-value.

## 7. Admin mapa

### Source operations
- enable/disable source
- last fetch
- parser health
- conflict flags
- stale detection
- robots/ToS notes

### Review operations
- suspicious offer queue
- broken parser queue
- manual override
- trust downgrade
- expired deal cleanup

### Quality analytics
- false positive alerts
- stale deals shown
- user-dismissed alerts
- source error rate
- unverified leakage

## 8. Monetization hooks

Připravené, ale neagresivní.

Možnosti:
- free + pro alerts
- pro compare engine depth
- premium watchlists
- affiliate tam, kde je čistě označený a nepřekrucuje verdict
- team plan později

## 9. Hlavní produktové testy

Každý release musí projít:
- savings utility testem,
- evidence trail testem,
- stale data testem,
- alert noise testem,
- compare sanity testem,
- iOS consumption sanity testem.
