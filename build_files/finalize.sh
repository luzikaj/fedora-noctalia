#!/usr/bin/env bash
# Post-copy stage: services, greetd, sanity checks.
set -euo pipefail

# --- greetd -> Noctalia greeter -------------------------------------------
# Use whichever greeter account the greetd/noctalia-greeter packages created.
greeter_user=""
for u in greeter greetd; do
    if getent passwd "$u" >/dev/null; then greeter_user=$u; break; fi
done
[[ -n $greeter_user ]] || { echo "No greeter account found (greeter/greetd)"; exit 1; }
greeter_group=$(id -gn "$greeter_user")

mkdir -p /etc/greetd
cat > /etc/greetd/config.toml <<EOF
[terminal]
vt = 1

[default_session]
command = "$(command -v noctalia-greeter-session)"
user = "${greeter_user}"
EOF

{
    if [[ $greeter_user != greeter ]]; then
        echo "d /var/lib/noctalia-greeter 0750 ${greeter_user} ${greeter_group} -"
    fi
    # Seed the greeter config (wallpaper, default session) once; never overwrite.
    echo "C /var/lib/noctalia-greeter/greeter.toml - - - - /usr/share/fedora-noctalia/greeter.toml"
    echo "z /var/lib/noctalia-greeter/greeter.toml 0644 ${greeter_user} ${greeter_group} -"
} > /usr/lib/tmpfiles.d/noctalia-greeter-local.conf

systemctl enable greetd.service
systemctl enable noctalia-greeter-setup.service
systemctl set-default graphical.target

# --- other services --------------------------------------------------------
systemctl enable bluetooth.service
systemctl enable fwupd-refresh.timer 2>/dev/null || true
if rpm -q keyd >/dev/null 2>&1; then
    systemctl enable keyd.service
fi

# Updates: stage new images daily, apply on the next reboot you choose.
# (The stock timer reboots the machine without warning.)
systemctl mask bootc-fetch-apply-updates.timer
systemctl enable bootc-stage-update.timer

# --- sanity checks -----------------------------------------------------------
# Fail the build on a broken Umbriel config instead of at first login.
XDG_CONFIG_HOME=/nonexistent XDG_CONFIG_DIRS=/etc/xdg umbriel config validate
noctalia config validate /etc/xdg/noctalia/10-fedora-noctalia.toml
test -r /usr/share/backgrounds/fedora-noctalia/noctalia-night-3840x2160.jpg

for bin in umbriel start-umbriel noctalia noctalia-greeter-session; do
    command -v "$bin" >/dev/null || { echo "missing binary: $bin"; exit 1; }
done
ls /usr/share/wayland-sessions/
