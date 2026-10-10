# Arlington Pulse Geographic Quadrant Classification Policy

**Version:** 0.3.2 (PROPOSED)
**Status:** PROPOSED, NOT APPROVED. The editorial rules in §3 are the site owner's proposed rules, recorded for documentation. They are not approved for use. Items marked **PROVISIONAL** or **UNRESOLVED** must be settled before approval. Nothing in this document is an official boundary.
**Applies to:** Arlington Pulse article integrations (Letterman → website hub card and article page).
**Does not apply to:** Dallas or Fort Worth hubs; subscriber quadrant selections in `api/subscribe.js` (subscriber choices, not article classifications).

---

## 1. Purpose and scope

Each Arlington Pulse article carries one quadrant value. That value sets the hub card's `data-quadrant` attribute and badge, and the hub's quadrant filter reads it. This policy makes geographic classification consistent across future Letterman integrations, so two people or two Claude sessions classifying the same article reach the same answer.

The policy covers the editorial rules, the City of Arlington's published planning-area descriptions (kept separate), the reference-line convention, the precision required for location evidence, overlap and gap handling, the `all` fallback and manual-review flag, evidence to record, test cases, the hub behavior question, and the revision process.

It does not change existing cards, articles, application code, or Vercel configuration. Each of those is a separate change requiring its own approval.

---

## 2. Sources

Two kinds of rules are used. They are different in kind and must not be merged.

### 2A. City of Arlington planning-area descriptions (reference only, PROVISIONAL)

- Source: City of Arlington, *Comprehensive Plan: 99 Square Miles* (adopted March 2015), planning-area descriptions at printed pages approximately 147–156.
  - Document: https://www.arlingtontx.gov/files/assets/city/v/3/planning-and-development-services/documents/long-range-planning/comprehensive-plan-99-square-miles.pdf
  - City Comprehensive Plan page: https://arlingtontx.gov/CompPlan
- The City's descriptions are:
  - North Arlington (north of I-30)
  - East Arlington (east of Collins Street between I-30 and I-20)
  - Central Arlington (between Fielder Road, Collins Street, I-30 and I-20)
  - West Arlington (west of Fielder Road between I-30 and I-20)
  - South Arlington (south of I-20)

**Status of the Innovate Arlington update: NOT VERIFIED AS ADOPTED.** Nothing in this document implies that the updated plan has been adopted. As of 2026-10-10:

- The City's Innovate Arlington engagement page lists the plan as in "Phase 3: Plan Review & Adoption," described as "January 2026 through early 2027." It also lists a Comprehensive Plan Steering Committee meeting on December 3, 2026: https://www.arlingtonlistens.com/comprehensive-plan
- The City published a draft plan notice in August 2026: https://www.arlingtontx.gov/News-Articles/2026/August/Innovate-Arlington-Draft-Comprehensive-Plan-Available-for-Review (the article title was confirmed by search; the full text was not retrieved).
- **Adoption date: not verified.** The City's stated window runs to early 2027. No City Council adoption action was found.

**Limitation recorded:** These facts come from retrieval of City web pages. The City Council record and the final adopted text were not checked. Before approval, the owner must confirm (a) whether the update has been adopted and when, and (b) whether it changes any planning-area description or map. Until then, the 2015 descriptions are provisional.

### 2B. Arlington Pulse editorial classification rules (PROPOSED)

The site owner's editorial rules are defined in §3. They are not City-published boundaries. Where they use the same words as the City's description, they match the 2015 City description provisionally, but they remain Arlington Pulse rules. A §3 rule does not become a City boundary because its wording is similar.

### 2C. Verification tools (approximate, not authoritative)

OpenStreetMap road geometry (Overpass) and geocoding (Nominatim) were used to check test cases. They are not a source for boundaries. Their precision is limited, and the precision rules in §6 apply to any location result.

---

## 3. Definitions (owner's proposed editorial rules, PROPOSED)

| Value (`data-quadrant`) | Badge | Rule | Relation to the 2015 City description (2A) |
|---|---|---|---|
| `north` | NORTH | North of Interstate 30 (I-30). | Matches the 2015 City description (provisional). |
| `south` | SOUTH | South of Interstate 20 (I-20). | Matches the 2015 City description (provisional). |
| `central` | CENTRAL | Within the area bounded by Fielder Road, Collins Street, I-30 and I-20. | Matches the 2015 City description (provisional). |
| `east` | EAST | East of Collins Street, between I-30 and I-20. | Matches the 2015 City description (provisional). |
| `all` | ALL | General Arlington content, multi-quadrant content, or a location that cannot confidently be assigned under these rules. | Not a City description. Editorial fallback (§5). |

Values are lowercase in `data-quadrant`. Badge text is the uppercase form of the same value.

**Exactly five classification values are used:** `north`, `south`, `central`, `east`, and `all`. No other classification value exists or is proposed.

**Manual-review flag, separate from the classification.** A story that needs an editorial decision carries a **manual-review flag** alongside its value. The flag is not a classification value, and no quadrant value is created for review.

**Locations between I-30 and I-20 that are west of Fielder Road and outside the defined Central area** are classified `all`, with a manual-review flag where the location is uncertain. They are **never** classified CENTRAL to fill a gap.

**`all` does not mean citywide.** It means the story has no single quadrant under these rules. A story about one specific venue in an uncovered area is still `all`, while keeping its actual venue location and article details.

---

## 4. Boundary and overlap rules

### 4.1 Precedence between EAST and CENTRAL

**EAST takes precedence over CENTRAL within the defined I-30-to-I-20 band.** A location in that band that is east of Collins Street is EAST. CENTRAL applies only to locations in the band that are west of Collins Street and east of Fielder Road. A location in the band is never classified CENTRAL merely because it is in the band. The band is not treated as CENTRAL by default. Addresses exactly on Collins Street are handled under §4.3.

### 4.2 NORTH and SOUTH

NORTH is north of I-30 across all longitudes. SOUTH is south of I-20 across all longitudes. A location north of I-30 is NORTH whether it is east or west of Collins or Fielder, and likewise for SOUTH.

### 4.3 Reference-line and road-boundary convention (PROVISIONAL)

- **Reference line:** the **highway centerline** of I-30 and of I-20. Provisional until the policy is approved.
- **Buffer:** a location **within 100 metres** of the I-30 or I-20 centerline is flagged for manual review and classified `all` until the owner approves it.
- **Collins Street and Fielder Road:** these define the CENTRAL and EAST boundary only **within the I-30-to-I-20 band**. Inside that band, an address **on Collins Street or Fielder Road**, or a location within 100 metres of either road, is flagged for manual review and classified `all` until the owner approves it.
- **Outside the band:** north of I-30, the NORTH rule (§4.2) applies. South of I-20, the SOUTH rule applies. A Collins Street or Fielder Road address there is not flagged on that basis alone. It is flagged only if location uncertainty independently requires it (§4.4, §6).
- **Precision:** a location inside the buffer requires building-level or equivalent precise verification (§6).

**UNRESOLVED:** the centerline convention, the 100-metre buffer, and the band-limited Collins and Fielder rule are proposed, not approved. The owner must confirm them.

### 4.4 Gaps and uncovered areas

Not covered by a quadrant. Must not be silently assigned to CENTRAL, EAST, NORTH, or SOUTH:

1. **Between I-30 and I-20, west of Fielder Road, outside the Central area.** Classify `all`. The story's actual location is kept. Locations west of Fielder that are north of I-30 or south of I-20 are NORTH or SOUTH under §4.2, not gaps.
2. **Locations outside City limits** or outside Arlington. Classify `all` and add a manual-review flag.
3. **Locations near the ends of I-30 or I-20**, where the interstate leaves the city and "north of" or "south of" cannot be determined from the highway alone. Classify `all` and add a manual-review flag.
4. **Locations whose side of the reference line cannot be confidently established** from the available evidence. Classify `all` and add a manual-review flag.

---

## 5. ALL fallback and manual-review flag

Use `all` when a location cannot confidently be assigned under the defined rules. Never invent a location, and never force a quadrant to make a card look complete.

**Substantive coverage.** A location receives substantive coverage in a story when the story describes it at more than passing length, such as a dedicated paragraph or section, or when it is the subject of the headline. A location named only in passing is an **incidental mention**. Incidental mentions do not affect the classification.

**Threshold: UNRESOLVED.** The owner must confirm this definition of substantive coverage.

| Situation | Classification |
|---|---|
| General Arlington content, or citywide coverage | `all` |
| Two or more locations in different quadrants each receive substantive coverage, and no other documented rule applies | `all` |
| One location receives substantive coverage and the other locations are incidental mentions | Quadrant of the substantively covered location |
| No address, or the address cannot be verified | `all` |
| Address outside Arlington | `all` with manual-review flag |
| Location in a gap (§4.4) | `all` with manual-review flag |
| Venue-specific story in an uncovered area (no single quadrant under the rules) | `all`, keeps venue location and article details, manual-review flag if uncertain |
| Inside the buffer, or an address on Collins or Fielder inside the I-30-to-I-20 band (§4.3) | `all` with manual-review flag |
| Location cannot confidently be assigned under the defined rules | `all` with manual-review flag |
| Confidence is medium or low for any reason | `all` |

**Manual review.** A flagged item is recorded with its evidence (§6) and marked with a manual-review flag. The owner decides whether a quadrant applies, and the decision is recorded before any hub card changes. A reviewer may not assign a quadrant to a gap, a buffer case, or a band-road case without that decision.

---

## 6. Evidence to record, and location precision

Each proposal must include a record with these fields. The record lives in the change description or PR, not in public HTML.

- Article identifier (Letterman article ID and proposed slug)
- Address or addresses used, and where each appears in the source (for example, "content block 1, paragraph 2")
- Location method (street address, venue name, or other) and the tool used
- Coordinate precision: building, street, or area
- Coordinate and its source
- Side of I-30 and I-20, measured from the centerline
- Side of Collins Street and Fielder Road
- Distance from the nearest relevant boundary, in metres
- Buffer and road flags (inside the 100 m buffer; address on Collins or Fielder inside the band; yes or no)
- City reference used (§2A), with the adoption-status note
- Proposed value and confidence (`high`, `medium`, or `low`)
- Reason, in one or two sentences
- Unverified items and limitations
- Owner decision and date, once given

**Precision rule (PROVISIONAL).**
- **Building-level or equivalent precise verification is required** when the location is inside the 100 m buffer, or when the available evidence cannot confidently establish which side of a boundary the location is on.
- **Outside the buffer,** lower-precision evidence (street or area) may be recorded with its limitations if it is sufficient to establish the classification.
- **Do not claim that an unverified location is confirmed.** A result that depends on lower-precision evidence is recorded as provisional and states its limitation.

A `medium` or `low` result is classified `all` unless the owner overrides it in writing.

---

## 7. Test cases

Coordinates are approximate and come from the tools in §2C. Outcomes marked **provisional** or **unresolved** must be confirmed before use.

| # | Case | Evidence | Outcome | Status |
|---|---|---|---|---|
| T1 | **NORTH.** River Legacy Park, as a park | OpenStreetMap park features span approx. 32.78–32.81 N, −97.13 to −97.05 W. The sampled I-30 corridor (approx. −97.26 to −97.05 W) lies between 32.7585 and 32.7608 N. The park is at least about 2 km north of I-30. | `north` for the park as a park | Supported. The park is not a venue. The festival location is tested in T2. |
| T2 | **NORTH, provisional.** River Legacy festival venue, 701 NW Green Oaks Blvd | Two Nominatim street-level results for NW Green Oaks Blvd: approx. 32.7626 N, −97.1487 W and approx. 32.7701 N, −97.1470 W. The first is about 200 m north of the nearest sampled I-30 point (32.7608 N), and the second about 1.0 km north. **The reported street-level distance is outside the 100 m buffer.** However, the OpenStreetMap road segment's bounding box (32.7606 to 32.7645 N) straddles the I-30 latitude band, so the street evidence cannot confidently establish which side of I-30 the venue is on. No building-level coordinate for the Nature Center or festival site was found. The park centroid is **not** evidence of the venue's location. | **NORTH, PROVISIONAL.** Not confirmed. | **UNRESOLVED: building-level verification is unavailable.** Required: a building-level or equivalent precise coordinate from the organizer or the City's GIS parcel data, confirming the venue is north of the I-30 centerline. |
| T3 | **SOUTH.** A business south of I-20 | Business address south of I-20 | `south` | Expected. Confirm against the approved reference line. |
| T4 | **CENTRAL.** Business inside the Fielder–Collins area between I-30 and I-20 | Business address in that area | `central` | Expected. Confirm against the approved map. |
| T5 | **EAST.** Business between I-30 and I-20, east of Collins | Business address in that area | `east` | Expected. EAST takes precedence (§4.1). Confirm against the approved map. |
| T6 | **ALL.** Story with substantive coverage of several locations in different quadrants | Article gives substantive coverage to venues in more than one quadrant, with no other documented rule applying | `all` | Per §5 |
| T7 | **ALL.** General Arlington or citywide event | No single address | `all` | Per §5 |
| T8 | **Band-road and buffer.** Address on Collins Street or Fielder Road inside the I-30-to-I-20 band, or a location within 100 m of the I-30 or I-20 centerline | Address or distance measured | `all` with manual-review flag | Per §4.3 (provisional). Building-level verification required inside the buffer (§6). |
| T9 | **Uncovered area.** Venue-specific story, business west of Fielder between I-30 and I-20 | Business address in that area | `all` with manual-review flag if uncertain | Per §4.4. Keeps the venue location and article details. Not CENTRAL. |
| T10 | **Uncovered area.** Venue near an end of I-30 or I-20, where the highway leaves the city | Location where the reference line is unclear | `all` with manual-review flag | Per §4.4 |
| T11 | **Entertainment District, venue by venue** (not one quadrant for the whole district) | AT&T Stadium, approx. 32.7479 N, −97.0928 W. Globe Life Field, approx. 32.7476 N, −97.0841 W. Both are about 1.2–1.3 km south of the sampled I-30 corridor, so neither is NORTH under §3. Their EAST or CENTRAL status depends on where Collins Street runs at that latitude, which **could not be retrieved** from the tools used. Texas Live!, Six Flags Over Texas and Hurricane Harbor were **not measured**. | **PENDING LOCATION CHECK** for every venue. Not assignable yet. | **UNRESOLVED.** The existing hub cards labeled NORTH on these topics conflict with §3. That conflict is a **separate follow-up** requiring location checks and owner approval. No card is changed by this policy. |
| T12 | **Incidental mention.** Story substantively about a Central venue, with a second venue named in one sentence | Headline and paragraphs cover one venue; the second venue receives no substantive coverage | Quadrant of the substantively covered venue (CENTRAL, if confirmed) | Per §5. Provisional until the Central location is verified. |

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
- **0.3 (proposed):** Owner's rules, provisional centerline and 100 m convention, the Innovate Arlington status (unresolved), River Legacy provisional, venue-by-venue Entertainment District handling, and the ALL hub-behavior analysis (separate change). Not approved.
- **0.3.1 (proposed):** Removed the suggestion that a WEST value be decided later. Exactly five values. `all` is not necessarily citywide, and the manual-review flag is separate from the value.
- **0.3.2 (proposed):** Separates City descriptions from editorial rules ("Matches the 2015 City description (provisional)"). Adds the precision rule (§6) and the substantive-coverage and incidental-mention definitions (§5). Limits the Collins and Fielder rule to the I-30-to-I-20 band. States EAST precedence explicitly. Replaces the Innovate Arlington schedule claims with City-sourced facts and removes the unsourced press claims. Standardizes "manual-review flag." Revises T2 (River Legacy). Adds T12. Not approved.

---

## 11. Unresolved issues

Each item must be settled before approval.

1. **Innovate Arlington update:** verify adoption and its date, and whether any planning-area description or map changes. The City's stated window runs to early 2027, and adoption is not verified (§2A).
2. **Reference plan:** confirm the 2015 descriptions as provisional, or replace them with the adopted update.
3. **Reference-line convention:** confirm the I-30 and I-20 centerline convention (§4.3).
4. **Buffer:** confirm the 100 m buffer (§4.3).
5. **Collins and Fielder rule:** confirm that it applies only within the I-30-to-I-20 band (§4.3).
6. **Substantive coverage:** confirm the definition in §5.
7. **River Legacy festival venue:** building-level or equivalent precise location required. NORTH remains provisional (T2).
8. **Entertainment District venues:** location checks for each venue, including Collins Street's position at that latitude (T11). Separate follow-up: the existing hub NORTH labels conflict with §3, and changing them needs approval.
9. **Hub six-card cap (§9):** separate proposed implementation change requiring approval.
