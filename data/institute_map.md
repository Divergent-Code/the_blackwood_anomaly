# The Blackwood Institute — Spatial Map

Use this document to maintain consistent spatial geography. When the player moves,
call `move_to_location(location_name)` using the exact zone names below.
Do NOT invent new rooms outside this structure without anchoring them to a zone.

---

## Zone Layout (Top to Bottom)

```
[SURFACE — RESTRICTED ACCESS]
        |
  Surface Elevator Shaft  ← Escape Route Stage 2
        |
  Administration Level
        |
  Research Archive         ← Lore Hub
        |
  Sub-Level 1 — General Wards
        |
  Sub-Level 2 — Surgery Wing    ← Player Start Adjacent
        |
  Sub-Level 3 — Containment Sector
        |
  The Breach Point         ← Anomaly Epicentre
```

---

## Zone Descriptions

### Intake Bay 4 *(Starting Location)*
A recovery room. Eight gurneys bolted to the floor, four overturned. Clinical
white tile, now grey with grime and something darker. Fluorescent tubes flicker
at irregular intervals. The smell is isopropyl alcohol and something organic
underneath it. One door leads to the Surgery Wing. A sealed emergency hatch
leads to the Service Tunnels.

**Connections:** Surgery Wing (north), Service Tunnels (floor hatch)
**Threats present:** None initially. Converted may arrive after Turn 3.
**Notable:** The player's gurney. Surgical staples on their neck. No personal
effects.

---

### Surgery Wing
A long corridor of operating theatres. Heavy steel doors, most sealed. Through
small reinforced windows, the theatres are dark. Equipment has been rearranged —
tables pushed against walls, instruments scattered. The Surgical Automatons
originated here. At least two remain active.

**Connections:** Intake Bay 4 (south), Research Archive (elevator, requires
keycard), Morgue Corridor (east stairs)
**Threats present:** 1–2 Surgical Automatons (active), Warden surveillance (medium)
**Notable:** Operative theatre 7 contains a first aid kit (locked cabinet, DC 12).
The Warden control panel for this wing is in the scrub room.

---

### Morgue Corridor
A long, low-ceilinged passage. Body storage drawers line both walls — most closed,
several open and empty. The floor is slightly sloped toward a central drain.
The drain is blocked. The Crawl was first observed here.

**Connections:** Surgery Wing (west), Containment Sector (north, blast door)
**Threats present:** The Crawl (advancing slowly from the north end)
**Notable:** Dr. Voss's emergency badge is on a body in drawer 14 (drawer is jammed,
DC 12 to open). The badge is required to access the Research Archive elevator.

---

### Research Archive
A climate-controlled library of servers, filing cabinets, and terminal stations.
Dim emergency lighting only. This is where the Institute stored its research
data — and where it hid what it could not publish. Most terminals are locked.
One terminal (Station 7) accepts Dr. Voss's badge.

**Connections:** Surgery Wing (elevator, requires Voss badge), Administration Level
(stairwell, requires Director access code)
**Threats present:** The Warden (high surveillance — every terminal access is logged)
**Notable:** Contains the highest density of lore fragments. The Warden will respond
to activity here. Station 7 contains Subject 814's full intake file.

---

### Containment Sector
The lowest accessible area of the Institute before The Breach. Reinforced concrete
everywhere. The architecture becomes irregular here — angles that don't add up,
rooms that are larger inside than their external dimensions suggest. The Anomaly's
spatial distortion is strongest here. The Suture was first sighted in this sector.

**Connections:** Morgue Corridor (south blast door), The Breach Point (sealed
containment door — requires Director access code)
**Threats present:** The Suture, residual Converted, spatial disorientation
**Notable:** The Suture's anchor point is in Containment Room 3. The Director's
access code is etched into the underside of a workstation desk.

---

### The Breach Point
The origin of The Anomaly. A research laboratory whose walls, floor, and ceiling
have been partially replaced by something that is not concrete and not air. The
dimensional breach is visible — a 3-metre irregular aperture that emits no light
but absorbs it. This is the final obstacle before the surface elevator.

**Connections:** Containment Sector (south), Surface Elevator Shaft (north —
accessible only if escape stage ≥ 3)
**Threats present:** Final encounter — all active threats may converge here
**Notable:** This is where the Anomaly event occurred. Lore fragments here reveal
what the Institute was actually researching and what Subject 814 was.

---

### Surface Elevator Shaft
An industrial elevator, surprisingly intact. The mechanism requires power, which
must be rerouted from a junction box (DC 14). Once powered, the elevator ascends
to a locked surface hatch (DC 16 to force, or use Director code).

**Connections:** The Breach Point (below), Surface (above — game won)
**Threats present:** None initially. The Warden makes a final PA broadcast here.

---

### Service Tunnels
A network of maintenance crawlways connecting all zones. Low, dark, and narrow.
Used by utility drones pre-Anomaly. Now used by The Crawl as a transit network.
Moving through tunnels is faster but riskier.

**Connections:** All zones (via access hatches)
**Threats present:** The Crawl segments, Converted (occasional)
**Notable:** Several supply caches left by panicking staff (random items, DC 11 to
locate in a given tunnel section).
