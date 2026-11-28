# fedora-noctalia

A personal Fedora Atomic (bootc) spin:

- **Fedora 45** `fedora-bootc` base, updated atomically with `bootc`
- **Umbriel** compositor (Terra `umbriel-nightly`)
- **Noctalia** v5 shell (Fedora repos) and **Noctalia Greeter** on greetd (Terra)
- Helix, Fresh, Ghostty (foot as a fallback), k9s and fish, with the one-handed configs from fedora-gnc
- One-handed: right-handed Dvorak + Polish letters, keyd (Right Alt = Mod, sticky Ctrl/Shift), Mod + one key

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
vmware/fedora-noctalia.vmx    VMware Workstation VM template (3D, UEFI, SATA, NAT)
artwork/                      wallpaper + keybind cheat-sheet generators
.github/workflows/            image build+push, on-demand ISO and VMware VM builds
```

## First run

1. On your current Fedora machine, from the repo root:
   `./scripts/import-my-dotfiles.sh`, then review `git diff` (keep secrets and kubeconfigs out).
2. Push to GitHub. The **build-image** workflow pushes `ghcr.io/<you>/<repo>:latest`.
   In the package settings, make the package **public**, or installed machines will need registry credentials to update.
3. Test in VMware Workstation: run **build-vmware-vm**, download the `fedora-noctalia-45-<date>-vmware-vm` artifact,
   unzip it on a drive with space, and File → Open `fedora-noctalia.vmx`.
   Log in as your user (password: secret `VM_PASSWORD`, else `changeme`), then `passwd`.
   No installer involved; keyboard layout: `sudo localectl set-x11-keymap <layout> "" <variant>`.
4. For real hardware, run **build-iso** and write the ISO to a USB stick.
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

## Keyboard & keybinds (one-handed, right hand)

Built for a Logitech G413 TKL (no numpad; dedicated PrtSc/ScrLk/Pause; Fn right of Alt Gr).
Same setup as [fedora-gnc](https://github.com/luzikaj/fedora-gnc) (see its `docs/keyboard.md`):

| Where | Layout |
|---|---|
| Desktop (Umbriel, Noctalia, all apps) | `dvorak_r_pl`: right-handed Dvorak + Polish letters (`/etc/xkb/symbols/dvorak_r_pl`) |
| Text console, login screen (greeter) | `dvorak-r` (same keys, no Polish letters: keep passwords plain) |
| keyd (`/etc/keyd/default.conf`) | hold Right Alt = Mod, tap Right Alt + letter = ą ć ę ł ń ó ś ż ź, tap Right Ctrl / Right Shift = sticky |

After the installer, `noctalia-keyboard-firstboot.service` puts Dvorak-R back
on the console and login screen once (the installer writes its own choice).

Keybinds are the fedora-gnc niri binds ported to Umbriel: Mod + one key, never Shift.
Keys are named by what they type on Dvorak-R (QWERTY keycap in brackets):

| Keys | Action |
|---|---|
| e h t d `[G H J K]` | focus ← ↓ ↑ → (↓/↑ continue to the next/previous workspace) |
| o r s u `[T Y U I]` | move column ← / window ↓ / window ↑ / column → |
| n w / v g | workspace ↑ ↓ / send column ↑ ↓ |
| ' `[/]` / . `[R]` / - `[']` / Enter | launcher / window switcher / overview / terminal |
| l m f p / | width presets / narrower / wider / center / tabs |
| y b k j | fullscreen / maximize / floating / focus floating ↔ tiled |
| ; = | stack into left column / unstack to the right |
| [ ] / Backspace | notifications (control center) / clipboard / close |
| arrows | volume + / − / mute / play-pause (F11: audio devices) |
| Ins Del PgUp PgDn Home End | shortcuts / lock / last workspace / settings / other monitor / send there |
| F8 F9 F10 F12, Print | power menu, screenshots (window / area / screen), Print = area without Mod |
| c i a x | Speech Note: dictate / stop / read clipboard / cancel |
| Scroll Lock | pass keys to the focused app (games, VMs) and back |

The default desktop wallpaper is a cheat sheet of this keyboard
(`artwork/make-cheatsheet.py`; after changing binds, edit it and run
`python3 artwork/make-cheatsheet.py system_files/usr/share/backgrounds/fedora-noctalia`).
The plain `noctalia-night-*.jpg` versions are in `/usr/share/backgrounds/fedora-noctalia/`.

App configs in `/etc/skel` come from fedora-gnc: Helix, Ghostty and foot (fish
shell, paste with Ctrl+V), k9s plugins.
