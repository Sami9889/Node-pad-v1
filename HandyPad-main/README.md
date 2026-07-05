# HandyPad

A clean, minimal, handy macropad for times when a 104 keys aren't enough 

*(or just an easier way to copy and paste)* 


<img width="802" height="460" alt="image" src="https://github.com/user-attachments/assets/417881f1-8a16-427b-800c-dba7bb696b5f" />



---

## Quick Start

1. Hold **BOOT** and plug in your XIAO RP2040.
2. Drop `nilay_macropad_default.uf2` onto the `RPI-RP2` drive.
3. Plug it back in. Watch the little car rev on the OLED.

---

## Features

- **OLED display** to display custom memes or other info
- **Rotary encoder and button** for volume adjustment, scrolling, or whatever you want to map it to!
- **7 keys** to map to the shortcuts you desire
- Every key press (including the encoder push) makes a **car rev on the OLED**

---

## Defaults (if you don't want to change anything):

### Keys:

| Row        | Key 1           | Key 2           | Key 3         | Key 4        |
|------------|-----------------|-----------------|---------------|--------------|
| **Top**    | Play/Pause      | Previous Track  | Next Track    | Rotary Encoder In This Spot|
| **Bottom** | Copy (Ctrl+C)   | Paste (Ctrl+V)  | Undo (Ctrl+Z) | Print Screen |

### Encoder:

- **Rotate left** → Volume Down
- **Rotate right** → Volume Up
- **Push** → Mute

---

## What is this?

This is a macropad I built to assist me at my desk. This device can come in handy whether you're designing something in CAD, working on a PCB, gaming, or really anything you would like to use it for.

## How it works and Issues I Faced

The Xiao rp2040 is mounted on the bottom of the PCB along with the diodes. The rest of the components are on the top. The macropad is running **QMK** for the keymaps, screen, and knob. Pretty obvious, but it uses a matrix layout for the switches. 

When I was designing the PCB I wanted to make this macropad as compact as possible with its current hardware which was challenging. I had to reposition the components several times before I was satisfied. I also spent quite some time in CAD designing this case as I wanted to make it as clean as possible. It took me quite some while to find the right shape and and size without making it look awkward.

---

## BOM

- 1x unsoldered Seeed XIAO RP2040
- 7x through-hole 1N4148 Diodes
- 7x MX-Style switches
- 1x EC11 Rotary encoder
- 1x 0.91 inch OLED display *(the pin order is GND-VCC-SCL-SDA, **MAKE SURE YOUR PCB MATCHES**)*
- 7x white blank DSA keycaps
- 6x M3x16mm screws

---

## Renders

<img width="929" height="648" alt="Screenshot 2026-06-10 213152" src="https://github.com/user-attachments/assets/f5808cac-8802-414a-8558-305516b8b752" />
<img width="585" height="562" alt="Screenshot 2026-06-06 142748" src="https://github.com/user-attachments/assets/f998e8e6-ef55-478a-8692-23534d02d841" />
<img width="427" height="596" alt="Screenshot 2026-06-30 115217" src="https://github.com/user-attachments/assets/94caf92b-771c-4275-b181-fab46d716bd0" />
<img width="829" height="654" alt="Screenshot 2026-06-11 084459" src="https://github.com/user-attachments/assets/3e8333df-a878-4278-a8e8-20f8c56589e8" />

---

## Credits

Big shout out to **Hack Club** for giving me the opportunity to make this macropad. I would also like to thank [Logan Peterson](https://github.com/SharKingStudios/SplashPad/tree/main), as I modeled my readme.md after his hackpad's since I was amazed by how well written it was.

---

## Disclaimer

This project is open source. If anything you make out of this does not work or has any issues, I sincerely apologize, but at the end of the day **that's on you.**
