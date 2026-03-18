# SCOPE — Token Hunter

## 1. Scope v jedné větě

Token Hunter je savings-first produkt pro sledování a doporučování nejvýhodnějších LLM/AI dealů, access routes a relevantních novinek, s backend intelligence a iOS-ready architekturou.

## 2. V1 — povinné jádro

### A. Source Registry
Musí existovat centrální registr zdrojů:
- official pricing pages,
- official docs,
- official changelogy,
- provider/model katalogy,
- trusted AI blogs/newsletters,
- release/discovery feedy.

### B. Normalizovaný katalog
Normalizované entity:
- provider,
- model,
- access route,
- plan,
- pricing item,
- free tier,
- promo/trial/credit,
- restrictions,
- evidence snapshot,
- last verified time.

### C. Use-case profily
Předdefinované režimy pro rozhodování:
- coding cheap,
- coding best value,
- chat cheap,
- agent workflows,
- experimentation/free,
- batch summarization,
- local/open-source oriented.

### D. Best Buy Engine
Musí umět vrátit:
- nejlepší volbu,
- 2–4 alternativy,
- proč,
- rizika,
- estimated savings,
- confidence.

### E. Deal Feed
Jedna hlavní feed vrstva:
- nové dealy,
- změny cen,
- expirující nabídky,
- nově dostupné free cesty,
- levnější access route,
- nové watch-worthy releases.

### F. Alerts
Nutné typy alertů:
- model watchlist,
- provider watchlist,
- use-case watchlist,
- „notify me when something clearly better appears“.

### G. Deal Detail
Každý deal musí mít:
- headline,
- verdict,
- podmínky,
- zdroje,
- čas posledního ověření,
- koho se týká,
- limity,
- alternativy.

### H. iOS-ready API contract
Backend musí od začátku poskytovat čisté API pro:
- home feed,
- alerts,
- watchlist,
- compare,
- deal detail,
- search,
- saved picks.

## 3. V1.5 — silné rozšíření

- osobní budget profil,
- kalkulačka měsíční útraty,
- doporučení „switch route“,
- bundle detector,
- research digest,
- badge: hype / watch / relevant / game changer.

## 4. V2

- personal spend tracking,
- email digests,
- Telegram/Discord notifikace,
- týmové watchlisty,
- community-submitted leads s moderací,
- referral / affiliate vrstva,
- dlouhodobý savings history.

## 5. Out of scope na startu

Do V1 nepatří:
- vlastní benchmark lab,
- vlastní inference gateway,
- platební integrace a nákup z appky,
- wallet management,
- community fórum,
- všeobecný coupon web mimo AI,
- široké scraping pokrytí „všeho na internetu“,
- sentiment analysis social sítí jako core,
- enterprise procurement suite.

## 6. Platform scope

### Web
Primární místo pro:
- detailní srovnání,
- filtrování,
- compare,
- onboarding,
- admin review.

### iOS
Primární místo pro:
- alerts,
- watchlist,
- widget,
- rychlé rozhodnutí,
- daily radar,
- saved picks.

### Backend
Jediné místo pro:
- crawling,
- parsing,
- scoring,
- deduplikaci,
- trust engine,
- alert orchestration,
- change detection.

## 7. Typy dat

### Truth data
- ceny,
- plány,
- free tiers,
- trialy,
- kredity,
- regiony,
- expirace,
- billing podmínky,
- rate limity pokud zásadně mění použitelnost.

### Discovery data
- launch posty,
- blogy,
- Product Hunt-like objevy,
- release notes,
- nové knihovny,
- nové appky,
- release feedy.

### Derived data
- best buy score,
- savings estimate,
- confidence,
- novelty,
- friction,
- trust,
- game-changer verdict.

## 8. Scope guardrails

Každá feature musí projít testem:
1. Zvyšuje úsporu?
2. Zvyšuje důvod vracet se do appky?
3. Zvyšuje důvěru?
4. Zkracuje čas k rozhodnutí?
5. Nenese neúměrnou crawling / legal / maintenance zátěž?

Když neprojde aspoň 3 z 5, nepatří do nejbližší roadmapy.
