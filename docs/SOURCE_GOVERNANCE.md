# Source Governance Policy

## Purpose

This project does not treat every RSS item as equally reliable. The source
registry defines how an item may be used before it reaches the daily report or
the rapid-assessment workbench.

## Source tiers

| Tier | Source type | Current examples | Permitted use |
| --- | --- | --- | --- |
| T1 | Official primary source | U.S. SEC, U.S. CFTC | Confirm that authority's own action, release, or statement. It does not automatically prove market impact. |
| T2 | Project primary source | Chainlink Blog | Confirm the project's own announcement only. It is not independent evidence about the broader market. |
| T3 | Specialist media and market-data media | CoinDesk, Cointelegraph, The Block, Bitcoin Magazine, CoinMarketCap | Discovery and context. Material claims remain pending until corroborated by a primary source or another independent source. |
| T4 | Unreviewed source | Any domain outside the registry | Not confirmed evidence. It is shown only as an unverified lead. |

## Current decisions

- SEC and CFTC are T1 because their releases are first-party records of their
  own official actions.
- Chainlink Blog is T2 because it is operated by the project it describes.
- CoinDesk, Cointelegraph, The Block, Bitcoin Magazine, and CoinMarketCap are
  T3. They provide useful specialist coverage or market-data context, but are
  not authoritative proof by themselves. Ownership, editorial focus, and platform
  conflicts are surfaced as conflict notes where relevant.
- The Block and Bitcoin Magazine have active RSS feeds and are collected by the
  daily RSS provider. CoinMarketCap is approved in the registry, but no stable
  public RSS endpoint has been confirmed yet; it can be used as a manual or
  future API-backed source.
- The registry intentionally makes T3 items `inference` rather than `fact`.
  This prevents a single media item from being written as a confirmed event.

## System behavior

- Each profile sets a quality score, confidence ceiling, scope of permitted
  claims, and whether confirmation is required.
- Ranking applies a penalty to events that still require confirmation.
- The report has a Source Radar section. It shows the latest available item per
  source, the original headline and summary, the source tier, boundaries of
  use, conflict note when applicable, and a follow-up instruction.
- Any source outside the registry becomes T4 by default.

## Change control

Reviewed defaults live in `src/crypto_intel/services/source_governance.py`.
`config/default.yaml` can override a reviewed profile without changing code.
Before adding a source, document its ownership, editorial or publication
method, source type, expected coverage, conflicts, and the exact claims it can
support. Reassess the registry at least quarterly and after major ownership or
policy changes.
