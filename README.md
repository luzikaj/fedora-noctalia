# fedora-noctalia

A personal Fedora Atomic (bootc) spin:

- **Fedora 45** `fedora-bootc` base, updated atomically with `bootc`
- **Umbriel** compositor (Terra `umbriel-nightly`)
- **Noctalia** v5 shell (Fedora repos) and **Noctalia Greeter** on greetd (Terra)
- Helix, Fresh, Ghostty (foot as a fallback), k9s and keyd, plus your own configs in `/etc/skel`
- One-handed, right-hand Dvorak keybinds: Mod plus one key, never Shift

## Layout

```
Containerfile                 image definition
build_files/packages.txt      required RPMs (build fails if one is missing)
build_files/packages-optional.txt  installed if available, warning otherwise
build_files/build.sh          package stage
build_files/finalize.sh       greetd, services, Umbriel config validation
system_files/                 copied onto / (etc/xdg/umbriel/config.toml, etc/skel, etc/keyd, units)
scripts/import-my-dotfiles.sh pulls your helix/fresh/ghostty/k9s/keyd configs into system_files
iso/config.toml               Anaconda ISO settings for bootc-image-builder
.github/workflows/            build+push to ghcr.io, and an on-demand ISO build
```

## First run

1. On your current Fedora machine, from the repo root:
   `./scripts/import-my-dotfiles.sh`, then review `git diff` (keep secrets and kubeconfigs out).
2. Push to GitHub. The **build-image** workflow pushes `ghcr.io/<you>/<repo>:latest`.
   In the package settings, make the package **public**, or installed machines will need registry credentials to update.
3. Run **build-iso** (Actions → build-iso → Run workflow) and download the ISO artifact.
4. Test it in your VirtualBox VM first (EFI on, 4+ GB RAM, VMSVGA with 3D).
   In the installer, choose your keyboard layout and create your user.
5. Log in through the Noctalia greeter, selecting the Umbriel session.

Local alternative: `just build`, then `just iso` (needs podman and sudo).

## Updates

`bootc-stage-update.timer` downloads new images daily and stages them.
They apply on your next reboot. The stock auto-reboot timer is masked.

```
sudo bootc upgrade          # fetch now
sudo bootc status
sudo bootc rollback         # boot the previous image next time
```

Edit the repo and push. CI also rebuilds weekly.

## Keybinds (Dvorak letters, QWERTY position in brackets)

| Keys | Action |
|---|---|
| Mod (tap) / Mod+Space | Noctalia launcher |
| Mod+Return | Terminal |
| Mod+BackSpace | Close window |
| Mod+D H T N `[h j k l]` | Focus left / down / up / right |
| Mod+F G C R `[y u i o]` | Move column left / window down / window up / column right |
| Mod+S `[;]` | Overview |
| Mod+L `[p]` | Fullscreen |
| Mod+M | Maximize to edges |
| Mod+Z `[/]` | Toggle floating |
| Mod+W / Mod+V `[, .]` | Consume into column left / right |
| Mod+/ `[[]` | Cycle width preset |
| Mod+- / Mod+= `[' ]]` | Narrower / wider |
| Mod+[ / Mod+] `[- =]` | Toggle tabs / next tab |
| Mod+6 7 8 9 0 | Workspace 1–5 |
| Mod+PgUp / PgDn | Previous / next workspace |
| Mod+B `[n]`, then 6–0 or PgUp/PgDn | Send window to workspace (Esc cancels) |
| Mod+Insert / Home / End / Delete | Clipboard / control center / settings / session menu |
| Mod+\ | Keybind cheatsheet |
| Print | Region screenshot |
| Mod+Pause | Pass all keys through to the focused app (games, VMs) |

`Mod` is Super. keyd turns held Right Alt into Super, using your existing
keyd config, so Right Alt stays both Mod and AltGr for Polish letters.

To customise per user: `cp /etc/xdg/umbriel/config.toml ~/.config/umbriel/` and edit it.
The user file replaces the system one completely.
