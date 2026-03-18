# SOURCE POLICY — Token Hunter

## 1. Základní pravidlo

Zdroj může dodat:
- truth,
- discovery lead,
- weak signal,
- nebo nic.

Ne všechny zdroje mají stejnou váhu.

## 2. Tiers zdrojů

### Tier 1 — Source of truth
Používá se pro verified pricing a verified offer verdicty.

Sem patří:
- oficiální pricing stránky,
- oficiální docs,
- oficiální release notes,
- oficiální produktové a API stránky.

### Tier 2 — Trusted discovery
Používá se pro objev novinek a sekundární ověření relevance.

Sem patří:
- reputačně silné AI publikace,
- GitHub releases,
- strukturované katalogy a srovnávače,
- technologické blogy s historií důvěryhodnosti.

### Tier 3 — Weak signal
Používá se jen jako stopa, ne jako důkaz.

Sem patří:
- X/Twitter,
- Reddit,
- Discord,
- komunitní chatter,
- neověřené blogposty bez primárních důkazů.

## 3. Povinná metadata zdroje

Každý zdroj musí mít:
- id,
- název,
- typ,
- trust tier,
- owner,
- robots/ToS poznámku,
- refresh policy,
- parser typ,
- fallback postup,
- error budget,
- review status.

## 4. Pravidla ingestu

### Official pricing pages
- nejvyšší priorita pro truth data
- ukládat evidence snapshots
- sledovat změny v čase

### Docs a release notes
- používat pro limity, podmínky, změny dostupnosti, quota a capability notes

### Katalogy a srovnávače
- používat jako discovery a pomocný kontext
- ne jako primární pravdu, pokud odporují oficiálnímu zdroji

### Community signály
- používat pouze jako leady ke zkontrolování

## 5. Conflict policy

Pokud se zdroje rozcházejí:
1. vítězí oficiální zdroj,
2. pokud není oficiální zdroj jasný, položka jde do review queue,
3. pokud je deal vysokého dopadu a neověřený, nesmí do hlavního feedu.

## 6. Freshness policy

### High-volatility data
- pricing
- promo/trial/credit
- rate-limit zásadní pro použitelnost

Vyžadují častější refresh a stale flagging.

### Medium-volatility data
- docs změny,
- release notes,
- katalogy provider routes

### Lower-volatility data
- obecné capability popisy,
- archivní informace,
- stabilní produktové identity

## 7. Evidence policy

Každý zásadní deal musí mít:
- minimálně 1 důvěryhodný evidence pointer,
- uložený captured title,
- captured excerpt,
- captured timestamp,
- source tier,
- parser version,
- last verified.

## 8. Suspicious offer policy

Deal je podezřelý, pokud:
- je extrémně výhodný a chybí mu primární důkaz,
- community claim odporuje official pricing,
- má nejasné podmínky,
- chybí datum expirace a jde o promo/trial,
- parser zachytil nekonzistenci.

Podezřelý deal jde do review queue.

## 9. Source expansion policy

Nový zdroj přidávej jen tehdy, když:
- zvyšuje coverage v důležité oblasti,
- snižuje slepá místa,
- zlepšuje discovery bez masivního noise cost,
- má rozumnou technickou a právní udržitelnost.
