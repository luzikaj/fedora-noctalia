Put your keyd configs (e.g. `default.conf`) here. `scripts/import-my-dotfiles.sh`
copies them from your current machine.

Umbriel's `Mod` is set to Super (`mod_key = "Super"`), so the held Right Alt
layer must emit Meta for the bind keys, exactly as it does for niri today,
while still sending AltGr for the Polish letters.

keyd.service is enabled automatically when the `keyd` package is in the image.
