# DECISIONS — Token Hunter

## Produktová rozhodnutí

### D1 — Savings-first je nejvyšší priorita
Discovery a AI news je doplněk, ne hlavní osa.

### D2 — Official-first truth
Pricing, limity a podmínky mají prioritu z oficiálních zdrojů.

### D3 — Best buy > katalog
Nebudujeme encyklopedii modelů. Budujeme verdict engine.

### D4 — Backend-first architektura
Crawler, parsery a scoring nežijí v klientu. Klient je spotřební vrstva.

### D5 — iOS-ready od dne 1
Všechny doménové kontrakty a API se navrhují tak, aby šly nativně použít v iOS klientu.

### D6 — Evidence trail je povinný
Každý důležitý verdict musí mít dohledatelný důkaz.

### D7 — Alerty musí být vzácné a užitečné
Ticho je lepší než spam. Lepší méně alertů s vysokou hodnotou.

### D8 — Žádné vymyšlené game-changer štítky
Game changer se nesmí opírat jen o hype.

### D9 — Ruční review je feature, ne selhání
U vysokého dopadu nebo konfliktu zdrojů je manuální review správné rozhodnutí.

### D10 — Affiliate nikdy nesmí diktovat verdict
Monetizace nesmí poškodit důvěru.

## Architektonická rozhodnutí

### A1 — Normalizace jako samostatná vrstva
Nikdy nepracovat přímo s nestrukturovaným scrape výstupem v UI logice.

### A2 — Source registry jako source of truth pro ingest
Každý zdroj musí mít metadata, trust tier a refresh policy.

### A3 — Confidence a stale flags jsou first-class pole
Nejsou to debug pole. Patří do domény a UI.

### A4 — Derived verdicty oddělit od raw evidence
Aby šlo kdykoli vysvětlit, proč verdict vznikl.

### A5 — Game changer classifier v1 pravidlově
Na startu nepoužívat složitou LLM logiku tam, kde stačí vysvětlitelná pravidla.

### A6 — Alerts vznikají jen z normalizovaných a verifikovaných změn
Ne z raw scrape signálů.

### A7 — Research layer nesmí přepsat savings layer
I kdyby byl mediálně zajímavější.
