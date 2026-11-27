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

dnf clean all
