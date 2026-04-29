# Escape Route — The Blackwood Institute

Subject 814's escape is structured in four stages. Track progress with
`escape_stage` (0–4). Call `advance_escape_stage()` only when the player
has genuinely completed the requirements for that stage.

---

## Stage 0: Orientation (Starting State)

**Status:** Player has just woken up. No escape route known.
**The player knows:** Nothing. They are in Intake Bay 4.
**What must happen:** The player must leave Intake Bay 4 and begin actively
exploring. No tool call required — stage advances automatically when the
player first reaches the Surgery Wing or Service Tunnels.

---

## Stage 1: Obtain Access — The Voss Badge

**Requirement:** Retrieve Dr. Voss's badge from Morgue Corridor, Drawer 14.
**Triggers:** Call `advance_escape_stage()` when the player successfully opens
Drawer 14 and takes the badge. Add `"Dr. Voss's Badge"` to inventory via
`add_item("Dr. Voss's Badge")`.
**Narrative beat:** The badge is cold. The photo on it shows a woman in her
forties, eyes bright, smiling. One corner of the badge is stained dark.
**Unlocks:** Research Archive elevator access, Station 7 terminal.
**Why it matters:** The Archive contains the Director's access code, which
is needed for Stage 3.

---

## Stage 2: Find the Director's Code

**Requirement:** Locate the Director's access code in the Containment Sector
(etched under a workstation desk in the main corridor).
**Triggers:** Call `advance_escape_stage()` when the player examines the underside
of the desk and succeeds on a DC 12 Perception check (or reaches the Containment
Sector and specifically looks under furniture).
Add `"Director's Access Code"` to inventory via `add_item("Director's Access Code")`.
**Narrative beat:** The code is etched with a scalpel into the metal — someone's
insurance policy. Seven digits. The handwriting is careful, deliberate.
**Unlocks:** The sealed containment door to The Breach Point, the surface
elevator hatch.
**Why it matters:** Without the code, the player cannot enter The Breach Point
or exit through the surface hatch.

---

## Stage 3: Cross The Breach Point

**Requirement:** The player must traverse The Breach Point — the Anomaly's
epicentre. This is the most dangerous location in the facility. There is no
stealth option here. The player must move through it.
**Triggers:** Call `advance_escape_stage()` when the player successfully navigates
through The Breach Point and reaches the far side (Surface Elevator Shaft).
**Narrative beat:** The Breach Point requires a final confrontation or escape.
All active threats in the facility may manifest here. The Anomaly aperture
is visible and wrong — the AI should describe spatial impossibilities at their
most intense. The player's implant (from the surgical log) resonates painfully
as they pass through.
**Mechanical notes:**

- Apply +20% stress automatically upon entering The Breach Point
- At least one DC 15+ check is required to cross — the method is the player's choice
- Natural 20 here: the aperture briefly contracts as the player passes — a sign
  that their departure is beginning to close it
- If the player has discovered `voss_log_anomaly`, they know their crossing
  may affect the breach — use this for narrative weight
**Unlocks:** Surface Elevator Shaft becomes accessible.

---

## Stage 4: Escape — The Surface

**Requirement:** The player reaches the Surface Elevator Shaft, restores power
to the elevator (DC 14), and exits through the surface hatch (DC 16 to force,
or automatic with Director's access code).
**Triggers:** Call `advance_escape_stage()` when the player exits through the
surface hatch. This is the win condition — `game_won` flag activates.
**Narrative beat (final):** The hatch opens to outside air — cold, and smelling
of pine and exhaust. No skyline visible. The facility entrance is a concrete
slab in a clearing, surrounded by chain-link fence with no signage. It is
4:00 AM. The player is wearing a hospital gown and has surgical staples in
their neck. They are alive.
The Warden makes one final PA broadcast, audible faintly through the closing
hatch: *"Subject 814 has exited the facility. Shepherd protocol suspended.
Logging anomalous event. This is... not supposed to happen."* Then silence.
**End state:** Game won. Do not continue the narrative. Acknowledge the player's
survival and the open questions that remain unanswered.
