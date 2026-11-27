# Create a VirtualBox VM for testing the spin on a Windows host.
# Tuned for: Ryzen 7 3700X (8C/16T), 32 GB RAM, RTX 2080.
#
# Recommended: boot the ready-made disk from the build-vm-disk workflow
#   .\create-virtualbox-vm.ps1 -Vmdk D:\VMs\disk.vmdk
# Installer ISO instead (creates an empty 64 GB disk):
#   .\create-virtualbox-vm.ps1 -Iso D:\ISO\fedora-noctalia.iso
#
# Graphics: VBoxSVGA without 3D. VMSVGA makes current kernels load the VMware
# driver (vmwgfx), which refuses VirtualBox and can hang the boot. The desktop
# then renders on the CPU: fine for testing, slow for blur/animations.
param(
    [string] $Vmdk,
    [string] $Iso,
    [string] $Name       = "fedora-noctalia",
    [string] $BaseFolder = "D:\VMs",     # NOT C: (it is nearly full)
    [int]    $Cpus       = 6,
    [int]    $MemoryMB   = 8192,
    [int]    $DiskGB     = 64,
    [switch] $Bridged                    # LAN IP (192.168.2.x) instead of NAT, e.g. for ssh
)

$ErrorActionPreference = "Stop"
$VBox = Join-Path $env:ProgramFiles "Oracle\VirtualBox\VBoxManage.exe"
function vbm { & $VBox @args; if ($LASTEXITCODE) { throw "VBoxManage $($args -join ' ') failed" } }

if (-not $Vmdk -and -not $Iso) { throw "Pass -Vmdk <disk.vmdk> or -Iso <installer.iso>" }
foreach ($f in @($Vmdk, $Iso)) { if ($f -and -not (Test-Path $f)) { throw "Not found: $f" } }

$hv = (bcdedit /enum '{current}' 2>$null | Select-String 'hypervisorlaunchtype') -join ''
if ($hv -match 'Auto') {
    Write-Warning "Hyper-V is enabled: VirtualBox will be slow. To disable it (run as admin, then reboot): bcdedit /set hypervisorlaunchtype off. This turns off WSL2 and Docker Desktop's WSL backend."
}

vbm createvm --name $Name --ostype Fedora_64 --basefolder $BaseFolder --register

vbm modifyvm $Name `
    --firmware efi `
    --cpus $Cpus --memory $MemoryMB `
    --ioapic on --pae on --nested-paging on --paravirt-provider kvm `
    --graphicscontroller vboxsvga --vram 128 --accelerate-3d off `
    --rtc-use-utc on `
    --mouse ps2 --keyboard ps2 --usb-xhci on `
    --audio-driver default --audio-controller hda --audio-enabled on --audio-out on `
    --clipboard-mode bidirectional

if ($Bridged) {
    $nic = (Get-NetAdapter -Physical | Where-Object Status -eq Up | Select-Object -First 1).InterfaceDescription
    vbm modifyvm $Name --nic1 bridged --bridge-adapter1 "$nic" --nic-type1 virtio
} else {
    vbm modifyvm $Name --nic1 nat --nic-type1 virtio
}

vbm storagectl $Name --name SATA --add sata --controller IntelAhci --portcount 2 --hostiocache on

if ($Vmdk) {
    # Keep the disk next to the VM, on the same drive
    $vmDir = Join-Path $BaseFolder $Name
    $disk = Join-Path $vmDir "$Name.vmdk"
    Copy-Item $Vmdk $disk
    vbm storageattach $Name --storagectl SATA --port 0 --device 0 --type hdd --medium $disk --nonrotational on --discard on
    vbm modifyvm $Name --boot1 disk --boot2 none --boot3 none --boot4 none
} else {
    $disk = Join-Path $BaseFolder "$Name\$Name.vdi"
    vbm createmedium disk --filename $disk --size ($DiskGB * 1024) --format VDI
    vbm storageattach $Name --storagectl SATA --port 0 --device 0 --type hdd --medium $disk --nonrotational on --discard on
    vbm storageattach $Name --storagectl SATA --port 1 --device 0 --type dvddrive --medium $Iso
    vbm modifyvm $Name --boot1 dvd --boot2 disk --boot3 none --boot4 none
}

Write-Host "`nCreated $Name in $BaseFolder. Start it with:  & '$VBox' startvm $Name"
