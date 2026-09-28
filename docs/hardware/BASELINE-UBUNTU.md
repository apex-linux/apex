# Baselines on Ubuntu, before Apex

The roadmap's S0 hardware track measures the laptop on its current Ubuntu install, so
that each Apex slice has a number to compare against. Each section names the date, the
software it ran on and the commands. Values are copied from the commands' output.

## dGPU: RTX 3050 Mobile (GA107M, `10de:25a2`), 2026-09-28

Software: Ubuntu 26.04.1 LTS, kernel 7.0.0-34-generic, GNOME Shell 50.1 on Wayland,
NVIDIA UNIX Open Kernel Module 595.91.07 (licence "Dual MIT/GPL").

| Fact | Value | Command |
|---|---|---|
| Runtime PM | `power/control` is `auto`; `runtime_status` is `suspended`; `power_state` is `D3cold` | `cat /sys/bus/pci/devices/0000:01:00.0/{power/control,power/runtime_status,power_state}` |
| Idle share | suspended 22,406 s of 23,110 s since boot (97.0 %) | `power/runtime_suspended_time` and `power/runtime_active_time` |
| RTD3 | `Runtime D3 status: Enabled (fine-grained)`; `Video Memory: Off` | `cat /proc/driver/nvidia/gpus/*/power` |
| Hardware support | video memory self refresh and video memory off: supported; S0ix platform support: supported, status disabled; Notebook Dynamic Boost: supported | same file |
| Driver parameters | `DynamicPowerManagement: 2`, `DynamicPowerManagementVideoMemoryThreshold: 200`, `PreserveVideoMemoryAllocations: 1`, `EnableS0ixPowerManagement: 0`, `UseKernelSuspendNotifiers: 0` | `grep -E 'DynamicPower\|S0ix\|PreserveVideo\|KernelSuspend' /proc/driver/nvidia/params` |
| System sleep | only `[s2idle]` is offered | `cat /sys/power/mem_sleep` |
| PCI functions | function 0 only; no HDMI audio function | `ls -d /sys/bus/pci/devices/0000:01:00.*` |
| MUX | none exposed: asus-nb-wmi has no `gpu_mux_mode` or `dgpu_disable` | `ls /sys/devices/platform/asus-nb-wmi/` |
| Display GPUs | DRM cards for vendors `0x10de` and `0x1002`; the AMD iGPU drives the panel | `cat /sys/class/drm/card*/device/vendor` |
| Platform profile | `performance` at the time of the reading | `cat /sys/firmware/acpi/platform_profile` |

What it means for ADR 0015:

- Fine-grained RTD3 with the open module works on this machine. The idle target in
  ACCEPTANCE §4 (at least 95 % runtime-suspended) is met today at 97.0 %.
- Ubuntu suspends the GPU through the nvidia-suspend units (`UseKernelSuspendNotifiers:
  0`); Apex plans the kernel suspend notifiers (ADR 0015 §6). The S4 s2idle row compares
  the two.
- S0ix power management is off by default on this driver. The two 30-minute lid-closed
  runs of the S0 hardware track (`NVreg_EnableS0ixPowerManagement=0` and `=1`) are still
  to be done.

## Still to measure in S0 (owner, on Ubuntu)

| Item | Where it goes |
|---|---|
| Speakers: the `model=` alias experiment after a cold boot and after a Windows restart | `docs/hardware/AUDIO.md`, and the winning line for ROADMAP S1d |
| Fingerprint: the elanpress genuine and impostor score test | `docs/hardware/FINGERPRINT.md` §5 |
| s2idle: one 30-minute lid-closed run, drain and `last_hw_sleep` | this file |
| dGPU: the two 30-minute lid-closed runs with `EnableS0ixPowerManagement=0` and `=1` | this file |
