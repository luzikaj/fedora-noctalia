#!/usr/bin/env bash
# Package stage. Runs once inside the container build.
set -euo pipefail

list() { grep -vE '^[[:space:]]*(#|$)' "$1"; }

# Writable dirs some RPM scriptlets expect on a bootc base
mkdir -p /var/roothome

dnf -y install dnf5-plugins

# Terra: provides umbriel-nightly, noctalia-greeter (and usually ghostty, keyd ...)
dnf -y install --nogpgcheck \
    --repofrompath 'terra,https://repos.fyralabs.com/terra$releasever' terra-release

# Required packages
mapfile -t required < <(list /ctx/packages.txt)
dnf -y install "${required[@]}"

# Optional packages: skip what no enabled repo has, then report it
mapfile -t optional < <(list /ctx/packages-optional.txt)
if ((${#optional[@]})); then
    dnf -y install --skip-unavailable "${optional[@]}"
    for p in "${optional[@]}"; do
        rpm -q "$p" >/dev/null 2>&1 || echo "::warning::optional package not available: $p"
    done
fi

# Fresh editor: no Fedora/COPR/Terra package; install the latest GitHub release
# RPM, checksum-verified (same as fedora-gnc's fedora-setup.sh).
if ! rpm -q fresh-editor >/dev/null 2>&1 && ! command -v fresh >/dev/null; then
    tmp=$(mktemp -d)
    rel=$(curl -fsSL https://api.github.com/repos/sinelaw/fresh/releases/latest) || rel=""
    url=$(jq -r '.assets[].browser_download_url' <<<"$rel" 2>/dev/null | grep -E "\.$(uname -m)\.rpm$" | head -n1 || true)
    if [[ -n $url ]] \
        && curl -fsSL -o "$tmp/fresh.rpm" "$url" \
        && curl -fsSL -o "$tmp/fresh.rpm.sha256" "$url.sha256" \
        && [[ $(sha256sum "$tmp/fresh.rpm" | cut -d' ' -f1) == $(cut -d' ' -f1 "$tmp/fresh.rpm.sha256") ]]; then
        dnf -y install "$tmp/fresh.rpm"
    else
        echo "::warning::Fresh editor: could not download/verify the release RPM"
    fi
    rm -rf "$tmp"
fi

dnf clean all
