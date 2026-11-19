#!/bin/sh
# Remove five-finger-gestures. Your config file is kept.
BIN="$HOME/.local/bin"

pkill -f "$BIN/five-finger-gestures" 2>/dev/null && echo "Stopped five-finger-gestures"
rm -f "$BIN/five-finger-gestures" "$BIN/gesture-key" \
      "$HOME/.config/autostart/five-finger-gestures.desktop"
echo "Removed the programs and the login autostart entry."
echo "Kept ~/.config/five-finger-gestures.conf (delete it yourself if you like)."
if [ -e /etc/udev/rules.d/70-five-finger-gestures-uinput.rules ]; then
    echo "The install added /etc/udev/rules.d/70-five-finger-gestures-uinput.rules;"
    echo "remove it with: sudo rm /etc/udev/rules.d/70-five-finger-gestures-uinput.rules"
fi
