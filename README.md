# five-finger-gestures

**Real 5-finger touchpad gestures on Linux, kept separate from your 4-finger
gestures.** Swipe five fingers to skip a song while four fingers still switch
workspaces. Also adds a 4-finger tap.

[![Latest release](https://img.shields.io/github/v/release/aadheel/five-finger-gestures)](https://github.com/aadheel/five-finger-gestures/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![Python 3.6+, no dependencies](https://img.shields.io/badge/python-3.6%2B%2C%20no%20dependencies-informational)
![Wayland and X11](https://img.shields.io/badge/Wayland%20%26%20X11-supported-success)

| Gesture (default config) | Does |
|---|---|
| 5-finger slide up / down | Volume up / down, step by step as you slide |
| 5-finger swipe left / right | Previous / next song |
| 5-finger tap | Play / pause |
| 4-finger tap | Screenshot tool |
| 5-finger pinch in / out | Nothing by default — add your own |

Every gesture can press any key combo or run any command, and the sensitivity
is adjustable, all from one config file. Your normal 1–4 finger gestures
(scrolling, workspace swipes, overview, …) keep working exactly as before.

Pure Python 3 standard library, no dependencies. Works on Wayland and X11.

## Why this exists

libinput, the touchpad driver behind GNOME, KDE and most Wayland desktops,
has no separate 5-finger gestures: a 5-finger swipe is reported as a 4-finger
swipe (one finger is usually taken for a resting thumb). Gesture tools such as
libinput-gestures, Fusuma or Touchegg read libinput's gesture events, so they
can't tell 4 fingers from 5. And even a tool that reads the touchpad directly
can't stop the desktop from also acting on the swipe it saw as 4 fingers.

### Compared to other tools

| | five-finger-gestures | libinput-gestures | Fusuma | Touchégg |
|---|---|---|---|---|
| Tells 5 fingers from 4 | **Yes** | No | No | No |
| 5-finger gestures leave the desktop's 4-finger gestures alone | **Yes** | No | No | No |
| Presses keys on Wayland with no extra tools | Yes (own virtual keyboard) | No (xdotool / ydotool) | No (ydotool) | Depends on desktop |
| 3- and 4-finger swipes and pinches | No (left to your desktop) | Yes | Yes | Yes |
| Language / dependencies | Python 3, nothing else | Python 3, libinput-tools | Ruby | C++ daemon |

All of them read libinput's gesture events except this one, which reads the
touchpad itself; that is what makes the 5-finger difference possible.

The tools work well together: use your desktop or one of the others for
3- and 4-finger gestures, and this one for 5 fingers.

## How it works

1. It finds your touchpad and checks it can track at least 5 fingers at once.
2. It creates a **virtual copy** of the touchpad through `/dev/uinput` (same
   name, IDs, size and axes, so libinput gives it the same settings and
   quirks) and takes the real touchpad for itself (`EVIOCGRAB`). Your desktop
   now uses the copy.
3. Every touch with 1–4 fingers is passed through to the copy unchanged.
4. When a 5th finger lands, the copy's fingers are frozen until the hand
   lifts. The desktop sees fingers resting, not a gesture. The program follows
   each finger, measures the swipe, slide, pinch or tap, and runs your action.
   Fingers that the touchpad drops mid-swipe don't spoil the measurement.
5. A 4-finger tap is passed through as usual (libinput ignores 4-finger taps)
   and just watched for.

If the program stops or crashes, the kernel releases the real touchpad and
removes the copy, so your touchpad simply goes back to normal.

## Requirements

- Linux with a touchpad that tracks 5 fingers (most modern precision
  touchpads do; `--check` tells you if yours doesn't).
- Python 3.6+.
- Permission to read the touchpad: be in the `input` group.
- Permission to write `/dev/uinput`. Many distros already grant this to the
  logged-in user (Steam's udev rules do, for example). `install.sh` checks
  and offers to add a udev rule if needed.

### Tested on

| Distro | Desktop | Laptop / touchpad | Works |
|---|---|---|---|
| Pop!\_OS 24.04 | GNOME 46, Wayland | Dell, DELL0CAA 27C6:0D53 (Goodix) | Yes |

Tried it somewhere else? Please
[add your laptop](https://github.com/aadheel/five-finger-gestures/issues/new?template=device-report.yml),
whether it worked or not. It takes a minute and helps the next person.

### Is it safe?

It's one readable Python file with no dependencies and no network access. It
needs to read your touchpad (the `input` group) and create virtual input
devices (`/dev/uinput`). Note that the `input` group lets any program you run
read all input devices, keyboards included; that's the same permission
libinput-gestures and Fusuma need. The program only opens the touchpad and
`/dev/uinput`, and only runs the actions written in your config.

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

Edit `~/.config/five-finger-gestures.conf` (with a system-wide install that
only has `/etc/five-finger-gestures.conf`, copy that to `~/.config/` first and
restart the program). Changes apply on the next
gesture, no restart needed. Then run `five-finger-gestures --check` to see
what each gesture does and catch typos.

```ini
slide up     = key volumeup         # repeats while you keep sliding
slide down   = key volumedown
swipe left   = key previoussong     # once, when you lift
swipe right  = key nextsong
tap          = key playpause
pinch out    = key super+a
4-finger tap = key print

slide step   = 7mm                  # settings
```

### Gestures

| Name | When it fires |
|---|---|
| `swipe up/down/left/right` | Once, when you lift your 5 fingers |
| `slide up/down/left/right` | Every *slide step* while your 5 fingers keep moving. Moving back the other way fires the opposite slide, like dragging a slider |
| `tap` | 5 fingers land and lift quickly without moving |
| `pinch in` / `pinch out` | 5 fingers close together / spread apart |
| `4-finger tap` | 4 fingers land and lift quickly (4-finger swipes stay with your desktop) |

Use either `swipe` or `slide` for a direction, not both: if a slide is set,
the swipe in that direction is ignored.

### Actions

- `key <combo>` presses keys, e.g. `key super+a`, `key ctrl+shift+t`,
  `key brightnessup`. The desktop sees real key presses, so its own shortcuts
  and media keys work, with no "allow remote control" prompt. See all key
  names with `five-finger-gestures --list-keys`. Letters follow US key
  positions.
- Anything else runs as a command, e.g. `notify-send "hi"`,
  `x-terminal-emulator`, `pactl set-sink-volume @DEFAULT_SINK@ +2%`.
  `~` and `$VARS` are expanded; there's no shell, so wrap pipes in
  `sh -c "…"`.

### Settings

| Setting | Default | Meaning |
|---|---|---|
| `swipe distance` | `6mm` | How far the fingers must move for a swipe |
| `slide step` | `7mm` | How far to move per repeat of a slide |
| `tap max move` | `3mm` | A tap moves less than this |
| `tap max time` | `0.35s` | A tap lifts within this time (`350ms` works too) |
| `pinch amount` | `30%` | How much the fingers must close or spread |

## Commands

```sh
five-finger-gestures --check        # what each gesture does, config problems, permissions
five-finger-gestures --debug        # run in the foreground and log every 5-finger touch
five-finger-gestures --list-keys    # key names for `key` actions
five-finger-gestures --key super+a  # press a key combo once (same as: gesture-key super+a)
five-finger-gestures --config FILE  # use another config file
five-finger-gestures --device /dev/input/eventN   # pick the touchpad
```

## Troubleshooting

Stop the background copy and watch what the program sees:

```sh
pkill -f five-finger-gestures
five-finger-gestures --debug
```

It logs every 5-finger touch with how far the fingers moved and which gesture
and action it chose. Press Ctrl+C to stop, then start it again with
`setsid -f five-finger-gestures` or by logging in again.

If your touchpad ever misbehaves, `pkill -f five-finger-gestures` gives the
real touchpad straight back to your desktop.

Notes:

- Your touchpad shows up twice in device lists (`libinput list-devices`,
  `xinput`): the real one, which the program holds, and the virtual copy
  that your desktop uses. There's also a "five-finger-gestures keyboard" for
  `key` actions.
- With several touchpads, the first one found is used; pick another with
  `--device`.

## Development

`python3 tests/test_gestures.py` runs an end-to-end test without a real
touchpad: it creates a fake touchpad, runs a test instance on it and checks
the swipes, slides, taps and pinches it recognises. Your real touchpad and
running copy aren't affected.

## Uninstall

```sh
./uninstall.sh
```

## License

MIT, see [LICENSE](LICENSE).
