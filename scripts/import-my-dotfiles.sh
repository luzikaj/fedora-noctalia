#!/usr/bin/env bash
# Run this on your CURRENT Fedora machine, from the repo root.
# Copies your configs into the image tree:
#   ~/.config/{helix,fresh,ghostty,k9s} -> system_files/etc/skel/.config/
#   /etc/keyd/*.conf                     -> system_files/etc/keyd/
# New users get /etc/skel at account creation; review the copies before committing
# (no secrets, tokens or kubeconfigs!).
set -euo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
skel="$repo/system_files/etc/skel/.config"
mkdir -p "$skel" "$repo/system_files/etc/keyd"

for app in helix fresh ghostty k9s; do
    src="$HOME/.config/$app"
    if [[ -d $src ]]; then
        rm -rf "${skel:?}/$app"
        cp -a "$src" "$skel/$app"
        echo "copied  ~/.config/$app"
    else
        echo "skipped ~/.config/$app (not found)"
    fi
done

# k9s keeps cluster state/logs/screen dumps next to its config: keep config only
if [[ -d $skel/k9s ]]; then
    find "$skel/k9s" -mindepth 1 -maxdepth 1 \
        ! -name 'config.yaml' ! -name 'plugins.yaml' ! -name 'hotkeys.yaml' \
        ! -name 'aliases.yaml' ! -name 'views.yaml' ! -name 'skins' \
        -exec rm -rf {} +
fi

if compgen -G "/etc/keyd/*.conf" >/dev/null; then
    cp /etc/keyd/*.conf "$repo/system_files/etc/keyd/"
    echo "copied  /etc/keyd/*.conf"
else
    echo "skipped /etc/keyd (no .conf files)"
fi

# Umbriel reads Mod as Super; your keyd config must emit meta (M) for held Right Alt.
if grep -rqs 'rightalt' "$repo/system_files/etc/keyd/"; then
    echo "keyd: rightalt mapping found. Check it produces Super (M) for Mod binds."
fi

echo
git -C "$repo" status --short system_files/ || true
