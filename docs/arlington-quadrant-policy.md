# Arlington Pulse Geographic Quadrant Classification Policy

**Version:** 0.3.1 (PROPOSED)
**Status:** PROPOSED, NOT APPROVED. The editorial rules in §3 are the site owner's proposed rules, recorded for documentation. They are not approved for use. Items marked **PROVISIONAL** or **UNRESOLVED** must be settled before approval. Nothing in this document is an official boundary.
**Applies to:** Arlington Pulse article integrations (Letterman → website hub card and article page).
**Does not apply to:** Dallas or Fort Worth hubs; subscriber quadrant selections in `api/subscribe.js` (subscriber choices, not article classifications).

---

## 1. Purpose and scope

Each Arlington Pulse article carries one quadrant value. That value sets the hub card's `data-quadrant` attribute and badge, and the hub's quadrant filter reads it. This policy makes geographic classification consistent across future Letterman integrations, so two people or two Claude sessions classifying the same article reach the same answer.

The policy covers the editorial rules, the City of Arlington's published planning-area descriptions (kept separate), the reference-line convention, overlap and gap handling, the ALL fallback and manual review, evidence to record, test cases, the hub behavior question, and the revision process.

It does not change existing cards, articles, application code, or Vercel configuration. Each of those is a separate change requiring its own approval.

---

## 2. Sources

Two kinds of rules are used. They are kept separate and must not be merged.

### 2A. City of Arlington planning-area descriptions (reference only, PROVISIONAL)

- Source: City of Arlington, *Comprehensive Plan: 99 Square Miles* (adopted 2015), planning-area descriptions at printed pages approximately 147–156.
  - Document: https://www.arlingtontx.gov/files/assets/city/v/3/planning-and-development-services/documents/long-range-planning/comprehensive-plan-99-square-miles.pdf
  - City Comprehensive Plan page: https://arlingtontx.gov/CompPlan
- The descriptions are:
  - North Arlington (north of I-30)
  - East Arlington (east of Collins Street between I-30 and I-20)
  - Central Arlington (between Fielder Road, Collins Street, I-30 and I-20)
  - West Arlington (west of Fielder Road between I-30 and I-20)
  - South Arlington (south of I-20)

**Status of the October 2026 update: UNRESOLVED.** The City's *Innovate Arlington* update was not verified as adopted. As of 2026-10-10, the findings were:
- The City released the draft plan in August 2026 for public review: https://www.arlingtontx.gov/News-Articles/2026/August/Innovate-Arlington-Draft-Comprehensive-Plan-Available-for-Review
- A Fort Worth Report article dated 2026-08-26 says the plan was still seeking feedback ahead of initial adoption in November: https://fortworthreport.org/2026/08/26/arlingtons-20-year-plan-still-seeking-community-feedback-ahead-of-initial-adoption-in-november/
- The City's steering committee schedule lists meetings on 2026-09-17, 2026-11-05 and 2026-12-03, and earlier City material points to adoption at the end of 2026.
- No City Council adoption record was found. The City's own Council minutes and the final adopted text were **not** checked.

**Limitation recorded:** The adoption status was verified only by web search. Until the City's official adopted text is checked, the 2015 descriptions are provisional. Before approval, the owner must confirm (a) whether the update has been adopted and (b) whether it changes any planning-area description or map.

### 2B. Arlington Pulse editorial classification rules (PROPOSED)

These are the site owner's rules, defined in §3. Central and East use the City's wording as a working reference. They are editorial rules, not City-published boundaries.

### 2C. Verification tools (approximate, not authoritative)

OpenStreetMap road geometry (Overpass) and geocoding (Nominatim) were used to check test cases. They are not a source for boundaries. Any location result must be confirmed at building level before it is relied on (§6, §7).

---

## 3. Definitions (owner's proposed editorial rules, PROPOSED)

| Value (`data-quadrant`) | Badge | Rule | Relation to City description (2A) |
|---|---|---|---|
| `north` | NORTH | North of Interstate 30 (I-30). | Same as City "North Arlington (north of I-30)". |
| `south` | SOUTH | South of Interstate 20 (I-20). | Same as City "South Arlington (south of I-20)". |
| `central` | CENTRAL | Within the area bounded by Fielder Road, Collins Street, I-30 and I-20. | Same as City "Central Arlington". |
| `east` | EAST | East of Collins Street, between I-30 and I-20. | Same as City "East Arlington". |
| `all` | ALL | General Arlington content, multi-quadrant content, or locations that cannot confidently be assigned. | Editorial fallback (§5). |

Values are lowercase in `data-quadrant`. Badge text is the uppercase form of the same value.

**Exactly five values are used:** `north`, `south`, `central`, `east`, and `all`. No other classification value exists or is proposed.

**Locations between I-30 and I-20 that are west of Fielder Road and outside the defined Central area** (the City's West Arlington description) are classified `all`. They are **never** classified CENTRAL to fill a gap.

**`all` does not mean citywide.** It means the story has no single quadrant under the rules. A story about one specific venue in an uncovered area is still `all`, while keeping its actual venue location and article details. Citywide and multi-quadrant stories are also `all`.

**Manual-review flag, separate from the classification.** A story that needs an editorial decision carries a review flag or documentation note alongside its value. The flag is not a classification value, and no quadrant value is created for review.

---

## 4. Boundary and overlap rules

### 4.1 Precedence between EAST and CENTRAL

Within the I-30 to I-20 band, EAST is east of Collins Street and CENTRAL is inside the Fielder-to-Collins area. These do not overlap. Where a location falls in the band east of Collins, it is EAST, and never CENTRAL. The band is not treated as CENTRAL by default.

### 4.2 NORTH and SOUTH

NORTH is north of I-30 across all longitudes. SOUTH is south of I-20 across all longitudes. A location north of I-30 is NORTH whether it is east or west of Collins or Fielder, and likewise for SOUTH.

### 4.3 Reference-line and road-boundary convention (PROVISIONAL)

- **Reference line:** the **highway centerline** of I-30 and of I-20. This is provisional until the policy is approved.
- **Review distance:** flag a location for editorial review if it is **within 100 metres** of a relevant boundary. Relevant boundaries are the I-30 and I-20 centerlines, and, for the CENTRAL and EAST split, Collins Street and Fielder Road.
- **Address on a boundary road:** flag for review if the address is **on Collins Street or Fielder Road**, regardless of distance.
- A flagged location is classified `all` until the owner approves it. It is not auto-assigned to a quadrant.

**UNRESOLVED:** the 100-metre margin, the centerline convention, and the treatment of addresses on Collins or Fielder are proposed, not approved. The owner must confirm them.

### 4.4 Gaps and uncovered areas

Not covered by a quadrant. Must not be silently assigned to CENTRAL, EAST, NORTH, or SOUTH:

1. **Between I-30 and I-20, west of Fielder Road, outside the Central area.** Classify `all`. Documentation note: the story's actual location is kept. Locations west of Fielder that are north of I-30 or south of I-20 are NORTH or SOUTH under §4.2, not gaps.
2. **Locations outside City limits** or outside Arlington. Classify `all`, flag for review.
3. **Locations near the ends of I-30 or I-20**, where the interstate leaves the city and "north of" or "south of" cannot be determined from the highway alone. Classify `all`, flag for review.
4. **Locations whose coordinate cannot be confirmed** to be on one side of the reference line. Classify `all`, flag for review.

---

## 5. ALL fallback and manual review

Use `all` when classification is uncertain. Never invent a location, and never force a quadrant to make a card look complete.

| Situation | Classification |
|---|---|
| General Arlington content, or citywide coverage | `all` |
| Several locations in different quadrants with no single primary location | `all` |
| One headline subject, with only incidental mentions of other locations | Quadrant of the headline subject |
| No address, or the address cannot be verified | `all` |
| Address outside Arlington | `all`, flag for review |
| Location in a gap (§4.4) | `all`, flag for review |
| Venue-specific story in an uncovered area (no single quadrant under the rules) | `all`, keeps venue location and article details, review note if uncertain |
| Within 100 m of a relevant boundary, or address on Collins or Fielder (§4.3) | `all`, flag for review |
| Confidence is medium or low for any reason | `all` |

**Manual review.** A flagged item is recorded with its evidence (§6) and marked for owner review. The owner decides whether a quadrant applies, and the decision is recorded before any hub card changes. A reviewer may not assign a quadrant to a gap or boundary case without that decision.

---

## 6. Evidence to record when proposing a quadrant

Each proposal must include a record with these fields. The record lives in the change description or PR, not in public HTML.

- Article identifier (Letterman article ID and proposed slug)
- Address or addresses used, and where each appears in the source (for example, "content block 1, paragraph 2")
- Location method (street address, venue name, or other) and the tool used
- **Coordinate precision:** building, street, or area. A street-level result is not building-level and must be recorded as a limitation.
- Coordinate and its source
- Side of I-30 and I-20, measured from the centerline
- Side of Collins Street and Fielder Road
- Distance from the nearest relevant boundary, in metres
- Boundary flag: within 100 m, or on Collins or Fielder (yes or no)
- City reference used (§2A), with page and the adoption-status note
- Proposed value and confidence (`high`, `medium`, or `low`)
- Reason, in one or two sentences
- **Unverified items and limitations**
- Owner decision and date, once given

A `medium` or `low` result is classified `all` unless the owner overrides it in writing.

---

## 7. Test cases

Coordinates are approximate and come from the tools in §2C. Outcomes marked **provisional** or **unresolved** must be confirmed before use.

| # | Case | Evidence | Outcome | Status |
|---|---|---|---|---|
| T1 | **NORTH.** River Legacy Park, as a park | OpenStreetMap park features span approx. 32.78–32.81 N, −97.13 to −97.05 W. The sampled I-30 corridor (approx. −97.26 to −97.05 W) lies between 32.7585 and 32.7608 N. The park is therefore at least about 2 km north of I-30. | `north` for the park as a park | Supported. The park is not a venue. The festival location is tested separately in T2. |
| T2 | **NORTH, provisional.** River Legacy festival venue, 701 NW Green Oaks Blvd | Two Nominatim street-level results for NW Green Oaks Blvd: approx. 32.7626 N, −97.1487 W and approx. 32.7701 N, −97.1470 W. Both are north of the sampled I-30 corridor (32.7585 to 32.7608 N). The first is about 200 m north of the nearest sampled I-30 point, and the second about 1.0 km north. The OpenStreetMap road segment's bounding box (32.7606 to 32.7645 N) straddles the I-30 latitude band, so the road itself does not clearly lie north of I-30 at that longitude. **No building-level coordinate for the Nature Center or the festival site was found.** An OpenStreetMap name search returned park features but no Nature Center building. | **NORTH, PROVISIONAL.** Not confirmed. | **UNRESOLVED: building-level verification is unavailable.** Required: a building-level coordinate from the organizer or the City's GIS parcel data, and confirmation that it is at least 100 m north of the I-30 centerline. |
| T3 | **SOUTH.** A business south of I-20 | Business address south of I-20 | `south` | Expected. Confirm against the approved reference line. |
| T4 | **CENTRAL.** Business inside the Fielder–Collins area between I-30 and I-20 | Business address in that area | `central` | Expected. Confirm against the approved map. |
| T5 | **EAST.** Business between I-30 and I-20, east of Collins | Business address in that area | `east` | Expected. Confirm against the approved map. |
| T6 | **ALL.** Multi-venue roundup across several quadrants | Article names venues in more than one quadrant, with no single subject | `all` | Per §5 |
| T7 | **ALL.** General Arlington or citywide event | No single address | `all` | Per §5 |
| T8 | **Boundary road.** Address on Collins Street or Fielder Road, or a location within 100 m of the I-30 or I-20 centerline | Address or distance measured | `all`, flag for review | Per §4.3 (provisional) |
| T9 | **Uncovered area.** Venue-specific story, business west of Fielder between I-30 and I-20 | Business address in that area | `all`, with review note | Per §4.4. Keeps the venue location and article details. Not CENTRAL. |
| T10 | **Uncovered area.** Venue near an end of I-30 or I-20, where the highway leaves the city | Location where the reference line is unclear | `all`, flag for review | Per §4.4 |
| T11 | **Entertainment District, venue by venue** (not one quadrant for the whole district) | AT&T Stadium, approx. 32.7479 N, −97.0928 W. Globe Life Field, approx. 32.7476 N, −97.0841 W. Both are about 1.2–1.3 km south of the sampled I-30 corridor, so neither is NORTH under §3. Their EAST or CENTRAL status depends on where Collins Street runs at that latitude, which **could not be retrieved** from the tools used. Texas Live!, Six Flags Over Texas and Hurricane Harbor were **not measured**. | **PENDING LOCATION CHECK** for every venue. Not assignable yet. | **UNRESOLVED.** The existing hub cards labeled NORTH on these topics conflict with §3. That conflict is a **separate follow-up** requiring location checks and owner approval. No card is changed by this policy. |

---

## 8. Keeping the badge and `data-quadrant` consistent

- The `data-quadrant` value and the badge class must match exactly. Example: `data-quadrant="north"` pairs with `<span class="quadrant-badge north">NORTH</span>`.
- Allowed values are only `north`, `south`, `central`, `east` and `all`.
- The badge text must equal the uppercase form of the `data-quadrant` value.
- The hub's badge CSS already defines all five values. Adding a value would need a separate approved change to this policy, the badge CSS, and the filter buttons.
- Changing a card's quadrant changes both attributes in the same edit.
- The article page does not carry a quadrant. The hub card is the only place it is written, so the evidence record (§6) is the source of truth.
- Before a hub card is merged, confirm its value matches the evidence record.

---

## 9. Hub behavior for ALL cards (separate proposed change, NOT implemented)

**Intended editorial behavior:** general Arlington and genuinely multi-quadrant stories labeled `all` should appear under every quadrant filter.

**Current state, from the hub code on `main`:**
- The filter script shows a card when its value equals the active filter, or when the card's value is `all`. So `all` cards are already eligible under every filter.
- A CSS rule, `.archive-grid .issue-card:nth-child(n+7) { display: none; }`, hides every card after the sixth. It applies regardless of filter. As a result, `all` cards beyond the first six cannot appear under any filter.

**Conclusion:** the filter logic already matches the intended behavior. The gap is the six-card cap, not the filter. Any change is a **separate proposed implementation change** requiring owner approval. It is not made in this policy task and is not approved.

---

## 10. Revising this policy

1. Any change to a definition, boundary, convention or rule requires written approval from the site owner.
2. Each revision increments the version, records the date, and adds a changelog entry.
3. A boundary change applies to future classifications only. Existing cards are not reclassified automatically. Reclassifying existing cards is a separate change with its own evidence and approval.
4. When the City adopts a new Comprehensive Plan, re-check §2A and §3 against the adopted text and maps before the next approval.
5. Every revision is made on a feature branch and reviewed under the repository's governance (`CLAUDE.md`, `TRANSITION_CONTROL_LOG.md`).

### Changelog

- **0.1 (draft):** Initial draft with boundary placeholders.
- **0.2 (proposed):** Added City planning-area sources, the West gap, boundary and reference-line rules, manual review, and test cases.
- **0.3 (proposed):** Adds owner's rules, a provisional centerline and 100 m review convention, the status of the October 2026 update (unresolved), River Legacy provisional with the building-level limitation recorded, venue-by-venue Entertainment District handling, and the ALL hub-behavior analysis (separate change). Not approved.
- **0.3.1 (proposed):** Removes the suggestion that a WEST value be decided later; WEST is not needed. Exactly five values. Clarifies that `all` is not necessarily citywide, and that a manual-review flag is separate from the value.

---

## 11. Unresolved issues

Each item must be settled before approval.

1. **Innovate Arlington update:** verify adoption, and whether any planning-area description changes. Adoption was not verified (§2A).
2. **Reference plan:** confirm the 2015 descriptions as provisional, or replace them with the adopted update.
3. **Reference-line convention:** confirm the I-30 and I-20 centerline convention (§4.3).
4. **Review margin:** confirm the 100 m margin (§4.3).
5. **Address on Collins or Fielder:** confirm review regardless of distance (§4.3).
6. **River Legacy festival venue:** building-level coordinate required. Provisional NORTH (T2).
7. **Entertainment District venues:** location checks for each venue, including Collins Street's position at that latitude (T11). Separate follow-up: existing hub NORTH labels conflict with §3, and changing them needs approval.
8. **Hub six-card cap (§9):** separate proposed implementation change requiring approval.
