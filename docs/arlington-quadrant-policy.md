# Arlington Pulse Quadrant Classification Policy

**Version:** 0.1 (DRAFT)
**Status:** NOT APPROVED. Geographic boundaries in this document are placeholders. Nothing here is an official boundary until the site owner approves it in writing.
**Applies to:** Arlington Pulse article integrations (Letterman → website hub card and article page).
**Does not apply to:** Dallas or Fort Worth hubs; subscriber quadrant selections in `api/subscribe.js` (those are subscriber choices, not article classifications, and are not changed by this policy).

---

## 1. Purpose and scope

Every Arlington Pulse article carries one quadrant value. That value sets the hub card's `data-quadrant` attribute and its badge, and it drives the hub's quadrant filter. This policy makes classification consistent across all future Letterman integrations, so that two people (or two Claude sessions) classifying the same article reach the same answer.

The policy covers:
- how each quadrant is defined;
- how to classify an article from its actual venue or business address;
- what to do when classification is uncertain;
- what evidence must be recorded;
- how the badge and `data-quadrant` stay consistent;
- how the policy is revised.

It does not reclassify existing live cards. Applying it to existing cards is a separate change requiring its own approval.

---

## 2. Quadrant values and definitions

| Value (`data-quadrant`) | Badge text | Meaning | Status |
|---|---|---|---|
| `north` | NORTH | Primary venue or subject lies inside the NORTH region. | Region boundary PENDING APPROVAL |
| `south` | SOUTH | Primary venue or subject lies inside the SOUTH region. | Region boundary PENDING APPROVAL |
| `central` | CENTRAL | Primary venue or subject lies inside the CENTRAL region. | Region boundary PENDING APPROVAL |
| `east` | EAST | Primary venue or subject lies inside the EAST region. | Region boundary PENDING APPROVAL |
| `all` | ALL | Citywide, multi-location, general Arlington, or location cannot be verified. | Definition proposed; see §5 |

Values are lowercase in the `data-quadrant` attribute. Badge text is the uppercase form of the same value.

---

## 3. Geographic boundaries

**No boundaries are approved.** The rows below are placeholders. Each must be replaced with an owner-approved description before this policy is used for classification.

| Region | Boundary description | Reference map | Status |
|---|---|---|---|
| NORTH | [PLACEHOLDER: to be defined from the approved map] | [PLACEHOLDER] | PENDING OWNER APPROVAL |
| SOUTH | [PLACEHOLDER: to be defined from the approved map] | [PLACEHOLDER] | PENDING OWNER APPROVAL |
| CENTRAL | [PLACEHOLDER: to be defined from the approved map] | [PLACEHOLDER] | PENDING OWNER APPROVAL |
| EAST | [PLACEHOLDER: to be defined from the approved map] | [PLACEHOLDER] | PENDING OWNER APPROVAL |

### 3.1 Reference points observed in existing site content (not boundaries)

These are places the existing site already mentions. They are recorded here only as examples of how the site has used the labels. They do not define any region.

- Entertainment District, Globe Life Field, AT&T Stadium, Texas Live! (currently appear on NORTH cards). **Open question:** see §10.
- UTA campus and Downtown Arlington (appear in CARD_DATA_STRUCTURE.md as CENTRAL examples).
- Division Street corridor (CARD_DATA_STRUCTURE.md lists it as an EAST example).
- Sublett Road (an existing SOUTH card).

### 3.2 Boundary method (proposed)

1. The owner selects one authoritative map or boundary source and records its name, version, and date in §3.
2. Each region is described using named, publicly recognizable reference features (for example, major roads, rail lines, or city limits). Coordinates are not used in the policy text; they may be used as evidence only.
3. Regions must cover all of Arlington with no gaps or overlaps. Any location that falls on a line or outside the city is classified `all`.
4. Boundary changes follow §9.

---

## 4. How to classify an article

Classification is based on the actual venue or business address, not on a neighborhood name used in marketing copy.

1. **Find the address.** Take the street address of the primary venue or business from the article body. Record where it appears (for example, "content block 1, paragraph 2").
2. **Check it is in Arlington.** If the address is outside Arlington or missing, go to §5.
3. **Locate it on the approved map.** Confirm which region contains the address.
4. **Check for a single primary location.** If the article's headline subject is one venue or one address, that venue determines the quadrant (see §5 for multi-location rules).
5. **Assign the value** (`north`, `south`, `central`, or `east`) only when steps 1–4 succeed with high confidence. Otherwise assign `all`.
6. **Record the evidence** (§7) before the value is written to the hub card.

Neighborhood or district names alone (for example, "Downtown" or "the Entertainment District") are not enough to assign a region unless the owner-approved map maps that name to a region.

---

## 5. Multiple locations, general Arlington coverage, and uncertainty

**Use `all` when classification is uncertain.** Do not invent a location and do not force a quadrant to make a card look complete.

| Situation | Classification (proposed) |
|---|---|
| Article covers several locations in different regions, with no single subject | `all` |
| Article has one headline subject and only incidental mentions of other locations | Quadrant of the headline subject |
| Article is about Arlington in general, citywide news, or a city-level event | `all` |
| No address is given, or the address cannot be verified | `all` |
| Address is outside Arlington | `all` (and flag for review) |
| Location sits exactly on a region boundary, or the map is unclear | `all` |
| Confidence is low for any reason | `all` |

---

## 6. Evidence required when proposing a classification

Every proposed classification must include a record with these fields. The record is kept in the change description or PR, not in the public HTML.

- Article identifier (Letterman article ID and proposed slug)
- Address or addresses used, and where each appears in the source
- Map or boundary source used (name and version from §3)
- Proposed value and confidence (`high`, `medium`, or `low`)
- Reason, in one or two sentences
- Ambiguities or open questions
- Approver (the owner) and approval date, once given

A medium or low confidence result is classified as `all` unless the owner overrides it in writing.

---

## 7. Examples and test cases

These examples test the rules. Outcomes marked **hypothesis** must be checked against the approved map before they are used.

| Case | Source evidence | Proposed outcome | Status |
|---|---|---|---|
| River Legacy Fall Festival at River Legacy Park, 701 NW Green Oaks Blvd | Letterman article body, content block 1 | `north` (hypothesis) | **Hypothesis.** Validate against the approved NORTH boundary. Not proof that any boundary policy exists. |
| Multi-venue coffee roundup across Downtown and other areas | Article body names five venues | `all` (multi-location rule) | Proposed |
| "Arlington summer events" citywide roundup | No single address | `all` | Proposed |
| Single business on Sublett Road | Business street address | `south` (hypothesis) | **Hypothesis.** Validate against the approved SOUTH boundary. |
| Venue with address outside Arlington | Address in another city | `all`, flagged for review | Proposed |
| Article with no address at all | None | `all` | Proposed |

---

## 8. Keeping the badge and `data-quadrant` consistent

- The `data-quadrant` value and the badge class must match exactly. Example: `data-quadrant="north"` pairs with `<span class="quadrant-badge north">NORTH</span>`.
- Allowed values are only `north`, `south`, `central`, `east`, and `all`. No other value may be used.
- The badge text must equal the uppercase form of the `data-quadrant` value.
- The badge CSS classes already exist in the hub for all five values. Any new value requires a separate approved change to both the policy and the hub CSS.
- Changing a card's quadrant changes both attributes in the same edit.
- The article page itself does not carry a quadrant value. The hub card is the only place the value is written, so the evidence record in §6 is the source of truth for that card.
- Before a hub card is merged, confirm the card's value matches the evidence record.

---

## 9. Revising this policy

1. Any change to a boundary, a definition, or a rule requires written approval from the site owner.
2. Each revision increments the version number, records the date, and adds a changelog entry below.
3. A boundary change applies to future classifications only. Existing cards are not reclassified automatically. Reclassifying existing cards is a separate change with its own evidence records and approval.
4. Every revision is made on a feature branch and reviewed under the repository's governance process (`CLAUDE.md`, `TRANSITION_CONTROL_LOG.md`).

### Changelog

- **0.1 (draft):** Initial draft. Boundaries are placeholders. Not approved.

---

## 10. Open decisions for the site owner

1. Which authoritative map or boundary source defines the regions?
2. Where does the Entertainment District (Globe Life Field, AT&T Stadium, Texas Live!) fall? It is currently labeled NORTH.
3. Is Downtown Arlington CENTRAL?
4. Should an article with one headline subject and incidental mentions take that subject's quadrant, or `all`? This draft proposes the subject's quadrant.
5. Should River Legacy Park remain NORTH once the boundary is approved?
6. Should the hub filter continue to show `all` cards under every quadrant filter? That behavior is in hub code, so any change requires its own approved change, and this policy does not change it.
