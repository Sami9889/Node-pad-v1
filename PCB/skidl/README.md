# NodePad — SKiDL Schematic Source

The schematic is authored as Python using [SKiDL](https://github.com/devbisme/skidl).
Running the scripts produces a KiCad netlist that can be imported directly
into `NodePad.kicad_pcb` to place footprints and pre-wire ratsnest.

## Why SKiDL, not click-in-KiCad?

- Every connection is version-controlled text — meaningful `git diff`.
- Sub-blocks are reusable Python functions (`rtc.build()`, `user_io.build()`).
- Rules like *"every USB power line needs a ferrite bead"* can be enforced in code.
- Bulk changes (e.g. rename a net) are 1-line refactors, not a hunt-through in KiCad.
- Trade-off: no pretty visual schematic PDF from these files alone. The Python
  IS the source of truth. If a visual is needed later, KiCad's schematic editor
  can be used to lay out sheet symbols manually, or SKiDL's beta ERC/HTML report.

## What's here today (rev 0.1)

| File | Contents | Components | Status |
|------|----------|-----------:|--------|
| `power_tree.py` | USB-C → CH224K PD → MP2315 buck → AP2112 LDO, all decoupling, ESD, test points | 30 | ✅ Netlist clean |
| `rtc.py`        | DS3231MZ+ RTC + CR2032 backup + I²C pull-ups | 9 | ✅ Netlist clean |
| `user_io.py`    | SW1/SW2 buttons, D1–D5 LEDs, J13 GPIO 40-pin header, J15 fan header | 14 | ✅ Netlist clean |
| `main.py`       | Composes the above into a single design and emits `nodepad.net` | — | ✅ Runs, 0 errors |

Deliberately **not yet** written (real engineering work, need datasheet + eyes):

- `cm5.py`      — Radxa CM5 SoM 2×100-pin DF40 connectors, breakouts
- `ethernet.py` — RJ45 #1 (native GbE) + RJ45 #2 (RTL8125 over PCIe) + magnetics
- `usb_hub.py`  — GL3523 hub + 4× USB-A + TPS2553 per-port switches
- `m2.py`       — M-key NVMe (2280) + E-key WiFi (2230) with PCIe lane wiring
- `hdmi.py`     — HDMI Type-A + ESD array + level shifting
- `poe.py`      — Optional PoE PD circuit (DNP by default)

Each is roughly a 1–2-day authoring + review job.

## Prerequisites

```bash
pip install skidl==2.2.3
# KiCad symbol library (one-time)
git clone --depth 1 --branch 9.0.0 \
    https://gitlab.com/kicad/libraries/kicad-symbols.git \
    ~/kicad-symbols
export KICAD_SYMBOL_DIR=~/kicad-symbols
export KICAD9_SYMBOL_DIR=~/kicad-symbols
```

## Generate the netlist

```bash
cd PCB/skidl
python3 main.py
# → netlists/nodepad.net   (KiCad-compatible netlist)
```

## Import into KiCad PCB

1. Open `PCB/NodePad.kicad_pcb` in KiCad 10.
2. **File → Import → KiCad Netlist**
3. Point it at `PCB/skidl/netlists/nodepad.net`
4. Set *"Match footprints by:"* to **Reference**.
5. Set *"Update options:"* to **Delete extra footprints** = ON,
   **Update fields** = ON, **Delete extra tracks** = OFF.
6. Click **Update PCB**. All 53 footprints drop onto the board with
   ratsnest lines showing every net that needs to be routed.
7. Save.

At this point you can start placement (drag components into the zones
labelled on the Fab layer of the PCB) and routing per the plan in
`../DESIGN.md`.

## Roundtrip warning ⚠️

If you edit the schematic in **KiCad** after importing the netlist, those
edits will **not** flow back into the SKiDL Python source. Pick one direction
of truth per stage:

- **Design phase**: SKiDL is the source, regenerate netlist, re-import to PCB.
- **Layout phase**: PCB is the source; add small tweaks (a stray via, a
  silkscreen edit) in KiCad; don't touch nets there.
- **After rev-1 fab**: freeze the SKiDL scripts, use KiCad-native for rev-2
  polish, and treat the Python as historical documentation.

## Sanity check on latest netlist

Latest generation:
- **53 components** placed
- **41 nets** wired (some auto-numbered `N$*` for internal power-tree loops)
- **17 unique footprints** — all from stock KiCad library, all JLCPCB-friendly
- **0 ERC errors** (51 warnings, all "unconnected pin" on the GPIO header —
  these get resolved once the CM5 SoM connectors are added and their GPIOs
  route into `J13`)

Regenerate any time:

```bash
python3 main.py
```
