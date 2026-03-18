# SCORING POLICY — Token Hunter

## 1. Cíl scoringu

Scoring nemá dokazovat „nejlepší model na světě“. Má vybrat **nejvýhodnější volbu pro daný use-case**.

## 2. Hlavní skóre

### Best Buy Score
Složený score z:
- Price Advantage
- Effective Savings
- Use-case Fit
- Reliability
- Confidence
- Friction Penalty
- Expiry Pressure
- Novelty Bonus
- Hype Penalty

## 3. Doporučené váhy pro V1

- Price Advantage: 30
- Use-case Fit: 20
- Confidence: 15
- Reliability: 10
- Effective Savings: 10
- Expiry Pressure: 10
- Novelty Bonus: 5
- Friction Penalty: -10
- Hype Penalty: -10

## 4. Definice jednotlivých složek

### Price Advantage
Jak levná je nabídka vzhledem k relevantním alternativám.

### Effective Savings
Kolik realisticky ušetří uživatel v typickém scénáři.

### Use-case Fit
Jak dobře nabídka sedí na coding/chat/agents/summarization/experimentation.

### Reliability
Jak stabilní je přístupová cesta a jak důvěryhodný je provider/route.

### Confidence
Jak silné a čerstvé jsou důkazy.

### Friction Penalty
Region lock, waitlist, preview frikce, složitý onboarding, nepříjemné limity.

### Expiry Pressure
Časově omezené příležitosti mají vyšší prioritu, ale nesmí kvůli tomu přeskočit nekvalitní deal.

### Novelty Bonus
Lehký bonus za novou relevantní příležitost.

### Hype Penalty
Trest pro hlučnou, ale slabě doloženou nebo málo praktickou novinku.

## 5. Confidence Score

Confidence vzniká z:
- source tier,
- počtu nezávislých důkazů,
- stáří dat,
- parser confidence,
- přítomnosti oficiální evidence,
- konfliktů mezi zdroji.

## 6. Game Changer classifier v1

Pravidlově:

Game changer =
- výrazná cenová výhoda **nebo**
- výrazná capability změna **nebo**
- zásadní workflow zjednodušení

a zároveň:
- vysoká relevance,
- dostatečná confidence,
- nízké nebo zvládnutelné frikce.

### Výstupní štítky
- Hype
- Watch
- Relevant
- Game changer

## 7. Compare policy

Compare obrazovka musí vždy ukázat:
- #1 recommendation,
- 2–4 alternatives,
- proč vítěz vyhrál,
- v čem prohrává,
- caveats,
- confidence.

## 8. Guardrails

Scoring se nesmí zvrtnout v:
- black-box magii,
- neauditovatelná rozhodnutí,
- marketingové zvýhodnění sponzorů,
- rigidní jedno číslo bez kontextu.

## 9. Budoucí rozšíření

Později přidat:
- personal budget weighting,
- preference weighting,
- historical stability,
- personalized route switching recommendations,
- cohort-based scoring templates.
