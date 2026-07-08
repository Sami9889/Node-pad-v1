# NodePad

> A tiny, cheap, more-powerful-than-a-Pi homelab node.
> Radxa CM5 (RK3588S2, 8-core, up to 16 GB RAM) on a **100 × 100 mm** carrier board with the kind of I/O a Pi 5 doesn't give you.

**Status:** design phase — schematic & PCB not started yet.
**Author:** Samrath "Sami" Singh
**License:** TBD (MIT or CERN-OHL-P recommended if you plan to sell it)

---

## What is it?

A carrier board for the **Radxa CM5** compute module. You skip designing the CPU/RAM/eMMC section (Radxa already did that) and get a compact server-class SBC with I/O aimed at self-hosting, homelab, mini-Kubernetes, edge servers, network appliances, and NAS-lite.

Think of it as a **"buy 4, stack them, run K3s on PoE"** kind of board.

## Why not just buy a Pi 5?

| Feature | Pi 5 | Radxa CM5 + NodePad |
|---|---|---|
| CPU | 4× Cortex-A76 @ 2.4 GHz | **8×** (4×A76 + 4×A55) @ 2.4 GHz |
| GPU | VideoCore VII | **Mali-G610 MP4** (better) |
| NPU | ❌ | **6 TOPS** |
| Max RAM | 16 GB | 16 GB |
| Ethernet | 1× **1 GbE** | 2× **2.5 GbE** |
| NVMe | via HAT | **native M.2 M-key on board** |
| PoE | HAT (~$20) | **on-board (optional-populate)** |
| Boot | microSD | **eMMC on module** (no SD lottery) |

## Killer features (the pitch)

1. **Dual 2.5 GbE** — one built into the CM5, second added via the M.2 E-key slot with a 2.5GbE controller card *or* a discrete PHY on-board. Enough to run this thing as a router or a K3s node with dedicated cluster interconnect.
2. **M.2 M-key NVMe** slot (2280) — real SSDs, no microSD.
3. **PoE+ optional** — populate the PoE PD circuit and power it with a single Ethernet cable. Leave it unpopulated for cheap builds.
4. **USB-C PD input** — programmable trigger negotiates 12V/15V/20V from any PD charger. No barrel jack, no wall wart headache.
5. **100 × 100 mm square** — cheapest JLCPCB tier, fits in a 3D-printed cube smaller than a Pi 5.

## Cost target

| Version | BOM cost (qty 10) | Sell target |
|---|---|---|
| **Base** (no PoE) | ~$40 empty board | **$99** empty / **$189** with CM5 8GB |
| **Full** (with PoE) | ~$55 empty board | **$129** empty / **$219** with CM5 8GB |

Comparable products: Turing Pi 2 ($260, but 4-node), Radxa Rock 5A ($90 SBC, no PoE/NVMe boot), DeskPi Super6C ($200, Pi CM4-only). NodePad's niche = smallest + PoE + cheap single node.

---

## Bill of Materials (JLCPCB / LCSC part numbers)

All parts picked to be **in JLCPCB's Basic or Extended library** so the whole board can be assembled by JLC PCBA (no hand-soldering headaches). Prices approximate as of 2026-07.

### Compute
| Ref | Part | Function | LCSC | Qty | Price ea. |
|---|---|---|---|---|---|
| U1 | Radxa CM5 (8 GB / 64 GB) | System-on-module | — (Radxa direct) | 1 | **$89** |
| J1, J2 | Hirose DF40C-100DS-0.4V | 2× 100-pin SoM connectors | C43880 | 2 | $2.50 |

### Networking
| Ref | Part | Function | LCSC | Qty | Price ea. |
|---|---|---|---|---|---|
| U2 | RTL8125BG | 2.5GbE MAC+PHY (2nd NIC) | C2861126 | 1 | $3.10 |
| J3, J4 | Bel Fuse 0826-1G1T-04-F | RJ45 with integrated magnetics + LEDs, PoE-capable | C516428 | 2 | $2.80 |
| Y1 | 25 MHz TCXO 3.3V 20ppm | RTL8125 clock reference | C1804 | 1 | $0.30 |

### Storage
| Ref | Part | Function | LCSC | Qty | Price ea. |
|---|---|---|---|---|---|
| J5 | M.2 M-key 2280 socket | NVMe SSD slot | C725119 | 1 | $1.20 |
| J6 | M.2 E-key 2230 socket | WiFi/BT card or 2nd NIC | C725118 | 1 | $0.95 |

### Power
| Ref | Part | Function | LCSC | Qty | Price ea. |
|---|---|---|---|---|---|
| U3 | MP2315 | 5V @ 3A buck (main rail from 12V PD) | C89358 | 1 | $0.42 |
| U4 | AP2112K-3.3 | 3.3V @ 600 mA LDO (rail for RTC, aux) | C51118 | 1 | $0.20 |
| U5 | CH224K | USB-C PD sink, programmable 5/9/12/15/20V | C970725 | 1 | $0.55 |
| U6 *(opt)* | MP8007GV | PoE+ PD converter (802.3at, 25W) | C910435 | 1 | $2.80 |
| T1 *(opt)* | 750317847 or eq. | PoE flyback transformer | C — | 1 | $2.20 |

### I/O
| Ref | Part | Function | LCSC | Qty | Price ea. |
|---|---|---|---|---|---|
| J7 | USB-C 16-pin recept. | Power in + USB 2.0 data | C165948 | 1 | $0.35 |
| J8–J11 | USB-A 3.0 vertical | 4× USB 3.0 host ports | C165999 | 4 | $0.55 |
| J12 | HDMI Type-A | HDMI 2.0 out | C2681 | 1 | $0.60 |
| J13 | 40-pin 2.54 mm header | Pi-compatible GPIO | C124378 | 1 | $0.25 |
| J14 | microSD push-push socket | Boot fallback | C91145 | 1 | $0.45 |
| J15 | 4-pin 2.54 mm header | PWM fan | C124381 | 1 | $0.15 |

### Housekeeping
| Ref | Part | Function | LCSC | Qty | Price ea. |
|---|---|---|---|---|---|
| U7 | DS3231MZ+ | I²C RTC (server needs to know time on cold boot) | C107373 | 1 | $2.10 |
| BT1 | CR2032 SMD holder | RTC coin cell | C70376 | 1 | $0.28 |
| U8, U9 | USBLC6-2SC6 | USB ESD/TVS | C7469 | 2 | $0.16 |
| SW1 | Momentary 6×6 mm tact | Reset button | C318884 | 1 | $0.08 |
| SW2 | Momentary 6×6 mm tact | Boot/recovery button | C318884 | 1 | $0.08 |
| D1–D5 | 0603 green/red LEDs | Power, activity, link, status | C72043 | 5 | $0.03 |
| — | Passives (R, C, L, ferrites) | ~120 in total, 0402/0603 | JLC Basic | — | ~$3 total |

### PCB
| Item | Spec | Price (qty 10 at JLCPCB) |
|---|---|---|
| 4-layer PCB, 100 × 100 mm, ENIG, black soldermask | Standard stackup, 1 oz Cu | ~$25 total ($2.50/board) |
| JLC PCBA (all SMD assembled) | 1-side, standard | ~$8/board |

### Rolled-up cost per finished board (qty 10)

| Version | PCB | PCBA | Components (per board) | **Empty PCB total** | Add CM5 8GB | **All-in** |
|---|---|---|---|---|---|---|
| Base (no PoE) | $2.50 | $8 | ~$26 | **~$36.50** | +$89 | **$125.50** |
| Full (with PoE) | $2.50 | $9 | ~$32 | **~$43.50** | +$89 | **$132.50** |

Room to sell base @ **$99 (empty PCB only)** or **$199 (with 8GB CM5 pre-installed)** and still keep ~40% margin. 🎯

---

## Block diagram

```
                        ┌──────────────────────────────────┐
                        │      Radxa CM5 (RK3588S2)        │
                        │  8-core • 8GB LPDDR4X • 64GB eMMC│
                        │  Native: 1 GbE, HDMI, USB3.0,    │
                        │  PCIe 2.1 x1, MIPI-DSI/CSI, GPIO │
                        └──┬───┬───┬───┬───┬───┬───┬───────┘
                           │   │   │   │   │   │   │
              ┌────────────┘   │   │   │   │   │   └──────────────┐
              │                │   │   │   │   │                  │
        ┌─────▼─────┐    ┌─────▼─┐ │   │   │ ┌─▼──────┐   ┌───────▼─────┐
        │ RTL8125BG │    │ RJ45  │ │   │   │ │ HDMI 2.0│   │ 40-pin GPIO │
        │  2.5 GbE  │◄──►│ #1 PoE│ │   │   │ └─────────┘   │  Pi-compat  │
        │  (2nd NIC)│    │ 1 GbE │ │   │   │               └─────────────┘
        └─────┬─────┘    └───────┘ │   │   │
              │                    │   │   │
         ┌────▼────┐            ┌──▼─┐ │  ┌▼─────────┐
         │  RJ45 #2│            │M.2 │ │  │ 4× USB   │
         │ 2.5 GbE │            │E-key│ │  │ 3.0 A   │
         │ (opt PoE│            │2230 │ │  └──────────┘
         │  input) │            │(WiFi│ │
         └────┬────┘            │/NIC)│ │
              │                 └─────┘ │
         ┌────▼──────┐         ┌────────▼─┐
         │ MP8007 PoE│         │ M.2 M-key│
         │  PD (opt) │         │  2280    │
         └────┬──────┘         │  NVMe    │
              │                └──────────┘
        ┌─────▼─────┐    ┌──────────────┐   ┌───────────┐
        │ CH224K PD │◄───│  USB-C in    │   │ DS3231 RTC│
        │  trigger  │    │ (5/12/20V)   │   │ +CR2032   │
        └─────┬─────┘    └──────────────┘   └───────────┘
              │
        ┌─────▼──────┐
        │ MP2315 buck│──► 5V rail (CM5, USB, fan, etc.)
        │ + AP2112   │──► 3.3V aux (RTC, LEDs, logic)
        └────────────┘
```

## Repo layout (planned)

```
nodepad/
├── README.md                (this file)
├── DESIGN.md                (deep design rationale, pin assignments, DRC rules)
├── BOM.csv                  (machine-readable, for JLC PCBA upload)
├── PCB/                     (KiCad 10 project)
│   ├── NodePad.kicad_pro
│   ├── NodePad.kicad_sch    (multi-sheet: cpu, network, power, io)
│   └── NodePad.kicad_pcb
├── CAD/                     (case: front, back, mount plate)
│   └── nodepad-case.step
├── Production/
│   ├── gerbers.zip
│   ├── bom.csv              (JLC PCBA format)
│   ├── cpl.csv              (component placement)
│   └── assembly-drawings.pdf
├── Firmware/                (bootloader configs, device tree overlay if needed)
└── docs/
    └── quick-start.md
```

---

## ✅ Decisions locked in

| # | Decision | Choice |
|---|---|---|
| 1 | **PoE** | Footprint-only (populate optional) |
| 2 | **HDMI** | Kept |
| 3 | **2nd 2.5 GbE NIC** | On-board RTL8125BG (biggest diff vs Pi 5) |
| 4 | **USB 3.0 ports** | 4× vertical Type-A (via GL3523 hub) |
| 5 | **License** | CERN-OHL-P v2 |

---

## Next steps (in order)

- [x] Design brief locked
- [x] KiCad 10 project scaffold created (`/PCB/NodePad.kicad_pro`, `.kicad_sch`, `.kicad_pcb`)
- [x] 100 × 100 mm board outline with 4× M2.5 mounting holes
- [x] 4-layer stackup + JLC-tuned design rules + net classes (PCIe / USB3 / Ethernet / HDMI / Power)
- [x] BOM.csv with LCSC part numbers
- [x] LICENSE (CERN-OHL-P v2)
- [ ] Schematic capture — power tree
- [ ] Schematic capture — CM5 SoM connectors + decoupling
- [ ] Schematic capture — RTL8125 NIC + magnetics
- [ ] Schematic capture — M.2 M-key + E-key slots
- [ ] Schematic capture — GL3523 USB 3.0 hub + 4× USB-A
- [ ] Schematic capture — HDMI, GPIO header, RTC, buttons, LEDs
- [ ] Schematic capture — PoE section (footprint-only, DNP)
- [ ] ERC clean
- [ ] Footprint assignment (JLC-Basic priority)
- [ ] PCB placement
- [ ] PCB routing (PCIe → USB3 → HDMI → Ethernet → GPIO)
- [ ] DRC clean
- [ ] Gerber + CPL + BOM export
- [ ] Order 5 prototypes from JLCPCB (~$400)
- [ ] Bring-up + rev 2 fixes
- [ ] Sellable rev 2 spin

Realistic total timeline from your side: **~3 months part-time** to a rev-2 sellable board. My share (design + docs) is front-loaded in the first 2–3 weeks.

---

## Honest disclaimer

I can draft the schematic + rough PCB layout in KiCad and give you a starting point you can iterate on. **High-speed routing (2.5GbE differential pairs, PCIe Gen 2, USB 3.0)** benefits massively from human review before you spend money on prototypes — it's not the kind of thing to click "generate" and ship. Plan for at least **one rev-2 spin** to fix the bugs the first prototype reveals. Every serious hardware product does this.
