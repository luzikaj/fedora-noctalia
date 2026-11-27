# Create a VirtualBox VM for testing the spin on a Windows host.
# Tuned for: Ryzen 7 3700X (8C/16T), 32 GB RAM, RTX 2080, 1440p@1.5x main monitor.
#
# Usage (PowerShell):
#   .\create-virtualbox-vm.ps1 -Iso D:\ISO\fedora-noctalia.iso
#   .\create-virtualbox-vm.ps1 -Iso ... -BaseFolder G:\VMs -Bridged
param(
    [Parameter(Mandatory)] [string] $Iso,
    [string] $Name       = "fedora-noctalia",
    [string] $BaseFolder = "D:\VMs",     # NOT C: (it is nearly full)
    [int]    $Cpus       = 6,            # 6 of 16 threads; leaves the host responsive
    [int]    $MemoryMB   = 8192,
    [int]    $DiskGB     = 64,           # dynamic VDI, grows as needed
    [switch] $Bridged                    # LAN IP (192.168.2.x) instead of NAT, e.g. for ssh
)

$ErrorActionPreference = "Stop"
$VBox = Join-Path $env:ProgramFiles "Oracle\VirtualBox\VBoxManage.exe"
function vbm { & $VBox @args; if ($LASTEXITCODE) { throw "VBoxManage $($args -join ' ') failed" } }

if (-not (Test-Path $Iso)) { throw "ISO not found: $Iso" }

# Warn if Hyper-V/WSL2/VBS is active: VirtualBox then runs on the slow
# Hyper-V backend (green turtle icon in the VM status bar).
$hv = (bcdedit /enum '{current}' 2>$null | Select-String 'hypervisorlaunchtype') -join ''
if ($hv -match 'Auto') {
    Write-Warning "Hyper-V is enabled: VirtualBox will be slow. To disable it (run as admin, then reboot): bcdedit /set hypervisorlaunchtype off. This turns off WSL2 and Docker Desktop's WSL backend."
}

vbm createvm --name $Name --ostype Fedora_64 --basefolder $BaseFolder --register

vbm modifyvm $Name `
    --firmware efi `
    --cpus $Cpus --memory $MemoryMB `
    --ioapic on --pae on --nested-paging on --paravirt-provider kvm `
    --graphicscontroller vmsvga --vram 128 --accelerate-3d on `
    --rtc-use-utc on `
    --mouse usbtablet --usb-xhci on `
    --audio-driver default --audio-controller hda --audio-enabled on --audio-out on `
    --clipboard-mode bidirectional `
    --boot1 dvd --boot2 disk --boot3 none --boot4 none

if ($Bridged) {
    $nic = (Get-NetAdapter -Physical | Where-Object Status -eq Up | Select-Object -First 1).InterfaceDescription
    vbm modifyvm $Name --nic1 bridged --bridge-adapter1 "$nic" --nic-type1 virtio
} else {
    vbm modifyvm $Name --nic1 nat --nic-type1 virtio
}

$disk = Join-Path $BaseFolder "$Name\$Name.vdi"
vbm createmedium disk --filename $disk --size ($DiskGB * 1024) --format VDI
vbm storagectl $Name --name SATA --add sata --controller IntelAhci --portcount 2 --hostiocache on
vbm storageattach $Name --storagectl SATA --port 0 --device 0 --type hdd --medium $disk --nonrotational on --discard on
vbm storageattach $Name --storagectl SATA --port 1 --device 0 --type dvddrive --medium $Iso

Write-Host "`nCreated $Name in $BaseFolder. Start it with:  & '$VBox' startvm $Name"
