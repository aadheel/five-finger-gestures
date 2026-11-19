# five-finger-gestures

5-finger touchpad gestures for Linux, plus a 4-finger tap, that **don't also
trigger your desktop's 4-finger gestures**.

| Gesture (default config) | Does |
|---|---|
| 5-finger swipe left / right | Previous / next song |
| 5-finger swipe up / down | Volume up / down |
| 5-finger tap | Play / pause |
| 4-finger tap | Screenshot tool |
| 5-finger pinch in / out | Nothing by default — add your own |

Every gesture runs whatever command you put in the config file. Your normal
1–4 finger gestures (scrolling, workspace swipes, overview, …) keep working
exactly as before.

Pure Python 3 standard library, no dependencies, about 400 lines. Works on
Wayland and X11.

## Why this exists

libinput, the touchpad driver behind GNOME, KDE and most Wayland desktops,
has no separate 5-finger gestures: a 5-finger swipe is reported as a 4-finger
swipe (one finger is usually taken for a resting thumb). Gesture tools such as
libinput-gestures, Fusuma or Touchegg read libinput's gesture events, so they
can't tell 4 fingers from 5. And even a tool that reads the touchpad directly
can't stop the desktop from also acting on the swipe it saw as 4 fingers.

## How it works

1. It finds your touchpad and checks it can track at least 5 fingers at once.
2. It creates a **virtual copy** of the touchpad through `/dev/uinput` (same
   name, IDs, size and axes, so libinput gives it the same settings and
   quirks) and takes the real touchpad for itself (`EVIOCGRAB`). Your desktop
   now uses the copy.
3. Every touch with 1–4 fingers is passed through to the copy unchanged.
4. When a 5th finger lands, the copy's fingers are frozen until the hand
   lifts. The desktop sees fingers resting, not a gesture. The program follows
   each finger, measures the swipe, pinch or tap, and runs your command.
   Fingers that the touchpad drops mid-swipe don't spoil the measurement.
5. A 4-finger tap is passed through as usual (libinput ignores 4-finger taps)
   and just watched for.

If the program stops or crashes, the kernel releases the real touchpad and
removes the copy, so your touchpad simply goes back to normal.

## Requirements

- Linux with a touchpad that tracks 5 fingers (most modern precision
  touchpads do; the program tells you if yours doesn't).
- Python 3.6+.
- Permission to read the touchpad: be in the `input` group.
- Permission to write `/dev/uinput`. Many distros already grant this to the
  logged-in user (Steam's udev rules do, for example). `install.sh` checks
  and offers to add a udev rule if needed.

Tested on Pop!\_OS 24.04 with GNOME 46 (Wayland) on a Dell laptop. Reports from
other desktops and touchpads are welcome.

## Install

```sh
git clone https://github.com/aadheel/five-finger-gestures.git
cd five-finger-gestures
./install.sh
```

This installs `five-finger-gestures` and `gesture-key` to `~/.local/bin`, a
default config to `~/.config/five-finger-gestures.conf` (an existing one is
kept), and an autostart entry so it runs when you log in. If the permissions
above are missing, it shows the one-time `sudo` steps and offers to run them;
after that, log out and back in.

## Configure

Edit `~/.config/five-finger-gestures.conf`. Changes apply on the next
gesture, no restart needed.

```ini
swipe up     = ~/.local/bin/gesture-key volumeup
swipe right  = x-terminal-emulator
tap          = ~/.local/bin/gesture-key playpause
pinch out    = ~/.local/bin/gesture-key super+a
4-finger tap = ~/.local/bin/gesture-key print
```

Gesture names: `swipe up`, `swipe down`, `swipe left`, `swipe right`, `tap`,
`pinch in`, `pinch out` (all 5-finger), and `4-finger tap`.

`gesture-key` presses a key combination through a virtual keyboard, so it
triggers your desktop's own shortcuts and media keys without any
"allow remote control" prompt. Run `gesture-key` with no arguments to see the
supported key names (letters, digits, modifiers, arrows, F1–F12, media and
volume keys, Print, …).

Thresholds such as the minimum swipe distance (6 mm) and the maximum tap time
(0.35 s) are constants at the top of `five-finger-gestures`.

## Troubleshooting

Stop the background copy and watch what the program sees:

```sh
pkill -f five-finger-gestures
five-finger-gestures --debug
```

It logs every 5-finger touch with how far the fingers moved and which gesture
and command it chose. Press Ctrl+C to stop, then start it again with
`setsid -f five-finger-gestures` or by logging in again.

If your touchpad ever misbehaves, `pkill -f five-finger-gestures` gives the
real touchpad straight back to your desktop.

Notes:

- Your touchpad shows up twice in device lists (`libinput list-devices`,
  `xinput`): the real one, which the program holds, and the virtual copy
  that your desktop uses.
- With several touchpads, the first one found is used; pick another with
  `--device /dev/input/eventN`.

## Uninstall

```sh
./uninstall.sh
```

## License

MIT, see [LICENSE](LICENSE).
