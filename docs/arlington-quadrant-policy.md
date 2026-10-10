# Arlington Pulse Quadrant Classification Policy (practical editorial geography)

**Version:** 0.4 (PROPOSED)
**Status:** PROPOSED, NOT APPROVED. This revision is pending the owner's review of the diff. Items marked **PROVISIONAL** are individual venue classifications that remain uncertain.
**Applies to:** Arlington Pulse Letterman article integrations (hub card `data-quadrant` value and badge).
**Does not apply to:** Dallas or Fort Worth hubs; subscriber quadrant selections in `api/subscribe.js`.

---

## 1. Purpose and scope

This policy sets practical editorial geography for Arlington Pulse, comparable to how a general-purpose map app groups locations. It decides which quadrant a story is labeled with on the hub, and therefore which filter shows it.

It is **not** an official City of Arlington planning classification, and it is **not** a survey-grade boundary system. The boundaries are approximate editorial lines drawn from major highways and streets.

The policy does not change existing cards, articles, application code, the six-card display cap, or Vercel configuration. Each of those is a separate change.

---

## 2. Sources and background

### 2A. Background only: City of Arlington Comprehensive Plan (2015)

The City's *Comprehensive Plan: 99 Square Miles* (adopted March 17, 2015) describes planning areas named North, East, Central, West and South Arlington. Source: https://www.arlingtontx.gov/files/assets/city/v/3/planning-and-development-services/documents/long-range-planning/comprehensive-plan-99-square-miles.pdf (also linked from https://arlingtontx.gov/CompPlan).

This document is cited as **background only**. The policy:
- does not depend on City Council adoption of any newer plan, including the Innovate Arlington update;
- does not require matching the City's planning-area definitions exactly.

Innovate Arlington's adoption status is therefore not a blocker for this policy.

### 2B. Editorial classification rules

The rules in §3 and §4 are Arlington Pulse's editorial rules. They use major highways and streets as practical references.

### 2C. Checking tools

Map-app style checks and public geocoding may be used to see which side of a highway or street a venue is on. These checks are approximate. They are not survey measurements.

---

## 3. Values and definitions

| Value (`data-quadrant`) | Badge | Rule |
|---|---|---|
| `north` | NORTH | North of Interstate 30 (I-30). |
| `south` | SOUTH | South of Interstate 20 (I-20). |
| `central` | CENTRAL | Between I-30 and I-20, within the Fielder Road–Collins Street boundaries (west of Collins Street and east of Fielder Road). |
| `east` | EAST | East of Collins Street, between I-30 and I-20. |
| `all` | ALL | Citywide or multi-area stories, and specific locations that cannot confidently be assigned to one of the four quadrants above. |

Values are lowercase in `data-quadrant`. Badge text is the uppercase form of the same value.

**Exactly five values are used:** `north`, `south`, `central`, `east`, and `all`. **No WEST value exists.** Specific locations between I-30 and I-20 that are west of Fielder Road fall outside the four quadrants, so they are `all`. They are **never** classified CENTRAL.

**`all` does not mean citywide.** A specific venue that cannot be assigned keeps its actual location and article details, and is classified `all`.

**Manual-review flag, separate from the value.** The manual-review flag marks a story for an editor to check. It is not a classification value and does not change the quadrant. No quadrant value is created for review.

---

## 4. Boundary rules

### 4.1 EAST takes precedence over CENTRAL

**EAST takes precedence over CENTRAL within the I-30-to-I-20 band.** A location in that band and east of Collins Street is EAST. CENTRAL applies only to locations in the band that are west of Collins Street and east of Fielder Road. A location is never CENTRAL merely because it is in the band.

### 4.2 NORTH and SOUTH

NORTH is north of I-30, across all longitudes. SOUTH is south of I-20, across all longitudes.

### 4.3 Practical references

- Use I-30, I-20, Collins Street and Fielder Road as they appear on a standard map.
- Treat each highway as a line along its alignment.
- These lines are approximate editorial boundaries. They are not official City designations and not precise property lines.

### 4.4 Clear side versus ambiguous

- **A venue clearly on one side of a boundary is classified accordingly.** No building-level coordinate is required.
- **A genuinely ambiguous location is `all`** with a manual-review flag.

### 4.5 The 100-metre review guideline

A venue within about 100 metres of I-30, I-20, Collins Street or Fielder Road is a **practical review guideline**, not an absolute survey requirement. At that distance, check the venue's side on a map. If it is still unclear, classify it `all` with a manual-review flag.

### 4.6 Collins Street and Fielder Road

Inside the I-30-to-I-20 band, Collins Street and Fielder Road separate CENTRAL and EAST. A venue directly on one of these roads is classified only if it is clearly on one side of the line. Otherwise it is `all` with a manual-review flag. Outside the band, the NORTH and SOUTH rules in §4.2 apply.

### 4.7 Uncovered areas

- **Between I-30 and I-20, west of Fielder Road:** specific venues are `all`. They keep their location and details. They are not CENTRAL.
- **Near the ends of I-30 or I-20,** where the highway leaves the city and the side is unclear: `all` with a manual-review flag.
- **Outside Arlington:** `all` with a manual-review flag.

---

## 5. ALL and the manual-review flag

**Substantive coverage.** A location receives substantive coverage in a story when the story describes it at more than passing length, such as a dedicated paragraph or section, or when it is the subject of the headline. A location named only in passing is an **incidental mention**. Incidental mentions do not affect the classification.

| Situation | Classification |
|---|---|
| General or citywide story | `all` |
| Two or more locations in different quadrants each receive substantive coverage | `all` |
| One location receives substantive coverage; the others are incidental mentions | The quadrant of the substantively covered location |
| Specific location clearly on one side of a boundary | That quadrant. No flag needed. |
| Specific location that cannot confidently be assigned | `all` with manual-review flag |
| Within the 100 m review guideline and still unclear (§4.5) | `all` with manual-review flag |
| Confidence is low | `all` with manual-review flag |

**Manual review.** The manual-review flag tells the editor to check the classification before publishing. It does not change the value.

---

## 6. Evidence to record

For each proposal, record:

- Article ID and proposed slug;
- the address or venue used, and where it appears in the source;
- the basis for the location (street address, venue name, or other);
- the approximate side of I-30 or I-20, and of Collins Street or Fielder Road where relevant;
- the proposed value and confidence (`high`, `medium`, or `low`);
- whether a manual-review flag is set, and why;
- limitations, in one or two sentences.

A building-level coordinate is **not** required for a venue that is clearly on one side of a boundary. It is needed only when a location is genuinely ambiguous and the editor wants to resolve it.

---

## 7. Test cases

| # | Case | Outcome | Status |
|---|---|---|---|
| T1 | **NORTH.** River Legacy Park as a park, north of I-30 | `north` | Clear. The park is not a single venue. |
| T2 | **NORTH.** River Legacy festival venue, 701 NW Green Oaks Blvd. Street-level points put the address about 200 m to about 1 km north of I-30. | `north` | **PROVISIONAL.** The address is clearly north of I-30 on a standard map, but the road runs close to the highway. The editor should confirm the venue's position on a map before publishing. If that is unclear, use `all` with a manual-review flag. The park's centroid is not used as evidence of the venue's location. |
| T3 | **SOUTH.** Business south of I-20 | `south` | Clear. |
| T4 | **CENTRAL.** Business between I-30 and I-20, west of Collins and east of Fielder | `central` | Clear. |
| T5 | **EAST.** Business between I-30 and I-20, east of Collins | `east` | Clear. EAST takes precedence (§4.1). |
| T6 | **ALL.** Story with substantive coverage of venues in several quadrants | `all` | Per §5. |
| T7 | **ALL.** Citywide or general Arlington story | `all` | Per §5. |
| T8 | **Collins or Fielder, inside the band.** Venue directly on one of these roads | The quadrant of the side it is clearly on; otherwise `all` with manual-review flag | Per §4.6 |
| T9 | **Uncovered area.** Specific venue west of Fielder, between I-30 and I-20 | `all`, keeps its location and details. Not CENTRAL. | Per §4.7 |
| T10 | **Near the end of a highway.** Venue where I-30 or I-20 leaves the city and the side is unclear | `all` with manual-review flag | Per §4.7 |
| T11 | **Entertainment District, venue by venue.** AT&T Stadium and Globe Life Field are about 1.2–1.3 km south of I-30 on the approximate coordinates used in the earlier audit. | Not NORTH. Each venue's EAST or CENTRAL status is **PROVISIONAL**: confirm the venue's position relative to Collins Street on a standard map. Texas Live!, Six Flags Over Texas and Hurricane Harbor are provisional until checked the same way. | **PROVISIONAL** |
| T12 | **Incidental mention.** Story substantively about one venue, with a second venue named in one sentence | The quadrant of the substantively covered venue | Per §5 |

---

## 8. Keeping the badge and `data-quadrant` consistent

- The `data-quadrant` value and the badge class must match exactly. Example: `data-quadrant="north"` pairs with `<span class="quadrant-badge north">NORTH</span>`.
- Allowed values are only `north`, `south`, `central`, `east` and `all`.
- The badge text must equal the uppercase form of the `data-quadrant` value.
- The hub's badge CSS already defines all five values. Adding a value would need a separate approved change to this policy, the badge CSS, and the filter buttons.
- Changing a card's quadrant changes both attributes in the same edit.
- The article page does not carry a quadrant. The hub card is the only place it is written.

---

## 9. Hub behavior for ALL cards (separate proposed change, NOT implemented)

**Intended behavior:** general and multi-area stories labeled `all` should appear under every quadrant filter.

**Current state on `main`:**
- The filter script shows a card when its value equals the active filter, or when the card's value is `all`. So `all` cards are already eligible under every filter.
- The CSS rule `.archive-grid .issue-card:nth-child(n+7) { display: none; }` hides every card after the sixth, regardless of filter. As a result, `all` cards beyond the first six cannot appear under any filter.

**Conclusion:** the filter logic already matches the intended behavior. The gap is the six-card display cap. Changing it is a **separate implementation change** requiring owner approval. It is not part of this policy and is not approved.

---

## 10. Revising this policy

1. Changes to a definition, boundary reference or rule require the owner's written approval.
2. Each revision increments the version and adds a changelog entry.
3. A boundary change applies to future classifications only. Existing cards are not reclassified automatically. Reclassifying existing cards is a separate change with its own approval.
4. The policy does not depend on City adoption of a newer plan. If the owner later chooses to adopt official City boundaries, that is a separate revision.
5. Every revision is made on a feature branch and reviewed under the repository's governance (`CLAUDE.md`, `TRANSITION_CONTROL_LOG.md`).

### Changelog

- **0.1 (draft):** Initial draft.
- **0.2 (proposed):** Added City background, the West gap, boundary rules, manual review, and test cases.
- **0.3 (proposed):** Owner's rules, reference-line convention, River Legacy provisional, Entertainment District venue handling, hub analysis.
- **0.3.1 (proposed):** Removed the future WEST value suggestion. Five values only.
- **0.3.2 (proposed):** Separated City descriptions from editorial rules, added precision and substantive-coverage definitions, stated EAST precedence.
- **0.4 (proposed):** Practical editorial geography. Uses major highways and streets as approximate references. Removes the City-adoption, centerline and building-level blockers. The 100 m buffer becomes a review guideline. Clear-side venues need no building-level coordinate. Entertainment District and River Legacy venues are provisional where uncertain.

---

## 11. Open items for the owner

These are decisions and provisional items, not blockers on the policy's use.

1. **Approve** the five values and the rules in §3 and §4.
2. **Approve** the approach of using major highways and streets as approximate references (§4.3).
3. **Approve** the 100 m review guideline (§4.5) and the manual-review flag (§5).
4. **Confirm** the definition of substantive coverage (§5).
5. **PROVISIONAL:** River Legacy festival venue, NORTH (T2). Confirm on a map before publishing.
6. **PROVISIONAL:** Entertainment District venues, EAST or CENTRAL (T11). Confirm each venue's position relative to Collins Street.
7. **Existing hub card, separate follow-up:** on `main`, the only NORTH-labeled card is "Texas Live! Adds New Rooftop Bar for Rangers Season." Its venue is near AT&T Stadium, which is south of I-30, so the label likely conflicts with §4.2. No card is changed by this policy. Any change needs separate approval.
8. **Hub six-card cap (§9):** a separate implementation change requiring approval.
