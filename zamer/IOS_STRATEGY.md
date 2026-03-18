# iOS STRATEGY — Token Hunter

## 1. Základní postoj

iOS je pro Token Hunter **spotřební a notifikační vrstva**, ne místo, kde bude běžet crawling a hlavní rozhodovací logika.

## 2. Důvod

Backend musí dělat:
- crawling,
- parsing,
- normalization,
- verification,
- scoring,
- alert orchestration.

iOS má dělat:
- rychlou spotřebu výsledků,
- watchlist,
- push alerts,
- widgety,
- saved picks,
- lehkou lokální cache.

## 3. MVP pro iOS

### Povinné
- Home Radar
- Watchlist
- Deal Detail
- Push alerts
- Saved picks
- Offline last-known snapshots
- Widget „Today’s best buys"

### Nepovinné na startu
- advanced compare tuning,
- budget profile editing,
- research-heavy views,
- admin nebo parser review.

## 4. V2 pro iOS

- compare screen
- budget profile
- saved scenarios
- richer widgets
- notifikace tuning
- share extension
- iCloud sync lokálních preferencí pokud bude dávat smysl

## 5. Tech směr

- native SwiftUI
- shared backend domain contracts
- SwiftData pro lokální cache a preferences
- WidgetKit pro glanceable surfaces
- UserNotifications / APNs pro alerty
- BGTaskScheduler jen jako pomocná synchronizace, ne core dependency

## 6. UX principy

### Glanceability first
Uživatel má na první pohled vidět:
- nejlepší dnešní nabídku,
- nejdůležitější změnu,
- zda něco expiruje,
- zda se objevil lepší deal pro jeho watchlist.

### One-tap verdict
Každý deal detail musí být čitelný během několika sekund.

### Alert restraint
Notifikace musí být vzácné, stručné a užitečné.

## 7. iOS guardrails

- nepočítat s garantovaným background refreshem,
- necpát do iOS klienta scraper logiku,
- nebudovat mobil jako mini admin panel,
- držet mobilní scope úzký a pravidelně používatelný.

## 8. Widget strategie

Widget má být důvodem k dennímu návratu.

Doporučené widget stavy:
- today’s best buys
- expiring soon
- best free option today
- cheaper route found

## 9. Notifikační strategie

Povolené typy:
- new best buy in watched category
- cheaper route found
- free tier appeared
- expiring deal
- game changer candidate only for high-confidence items

Nepovolené typy:
- spammy research alerts,
- příliš časté minor price noise změny,
- neověřené novinky.
