# Arlington Pulse Geographic Quadrant Classification Policy

**Version:** 0.2 (PROPOSED)
**Status:** PROPOSED, NOT APPROVED. The editorial rules in §3 are proposed by the site owner for documentation and have not been approved for use. Nothing here is an official boundary until the site owner approves it in writing.
**Applies to:** Arlington Pulse article integrations (Letterman → website hub card and article page).
**Does not apply to:** Dallas or Fort Worth hubs; subscriber quadrant selections in `api/subscribe.js` (those are subscriber choices, not article classifications, and are not changed by this policy).

---

## 1. Purpose and scope

Each Arlington Pulse article carries one quadrant value. That value sets the hub card's `data-quadrant` attribute and badge, and it drives the hub's quadrant filter. This policy makes geographic classification consistent across future Letterman integrations, so two people or two Claude sessions classifying the same article reach the same answer.

The policy covers the editorial rules, how they relate to the City of Arlington's published planning descriptions, how to resolve overlaps, gaps, and boundary-road cases, the ALL fallback and manual review, the evidence to record, test cases, and the revision process.

It does not reclassify existing live cards. Applying it to existing cards is a separate change requiring its own approval.

---

## 2. Sources and how they are used

This policy uses two kinds of rules. Keep them separate.

**A. City of Arlington published planning descriptions (reference only).**
- Source: City of Arlington, *Comprehensive Plan: 99 Square Miles* (adopted 2015), planning-area descriptions at printed pages approximately 147–156.
  - Document: https://www.arlingtontx.gov/files/assets/city/v/3/planning-and-development-services/documents/long-range-planning/comprehensive-plan-99-square-miles.pdf
  - City Comprehensive Plan page: https://arlingtontx.gov/CompPlan
- The City's descriptions are:
  - **North Arlington (north of I-30)**
  - **East Arlington (east of Collins Street between I-30 and I-20)**
  - **Central Arlington (between Fielder Road, Collins Street, I-30 and I-20)**
  - **West Arlington (west of Fielder Road between I-30 and I-20)**
  - **South Arlington (south of I-20)**
- **Currency caveat.** The 2015 plan is the version reviewed for this draft. The City's FY26 budget lists an update, "Innovate Arlington," with adoption expected in October 2026. Re-check the current plan and its maps before approval.

**B. Arlington Pulse editorial classification rules (proposed, not City-published).** These are the site owner's rules, defined in §3. They use the City's wording for the Central and East areas as a working reference.

**C. Verification tools (approximate, not authoritative).** OpenStreetMap road geometry and geocoding were used to check test cases. They are not a source for boundaries. Any location result must be confirmed at building level before it is relied on (see §7).

---

## 3. Definitions (proposed editorial rules)

| Value (`data-quadrant`) | Badge | Proposed rule | Relation to City description |
|---|---|---|---|
| `north` | NORTH | Location is north of Interstate 30 (I-30). | Matches City "North Arlington (north of I-30)". |
| `south` | SOUTH | Location is south of Interstate 20 (I-20). | Matches City "South Arlington (south of I-20)". |
| `central` | CENTRAL | Location is between I-30 and I-20, west of Collins Street and east of Fielder Road. | Working definition based on City "Central Arlington (between Fielder Road, Collins Street, I-30 and I-20)". Not expanded to the whole I-30 to I-20 band. |
| `east` | EAST | Location is between I-30 and I-20, east of Collins Street. | Based on City "East Arlington (east of Collins Street between I-30 and I-20)". Treated as its own classification within the band. |
| `all` | ALL | Citywide, multi-location, general Arlington, unresolved, or unverifiable. | Editorial fallback. See §5. |

**Not a quadrant: West.** The City's "West Arlington" (west of Fielder Road between I-30 and I-20) has no Arlington Pulse value. Under this policy, locations there are classified `all` and flagged for review. They are not assigned to CENTRAL. Adding a `west` value requires owner approval and a separate change to the hub filter and badge CSS.

Values are lowercase in `data-quadrant`. Badge text is the uppercase form of the same value.

---

## 4. Boundary and overlap rules

### 4.1 Precedence between EAST and CENTRAL

Inside the I-30 to I-20 band, EAST is defined as east of Collins Street and CENTRAL as west of Collins Street and east of Fielder Road. These areas do not overlap, so EAST takes precedence in the sense that a location east of Collins is EAST and never CENTRAL. The band must not be treated as CENTRAL by default.

### 4.2 NORTH and SOUTH

NORTH and SOUTH are defined by I-30 and I-20 alone, across all longitudes. A location north of I-30 is NORTH whether it is east or west of Collins or Fielder. A location south of I-20 is SOUTH likewise. These rules are proposed as written by the owner. The City's descriptions cover these areas the same way.

### 4.3 Boundary roads and interstates

A location directly on a boundary road or interstate is **REVIEW**, not automatically assigned, unless the owner has approved a convention for it. Boundary roads are:
- I-30
- I-20
- Collins Street
- Fielder Road

"Directly on" means the address fronts the road, or its coordinate falls within the road right-of-way. The owner must approve a tie-break convention before any such location is auto-classified. Until then, classify it `all` and flag it for editorial review.

**Placeholder:** [PLACEHOLDER: owner-approved distance margin from any boundary line, below which a location is treated as boundary-road]

### 4.4 Gaps and uncovered areas

Under the rules in §3, the following are not covered by a quadrant and must not be silently assigned to CENTRAL, EAST, NORTH, or SOUTH:

1. **West Arlington** (west of Fielder Road between I-30 and I-20). No value exists. Classify `all`, flag for review.
2. **Locations outside City limits** or outside Arlington. Classify `all`, flag for review.
3. **Locations near the ends of I-30 or I-20**, where the interstate leaves the city and "north of" or "south of" cannot be determined from the highway alone. Classify `all`, flag for review.
4. **Locations whose coordinate cannot be confirmed** to be on one side of the reference line. Classify `all`, flag for review.

Locations east of Collins Street but north of I-30 or south of I-20 are not gaps. They fall under NORTH or SOUTH by §4.2. They are noted here so the owner can confirm that is intended.

### 4.5 Reference-line convention

"North of I-30" and "south of I-20" must be measured from a defined line. The interstate curves across the city, so the owner must approve one convention, for example the highway centerline or the nearest frontage-road edge. Until approved, classify only when the location is clearly away from the interstate, and otherwise treat it as boundary-road (§4.3).

---

## 5. ALL fallback and manual review

Use `all` when classification is uncertain. Never invent a location, and never force a quadrant to make a card look complete.

| Situation | Classification |
|---|---|
| Citywide, general Arlington, or city-level coverage | `all` |
| Several locations in different quadrants with no single primary location | `all` |
| One headline subject, with only incidental mentions of other locations | Quadrant of the headline subject |
| No address, or the address cannot be verified | `all` |
| Address outside Arlington | `all`, flag for review |
| Location in a gap (§4.4) | `all`, flag for review |
| Boundary-road or reference-line case (§4.3, §4.5) without an approved convention | `all`, flag for review |
| Confidence is medium or low for any reason | `all` |

**Manual review process.** A flagged item is recorded with its evidence (§6) and marked for owner review. The owner decides whether a quadrant applies. The decision is recorded in the evidence record before the hub card is changed. A reviewer may not assign a quadrant to a gap or boundary-road case without this decision.

---

## 6. Evidence Claude must record when proposing a quadrant

Each proposal must include a record with these fields. The record lives in the change description or PR, not in public HTML.

- Article identifier (Letterman article ID and proposed slug)
- Address or addresses used, and where each appears in the source (for example, "content block 1, paragraph 2")
- Location method (street address, venue name, or other) and the tool used to locate it
- Coordinate used, if any, with its precision (building, street, or area), and the method
- Relation to the reference lines: side of I-30 or I-20, and side of Collins Street or Fielder Road
- Distance from the nearest boundary line, in metres, where computed
- Boundary-road flag (yes or no)
- City of Arlington reference used (§2A) and page
- Proposed value and confidence (`high`, `medium`, or `low`)
- Reason, in one or two sentences
- Ambiguities and open questions
- Owner decision and date, once given

A `medium` or `low` result is classified `all` unless the owner overrides it in writing.

---

## 7. Test cases

Outcomes marked **hypothesis** must be confirmed against the approved map and convention before use. Coordinates below are approximate and come from the verification tools in §2C.

| # | Case | Evidence | Proposed outcome | Status |
|---|---|---|---|---|
| T1 | **NORTH.** River Legacy Park (park as a whole) | Park centroid approx. 32.8057 N, −97.0629 W (Nominatim). I-30 in the sampled corridor (approx. −97.26 to −97.05 W, from OpenStreetMap) lies between 32.7585 and 32.7608 N, so the centroid is roughly 5 km north of it. | `north` | Supported for the park as a whole. Verify the venue address, not the park name (see T2). |
| T2 | **NORTH, boundary-proximate.** River Legacy festival venue, 701 NW Green Oaks Blvd | Street-level geocode for NW Green Oaks Blvd, approx. 32.7626 N, −97.1487 W. That is about 200 m north of the nearest sampled I-30 point (32.7608 N) and about 290 m north of the I-30 centerline at that longitude (approx. 32.7600 N). | **REVIEW** until building-level coordinates are confirmed and the margin in §4.3 is set. Then `north` if confirmed. | **Hypothesis.** Not verified at building level. |
| T3 | **SOUTH.** A business south of I-20 | Business address south of I-20 | `south` | Expected. Confirm with the approved reference line. |
| T4 | **CENTRAL.** Business between I-30 and I-20, west of Collins and east of Fielder | Business address in that area | `central` | Expected. Confirm with the approved map. |
| T5 | **EAST.** Business between I-30 and I-20, east of Collins | Business address in that area | `east` | Expected. Confirm with the approved map. |
| T6 | **ALL.** Multi-venue roundup across several quadrants | Article names venues in more than one quadrant, with no single subject | `all` | Per §5 |
| T7 | **ALL.** Citywide news or general Arlington event | No single address | `all` | Per §5 |
| T8 | **Boundary road.** Address fronting Collins Street or Fielder Road, or within I-30 or I-20 right-of-way | Address on or beside a boundary road | `all`, **REVIEW** | Per §4.3 until the owner approves a tie-break convention |
| T9 | **Uncovered area.** Business on West Arlington (west of Fielder, between I-30 and I-20) | Business address in that area | `all`, **REVIEW** | Per §4.4. Do not assign CENTRAL. |
| T10 | **Uncovered area.** Venue near the end of I-30 or I-20 where the highway leaves the city | Location where the reference line is unclear | `all`, **REVIEW** | Per §4.4 |
| T11 | **Entertainment District (existing hub labels).** AT&T Stadium approx. 32.7479 N, −97.0928 W; Globe Life Field approx. 32.7476 N, −97.0841 W | Both sit at about 32.748 N, roughly 1.2 to 1.3 km south of the sampled I-30 corridor (32.7585 to 32.7608 N). The City's East description places the Entertainment District in the northern part of East Arlington. | **Not NORTH** under §3. Probably `east`, but Collins Street's position at that longitude is unverified. Owner decision needed. | **Conflict.** Existing hub NORTH cards on these topics do not match the rule. No card changed in this policy. |

---

## 8. Keeping the hub-card badge and `data-quadrant` consistent

- The `data-quadrant` value and the badge class must match exactly. Example: `data-quadrant="north"` pairs with `<span class="quadrant-badge north">NORTH</span>`.
- Allowed values are only `north`, `south`, `central`, `east`, and `all`. No other value may be used.
- The badge text must equal the uppercase form of the `data-quadrant` value.
- The hub's badge CSS already defines all five values. A new value requires a separate approved change to this policy, the badge CSS, and the filter buttons.
- Changing a card's quadrant changes both attributes in the same edit.
- The article page does not carry a quadrant value. The hub card is the only place it is written, so the evidence record in §6 is the source of truth for that card.
- Before a hub card is merged, confirm its value matches the evidence record.

---

## 9. Revising this policy

1. Any change to a definition, boundary, convention, or rule requires written approval from the site owner.
2. Each revision increments the version number, records the date, and adds a changelog entry.
3. A boundary change applies to future classifications only. Existing cards are not reclassified automatically. Reclassifying existing cards is a separate change with its own evidence records and approval.
4. When the City adopts a new Comprehensive Plan, re-check §2A and §3 against the adopted descriptions and maps before the next revision is approved.
5. Every revision is made on a feature branch and reviewed under the repository's governance process (`CLAUDE.md`, `TRANSITION_CONTROL_LOG.md`).

### Changelog

- **0.1 (draft):** Initial draft with boundary placeholders.
- **0.2 (proposed):** Adds City of Arlington planning-area sources, the West gap, boundary-road and reference-line rules, the manual review process, and test cases including River Legacy and the Entertainment District conflict. Not approved.

---

## 10. Open decisions for the site owner

1. Approve the City's 2015 *99 Square Miles* plan as the reference, or use the newer Innovate Arlington plan once adopted?
2. Approve the editorial rules in §3 as written (north of I-30, south of I-20, central and east as described)?
3. Adopt a reference-line convention for I-30 and I-20 (centerline or frontage-road edge)?
4. Set the boundary-road margin (§4.3 placeholder), and the tie-break convention for addresses on Collins Street or Fielder Road?
5. Add a WEST value for the City's West Arlington area, or keep it as `all`?
6. Should the Entertainment District, including AT&T Stadium, Globe Life Field, and Texas Live!, be EAST, CENTRAL, or NORTH under the rules? The current hub labels NORTH conflict with the rule.
7. Should River Legacy Park's festival venue be confirmed at building level before it is labeled NORTH?
8. Should the hub filter keep showing `all` cards under every quadrant filter? That is hub code, so it would be a separate approved change.
