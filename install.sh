#!/bin/sh
# Install five-finger-gestures for the current user (no root needed, except
# for the one-time permission setup it offers at the end if required).
set -e
cd "$(dirname "$0")"

BIN="$HOME/.local/bin"
CONF="$HOME/.config/five-finger-gestures.conf"
AUTOSTART="$HOME/.config/autostart/five-finger-gestures.desktop"
UDEV_RULE=/etc/udev/rules.d/70-five-finger-gestures-uinput.rules

command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }

mkdir -p "$BIN" "$(dirname "$AUTOSTART")"
install -m 755 five-finger-gestures gesture-key "$BIN/"
echo "Installed five-finger-gestures and gesture-key to $BIN"

if [ -e "$CONF" ]; then
    echo "Kept your existing $CONF"
else
    install -m 644 five-finger-gestures.conf "$CONF"
    echo "Created $CONF"
fi

cat > "$AUTOSTART" <<EOF
[Desktop Entry]
Type=Application
Name=Five-finger gestures
Comment=5-finger touchpad gestures (settings: ~/.config/five-finger-gestures.conf)
Exec=$BIN/five-finger-gestures
NoDisplay=true
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
echo "It will start automatically when you log in ($AUTOSTART)"

# --- permissions: read the touchpad (input group), write /dev/uinput ---
need_group=no; need_uinput=no; relogin=no
if ! id -nG "$USER" | grep -qw input; then
    need_group=yes
elif ! id -nG | grep -qw input; then
    relogin=yes  # added to the group, but this session predates it
fi
[ -w /dev/uinput ] || need_uinput=yes

if [ $need_group = yes ] || [ $need_uinput = yes ]; then
    echo
    echo "One-time setup needs root:"
    [ $need_group = yes ] && echo "  sudo usermod -aG input $USER          # read the touchpad"
    [ $need_uinput = yes ] && echo "  a udev rule giving your session access to /dev/uinput ($UDEV_RULE)"
    printf "Run it now with sudo? [y/N] "
    read -r answer
    case "$answer" in
        y|Y|yes)
            [ $need_group = yes ] && sudo usermod -aG input "$USER"
            if [ $need_uinput = yes ]; then
                echo 'KERNEL=="uinput", SUBSYSTEM=="misc", TAG+="uaccess", OPTIONS+="static_node=uinput"' \
                    | sudo tee "$UDEV_RULE" >/dev/null
                sudo udevadm control --reload
                sudo modprobe uinput || true
                sudo udevadm trigger --name-match=uinput || true
            fi
            echo "Done. Log out and back in, and five-finger-gestures will start."
            ;;
        *)
            echo "Skipped. Run those steps yourself, then log out and back in."
            ;;
    esac
    exit 0
fi

if [ $relogin = yes ]; then
    echo "Log out and back in (your 'input' group membership isn't active yet)."
    exit 0
fi

# Restart it now so the new version is used.
pkill -f "$BIN/five-finger-gestures" 2>/dev/null && sleep 0.5 || true
nohup setsid "$BIN/five-finger-gestures" >/dev/null 2>&1 </dev/null &
echo "Started. Try a 5-finger swipe!"
