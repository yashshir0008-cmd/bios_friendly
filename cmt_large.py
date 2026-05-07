"""
PhoenixBIOS Setup Utility Simulator — Enhanced Edition
Universal Diagnostic Engine + Hardware Monitor + Overclocking + PCI/PCIe
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import platform, psutil, threading, time, json, os, sys, subprocess, math, hashlib, random
from datetime import datetime
from copy import deepcopy

# ── Colour Palette ────────────────────────────────────────────────────────────
PHX_CYAN   = "#00AAAA"
PHX_BLUE   = "#0000AA"
PHX_GREY   = "#C0C0C0"
PHX_WHITE  = "#FFFFFF"
PHX_BLACK  = "#000000"
PHX_YELLOW = "#FFFF55"
PHX_RED    = "#FF5555"
PHX_GREEN  = "#55FF55"
WIN_LOCK_BG = "#005A9E"

FONT_MAIN       = ("Consolas", 12, "bold")
FONT_TITLE      = ("Consolas", 14, "bold")
FONT_SMALL      = ("Consolas", 10)
FONT_SMALL_BOLD = ("Consolas", 10, "bold")
FONT_WIN_CLOCK  = ("Segoe UI", 48, "normal")
FONT_WIN_DATE   = ("Segoe UI", 18, "normal")

CMOS_FILE = os.path.join(os.path.expanduser("~"), ".bios_cmos.json")

# ── Default Settings ──────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    # Main
    "diskette_a": "1.44/1.25 MB 3½\"",
    "diskette_b": "Disabled",
    "diag_screen": "Disabled",
    # Advanced
    "mp_spec": "1.4",
    "installed_os": "Other",
    "reset_config": "No",
    "cache_internal": "Enabled",
    "cache_external": "Enabled",
    "cache_size": "256 KB",
    "com1_port": "3F8h/IRQ4",
    "com2_port": "2F8h/IRQ3",
    "lpt_port": "378h/IRQ7",
    "lpt_mode": "Normal",
    "disk_access_mode": "DOS",
    "local_bus_ide": "Both",
    "usb_legacy": "Enabled",
    "usb_2_support": "Enabled",
    # Security
    "supervisor_pw": "",
    "user_pw": "",
    "pw_on_boot": "Disabled",
    "chassis_intrusion": "Disabled",
    # Boot
    "boot_order": [
        "HDD: Windows Boot Manager",
        "USB: Generic Flash Drive",
        "CD/DVD: Optical Drive",
        "Network: LAN PXE Boot"
    ],
    "boot_num_lock": "On",
    "fast_boot": "Enabled",
    "boot_diagnostic": "Disabled",
    # Power / Advanced
    "boot_mode": "UEFI",
    "secure_boot": "Enabled",
    "tpm_state": "Enabled",
    "virtualization": "Enabled",
    "hyperthreading": "Enabled",
    "sata_mode": "AHCI",
    "ram_freq": "Auto",
    "cpu_fan_ctrl": "Auto",
    "pwr_on_ac": "Disabled",
    "wake_on_lan": "Disabled",
    # Overclocking
    "cpu_multiplier": "Auto",
    "cpu_base_clock": "100 MHz",
    "cpu_voltage": "Auto",
    "ram_xmp": "Disabled",
    "ram_voltage": "Auto",
    "ram_timings": "Auto",
    "cpu_power_limit": "Auto",
    "spread_spectrum": "Enabled",
    # PCI / Onboard
    "onboard_audio": "Enabled",
    "onboard_lan": "Enabled",
    "onboard_lan2": "Disabled",
    "pcie_x16_slot": "Auto",
    "pcie_x1_slot1": "Enabled",
    "pcie_x1_slot2": "Enabled",
    "igpu": "Auto",
    "igpu_memory": "64 MB",
    "pci_latency": "32",
    "above_4g_decoding": "Disabled",
    "resizable_bar": "Disabled",
    # Flash Update
    "bios_flashed": False,
}

# ── Universal Setting Metadata ────────────────────────────────────────────────
# Each key maps to: display_name, category, risk, short_effect, long_consequence
# risk: "safe" | "caution" | "danger" | "info"
SETTING_META = {
    "boot_mode": {
        "name": "Boot Mode",
        "category": "Firmware",
        "risk_if_nondefault": "caution",
        "default": "UEFI",
        "effects": {
            "UEFI": ("safe", "Modern boot firmware.",
                "UEFI (Unified Extensible Firmware Interface) is the modern replacement for legacy BIOS. "
                "It supports GPT partition tables (up to 9.4 ZB disks), Secure Boot, fast boot, large drives over 2 TB, "
                "and 64-bit pre-boot environment. Windows 10/11, modern Linux, and macOS all require or strongly prefer UEFI. "
                "On a real PC, switching from Legacy to UEFI on an existing Windows installation will cause it to fail to boot "
                "unless the disk is already GPT-formatted and Windows was originally installed in UEFI mode."),
            "Legacy": ("caution", "Old BIOS-compatibility mode.",
                "Legacy (CSM) mode emulates the original IBM PC BIOS environment. It uses MBR partition tables which "
                "are limited to 4 primary partitions and 2 TB maximum disk size. Secure Boot is unavailable in Legacy mode. "
                "Windows 11 CANNOT be installed or run in Legacy mode — it will refuse installation. Windows 10 can use Legacy "
                "but Microsoft encourages UEFI. On a real PC, this mode is used when running very old operating systems "
                "(DOS, Windows XP, older Linux) or when the hard drive uses an MBR partition scheme. Switching an existing "
                "UEFI-installed OS to Legacy without converting the disk will result in a boot failure (BSOD or 'No boot device')."),
        }
    },
    "secure_boot": {
        "name": "Secure Boot",
        "category": "Security",
        "risk_if_nondefault": "caution",
        "default": "Enabled",
        "effects": {
            "Enabled": ("safe", "Blocks unsigned bootloaders.",
                "Secure Boot is a UEFI security feature that validates every piece of software during the boot process "
                "against a database of trusted digital signatures. Only signed bootloaders (Microsoft, Canonical, Red Hat etc.) "
                "can execute. This prevents rootkits, bootkits, and malicious code from loading before the OS. "
                "Windows 11 mandates Secure Boot. Most mainstream Linux distributions (Ubuntu, Fedora, Debian) are now "
                "Secure Boot compatible. However, custom/unsigned kernels, some older Linux distros, FreeBSD without shim, "
                "and bootable USB tools like Ventoy or some Kali builds may fail to boot. On a real PC, enabling Secure Boot "
                "after the fact usually requires no changes if Windows is already installed."),
            "Disabled": ("caution", "Allows unsigned bootloaders — required for some Linux/custom OS.",
                "Disabling Secure Boot allows any bootloader to execute, whether signed or not. This is required for "
                "running unsigned Linux kernels, some live USB environments, older operating systems, and custom OS projects. "
                "It also enables Hackintosh builds and running FreeBSD more easily. The security risk on a real PC is real: "
                "with Secure Boot disabled, a sophisticated attacker who gains physical access could install a bootkit — "
                "malware that loads before the OS and is invisible to antivirus. Windows 11 will refuse to install and may "
                "warn at every boot if Secure Boot is disabled. Windows 10 will still function but shows a watermark warning."),
        }
    },
    "tpm_state": {
        "name": "TPM State",
        "category": "Security",
        "risk_if_nondefault": "caution",
        "default": "Enabled",
        "effects": {
            "Enabled": ("safe", "Trusted Platform Module active.",
                "TPM (Trusted Platform Module) is a dedicated hardware security chip that stores cryptographic keys, "
                "certificates, and measurements of the boot process. It is used by Windows BitLocker (full-disk encryption), "
                "Windows Hello (biometric/PIN authentication), and many enterprise security solutions. Windows 11 requires "
                "TPM 2.0 as a hard requirement — it will not install without it. On a real PC, modern motherboards implement "
                "TPM as firmware (fTPM) built into the CPU, or as a discrete TPM chip. Enabling it costs no performance."),
            "Disabled": ("danger", "Breaks Win11, BitLocker, Windows Hello.",
                "Disabling TPM means the system has no hardware security anchor. The immediate real-world consequences: "
                "(1) Windows 11 will refuse to install — the installer checks for TPM 2.0 and halts. "
                "(2) Any existing BitLocker-encrypted drives will trigger recovery key prompts on every boot. "
                "(3) Windows Hello biometric/PIN login will stop working. "
                "(4) Enterprise MDM solutions (Intune, SCCM) may flag the device as non-compliant and revoke access. "
                "On a real PC, disabling TPM when BitLocker is already active is particularly dangerous — "
                "if you don't have the 48-digit recovery key, you permanently lose access to the encrypted data."),
        }
    },
    "virtualization": {
        "name": "CPU Virtualization (VT-x/AMD-V)",
        "category": "CPU",
        "risk_if_nondefault": "caution",
        "default": "Enabled",
        "effects": {
            "Enabled": ("safe", "Hardware VM acceleration active.",
                "CPU Virtualization (Intel VT-x or AMD-V) allows the processor to create isolated virtual machines "
                "with near-native performance. This is required for: VirtualBox, VMware Workstation/Player, Hyper-V (Windows), "
                "WSL2 (Windows Subsystem for Linux 2), Docker Desktop on Windows, Android Emulator (for app developers), "
                "and all modern hypervisors. With it enabled, a VM running Windows 11 inside Windows 10 runs at roughly "
                "80-90% of native CPU speed. Without it, software emulation is required which is 10-50x slower."),
            "Disabled": ("danger", "Breaks VMs, WSL2, Docker Desktop, Android emulator.",
                "Disabling CPU Virtualization on a real PC immediately breaks several important workflows: "
                "(1) VirtualBox and VMware will refuse to start 64-bit VMs, showing errors like 'VT-x is not available (VERR_VMX_NO_VMX)'. "
                "(2) Hyper-V becomes non-functional, which also breaks WSL2 — 'wsl' commands will fail with feature-not-available errors. "
                "(3) Docker Desktop on Windows requires Hyper-V or WSL2, so Docker stops working entirely. "
                "(4) Android Studio's emulator (AVD) will crash or refuse to start. "
                "This setting has zero negative performance impact when enabled — there is no reason to disable it "
                "on a modern PC unless troubleshooting a very specific hardware compatibility issue."),
        }
    },
    "hyperthreading": {
        "name": "Hyper-Threading / SMT",
        "category": "CPU",
        "risk_if_nondefault": "caution",
        "default": "Enabled",
        "effects": {
            "Enabled": ("safe", "Doubles visible logical cores.",
                "Hyper-Threading (Intel) / SMT (AMD) allows each physical CPU core to execute two instruction threads "
                "simultaneously by sharing execution units. A 4-core CPU appears as 8 logical cores to the OS. "
                "This improves multi-threaded workloads: web servers, video encoding, compilation, and most productivity apps "
                "see 20-40% throughput gains. The OS scheduler automatically manages the extra threads. "
                "Modern applications are designed to exploit this. There is no downside for typical use."),
            "Disabled": ("caution", "Halves logical core count, impacts multi-threaded performance.",
                "Disabling Hyper-Threading on a real PC halves the number of logical processors visible to the OS. "
                "A 4-core/8-thread CPU becomes a 4-core/4-thread CPU. Real-world performance impacts: "
                "video encoding in Handbrake/DaVinci Resolve: 25-35% slower; software compilation: 20-30% slower; "
                "running multiple VMs simultaneously: noticeably degraded. "
                "Some security researchers recommend disabling HT to mitigate CPU side-channel attacks like "
                "MDS (Microarchitectural Data Sampling) and Spectre/Meltdown variants — but for a student lab PC, "
                "this tradeoff is not worth it. The only legitimate reason to disable it today is in very specific "
                "real-time audio workloads where thread scheduling latency is critical."),
        }
    },
    "sata_mode": {
        "name": "SATA Controller Mode",
        "category": "Storage",
        "risk_if_nondefault": "danger",
        "default": "AHCI",
        "effects": {
            "AHCI": ("safe", "Modern SATA mode — supports TRIM, NCQ, hot-swap.",
                "AHCI (Advanced Host Controller Interface) is the standard SATA mode for modern drives. It enables: "
                "Native Command Queuing (NCQ) which lets the drive reorder requests for optimal seek paths; "
                "TRIM support for SSDs (essential for SSD longevity and performance); "
                "hot-plug capability for eSATA; and SMART data reporting. "
                "All modern SSDs and HDDs perform significantly better in AHCI than IDE mode. "
                "AHCI is required for NVMe M.2 drives in some BIOS implementations."),
            "IDE": ("danger", "Legacy compatibility mode — degrades SSD performance severely.",
                "Switching to IDE (also called 'Legacy' or 'Compatible') mode on a real PC with a modern SSD is one of "
                "the most damaging BIOS changes you can make to storage performance. The consequences: "
                "(1) TRIM is disabled — an SSD in IDE mode cannot tell the controller which blocks are free, "
                "so over weeks/months it fills with stale data and write performance degrades by 50-80%. "
                "(2) NCQ is disabled — the drive processes one command at a time instead of reordering an optimal queue. "
                "(3) If Windows was installed in AHCI mode and you switch to IDE, Windows will BSOD with INACCESSIBLE_BOOT_DEVICE "
                "because the AHCI driver is no longer being loaded. To switch safely, you must first enable AHCI driver loading "
                "in the registry (HKLM\\SYSTEM\\CurrentControlSet\\Services\\storahci — set Start to 0) before changing this setting. "
                "This mode only exists for compatibility with very old drives and operating systems (Windows XP era)."),
            "RAID": ("caution", "Hardware RAID — requires matching drives and setup.",
                "RAID mode enables the motherboard's onboard RAID controller, allowing multiple physical drives to be "
                "combined into a RAID array (RAID 0 for speed, RAID 1 for mirroring, RAID 5/10 for both). "
                "On a real PC, switching to RAID mode when drives were configured as individual AHCI disks will make "
                "Windows fail to boot — the RAID driver is different from the AHCI driver. "
                "Additionally, Intel RST (Rapid Storage Technology) or AMD RAID must be configured through a separate "
                "ROM utility during POST, and appropriate drivers must be injected into the Windows installation. "
                "RAID 0 (striping) doubles throughput but if either drive fails, ALL data is lost. "
                "RAID 1 (mirroring) provides redundancy — useful for servers, not typically home PCs."),
        }
    },
    "ram_freq": {
        "name": "Memory Frequency",
        "category": "Memory",
        "risk_if_nondefault": "caution",
        "default": "Auto",
        "effects": {
            "Auto": ("safe", "Uses SPD default (JEDEC standard speed).",
                "Auto mode reads the SPD (Serial Presence Detect) chip on each RAM stick and configures the memory "
                "controller to run at the JEDEC-certified default speed. This is always safe and stable. "
                "For DDR4, the JEDEC default is typically 2133-2400 MHz regardless of what the stick is rated for."),
            "1600 MHz": ("safe", "Conservative DDR3/DDR4 base speed.",
                "Running RAM at 1600 MHz is well within spec for DDR3 and conservative for DDR4. "
                "Fully stable on all platforms. DDR4 RAM rated for 3200 MHz running at 1600 MHz wastes its potential "
                "but guarantees stability. Useful for troubleshooting suspected RAM issues."),
            "2133 MHz": ("safe", "DDR4 JEDEC standard baseline.",
                "2133 MHz is the DDR4 JEDEC standard — all DDR4 RAM is certified to run at this speed. Fully safe."),
            "2400 MHz": ("safe", "Mild DDR4 overclock or rated speed.",
                "2400 MHz is within official DDR4 JEDEC specifications and supported by all modern Intel/AMD platforms without XMP. Safe and stable."),
            "2666 MHz": ("safe", "Common DDR4 XMP profile speed.",
                "2666 MHz typically requires XMP (Intel) or DOCP (AMD) to activate. Widely supported on Z-series Intel "
                "and X570/B550 AMD boards. Very stable for DDR4."),
            "3200 MHz": ("caution", "Requires XMP/DOCP — mild overclock.",
                "3200 MHz requires XMP Profile 1 on most DDR4 kits. On a real PC, this requires a motherboard that "
                "supports XMP (Z-series Intel or B/X AMD) and RAM rated for 3200. If the board or CPU's IMC (Integrated "
                "Memory Controller) doesn't support this speed stably, you'll see random BSODs (usually WHEA_UNCORRECTABLE_ERROR) "
                "or the system won't POST and will reset to default speed automatically."),
            "3600 MHz": ("caution", "High-performance DDR4 — may require tuning.",
                "3600 MHz is the 'sweet spot' for Ryzen AMD systems (matches the Infinity Fabric clock at 1800 MHz). "
                "Requires a quality motherboard, matched RAM kit (ideally same die/same manufacturer), and good CPU IMC. "
                "On cheaper boards or with mixed RAM sticks, 3600 may be unstable. System may reset to 2133 on failed boot."),
            "4800 MHz": ("danger", "Extreme DDR5 speed — instability risk.",
                "4800 MHz is DDR5 territory. Running DDR4 at 4800 MHz is effectively an extreme overclock that "
                "most systems cannot sustain. On a real PC, attempting this without a validated DDR5 platform will "
                "likely result in: failure to POST (system beeps and resets), RAM running at fallback 2133 MHz, "
                "or in rare cases, data corruption. DDR5 systems (Intel 12th gen+, AMD Ryzen 7000) natively support "
                "4800 MHz as the JEDEC base, but older DDR4 boards will be completely unstable."),
        }
    },
    "ram_xmp": {
        "name": "XMP / DOCP Profile",
        "category": "Memory",
        "risk_if_nondefault": "caution",
        "default": "Disabled",
        "effects": {
            "Disabled": ("safe", "RAM runs at JEDEC default speed.",
                "With XMP disabled, RAM runs at its JEDEC default (usually 2133-2400 MHz for DDR4) regardless of "
                "the advertised speed on the box. RAM sold as '3200 MHz' actually only guarantees the JEDEC default "
                "until XMP is enabled. No risk, but you're not getting the performance you paid for."),
            "Profile 1": ("caution", "Activates manufacturer-rated overclock.",
                "XMP (Extreme Memory Profile) Profile 1 applies the manufacturer's tested overclock — the speed, "
                "timings, and voltage advertised on the RAM kit packaging. On a real PC, this is generally safe if "
                "your motherboard and CPU support it, but it IS technically an overclock. The memory controller is "
                "running faster than Intel/AMD certify. Most modern Z/B/X series boards handle this fine. "
                "If unstable: system won't POST, beeps, and reverts. No permanent damage occurs."),
            "Profile 2": ("caution", "Activates secondary (usually faster) XMP profile.",
                "XMP Profile 2 is a secondary profile — some kits include a more aggressive second profile "
                "with higher speeds or tighter timings. Stability depends heavily on the specific CPU's IMC quality. "
                "If the system fails to boot, it will automatically revert to default. No hardware damage risk."),
        }
    },
    "cpu_multiplier": {
        "name": "CPU Multiplier",
        "category": "Overclocking",
        "risk_if_nondefault": "danger",
        "default": "Auto",
        "effects": {
            "Auto": ("safe", "Intel/AMD manages clock speed automatically.",
                "Auto allows the CPU to use its built-in power management (Intel Turbo Boost / AMD Precision Boost) "
                "to dynamically adjust the multiplier based on workload and thermal conditions. This is the optimal "
                "setting for nearly all use cases. No risk whatsoever."),
        },
        "_dynamic_note": ("danger",
            "Manually setting the CPU multiplier overclocks or underclocks the processor. On a real PC: "
            "going ABOVE the rated turbo boost speed risks system instability (BSODs, freezes), accelerated CPU degradation "
            "through electromigration, and potentially voided warranty. Intel locks multiplier changes to 'K' suffix CPUs "
            "(e.g., Core i7-13700K) and requires a Z-series motherboard — on non-K CPUs the BIOS option simply doesn't work. "
            "AMD allows multiplier changes on Ryzen CPUs with X570/B550/X670 boards. "
            "Going too high without adequate cooling causes thermal throttling (the CPU slows down to protect itself) "
            "or a hard thermal shutdown. Going below the base clock (underclocking) reduces performance but is safe and "
            "can reduce heat — useful for small form-factor builds with limited cooling.")
    },
    "cpu_voltage": {
        "name": "CPU Core Voltage (Vcore)",
        "category": "Overclocking",
        "risk_if_nondefault": "danger",
        "default": "Auto",
        "effects": {
            "Auto": ("safe", "CPU self-regulates voltage via VRM.",
                "Auto voltage lets the CPU's built-in power management and motherboard VRM (Voltage Regulator Module) "
                "dynamically adjust core voltage based on load and temperature. Completely safe and the recommended setting."),
        },
        "_dynamic_note": ("danger",
            "Manually increasing CPU voltage is the single most damaging BIOS change you can make on a real PC. "
            "Modern CPUs (Intel 12th/13th gen, AMD Ryzen 5000/7000) operate at 1.0–1.4V under load. "
            "Exceeding safe limits causes: (1) Drastically increased heat — each 0.1V adds ~10-15W of heat. "
            "(2) Accelerated electromigration — atoms literally migrate in the CPU traces, causing permanent degradation "
            "over months/years. (3) Immediate instability at very high voltages — BSODs, lockups. "
            "(4) Instantaneous damage at extreme voltages (>1.55V for Ryzen, >1.52V for Intel Alder/Raptor Lake). "
            "Intel's own guidance: never exceed 1.52V on 12th/13th gen under sustained load. "
            "Lowering voltage (undervolting) is generally safe and actually recommended — it reduces heat and can "
            "improve performance in thermally-limited laptops by allowing higher sustained boost clocks.")
    },
    "onboard_audio": {
        "name": "Onboard HD Audio",
        "category": "PCI/Onboard",
        "risk_if_nondefault": "safe",
        "default": "Enabled",
        "effects": {
            "Enabled": ("safe", "Integrated audio controller active.",
                "The integrated Realtek/ALC audio codec is enabled. Provides 3.5mm audio jacks on the rear I/O panel "
                "and front panel audio header. Uses minimal system resources. Recommended unless you have a dedicated sound card."),
            "Disabled": ("safe", "Integrated audio off — no rear audio jacks.",
                "Disabling onboard audio frees up a PCIe/PCI interrupt and can marginally reduce system noise floor for "
                "audiophiles using a dedicated sound card. On a real PC: once disabled, all rear audio jacks stop working "
                "immediately, and Windows will show the audio device as missing. The front panel audio header also becomes "
                "non-functional. If you have a USB DAC or dedicated PCIe sound card, you can safely disable this. "
                "Re-enabling it requires a reboot for the OS to re-detect and re-install the driver."),
        }
    },
    "onboard_lan": {
        "name": "Onboard LAN (Ethernet)",
        "category": "PCI/Onboard",
        "risk_if_nondefault": "caution",
        "default": "Enabled",
        "effects": {
            "Enabled": ("safe", "Integrated Gigabit Ethernet active.",
                "Onboard LAN provides the RJ45 Ethernet port on the rear I/O. Typically Intel i219V or Realtek 8125 "
                "on modern boards. Provides 1 Gbps or 2.5 Gbps wired network connectivity. Essential for most systems."),
            "Disabled": ("caution", "Rear ethernet port disabled.",
                "Disabling onboard LAN on a real PC immediately cuts wired network connectivity. The RJ45 port stops "
                "working. Only do this if: (a) you're using a dedicated PCIe NIC and want to avoid driver conflicts, "
                "(b) you're using only Wi-Fi and want to reduce attack surface, or (c) you're building a dedicated "
                "storage/media server with a PCIe 10GbE card. Wake-on-LAN functionality is also lost. "
                "On a domain-joined enterprise PC, losing the NIC unexpectedly can prevent login if cached credentials expire."),
        }
    },
    "igpu": {
        "name": "Integrated Graphics (iGPU)",
        "category": "PCI/Onboard",
        "risk_if_nondefault": "caution",
        "default": "Auto",
        "effects": {
            "Auto": ("safe", "iGPU active only if no discrete GPU present.",
                "Auto mode activates the CPU's integrated graphics only when no discrete GPU is detected in the PCIe x16 slot. "
                "When a discrete GPU is present, the iGPU is powered off to save resources. Best setting for most users."),
            "Enabled": ("safe", "iGPU always active — enables multi-monitor with dGPU.",
                "Forcing iGPU on alongside a discrete GPU enables additional display outputs from the motherboard's "
                "video ports (HDMI/DisplayPort on the I/O shield). Useful for 3+ monitor setups or when using "
                "Intel Quick Sync Video for hardware-accelerated encoding while the dGPU handles gaming. "
                "Uses a small amount of shared system RAM for the frame buffer."),
            "Disabled": ("caution", "iGPU completely off — rear video ports dead.",
                "Disabling the iGPU forces all video output through the discrete GPU. On a real PC, this means "
                "the HDMI/DisplayPort ports on the motherboard's rear I/O produce NO signal. "
                "Critical scenario: if your discrete GPU fails, you will have NO video output whatsoever — "
                "you'd need to either re-enable iGPU (blind BIOS navigation) or install another GPU to see anything. "
                "Also breaks Intel Quick Sync hardware encoding features."),
        }
    },
    "above_4g_decoding": {
        "name": "Above 4G Decoding",
        "category": "PCI/Onboard",
        "risk_if_nondefault": "caution",
        "default": "Disabled",
        "effects": {
            "Disabled": ("safe", "Standard PCIe address space below 4 GB.",
                "Standard PCIe BAR (Base Address Register) mapping below 4 GB. Compatible with all devices and OSes. "
                "Sufficient for most configurations. Recommended unless you have specific high-VRAM or multi-GPU needs."),
            "Enabled": ("caution", "Maps PCIe BARs above 4 GB — needed for large VRAM cards.",
                "Above 4G Decoding allows PCIe devices to map their memory-mapped I/O regions above the 4 GB address boundary. "
                "This is REQUIRED for: (1) GPUs with 8 GB+ VRAM (RTX 3080/4090, RX 6800 XT etc.) to expose their full "
                "memory space. (2) Multi-GPU setups where combined BAR space exceeds 4 GB. (3) Enabling Resizable BAR / "
                "Smart Access Memory for performance gains. On a real PC, enabling this on a system running 32-bit OS "
                "will cause compatibility issues. It requires a 64-bit OS. Some older OSes and BIOSes have bugs with "
                "this enabled. Recommended ON for any modern gaming PC with a high-end GPU."),
        }
    },
    "resizable_bar": {
        "name": "Resizable BAR (Smart Access Memory)",
        "category": "PCI/Onboard",
        "risk_if_nondefault": "safe",
        "default": "Disabled",
        "effects": {
            "Disabled": ("safe", "CPU accesses GPU VRAM in 256 MB chunks.",
                "Standard PCIe BAR access mode. CPU can only access 256 MB of GPU VRAM at a time, requiring multiple "
                "transactions to transfer large assets. Works with all hardware and drivers."),
            "Enabled": ("safe", "CPU can access full GPU VRAM — gaming performance boost.",
                "Resizable BAR (Intel) / Smart Access Memory (AMD) allows the CPU to access the GPU's entire VRAM "
                "in a single operation instead of 256 MB windows. This reduces CPU-GPU data transfer overhead. "
                "On a real PC with a modern GPU and updated drivers, this provides 2-15% performance gains in "
                "games like Forza Horizon 5, Hitman 3, and shader-heavy titles. Requires: Above 4G Decoding enabled, "
                "a supported CPU (Intel 10th gen+ or Ryzen 3000+), a supported GPU (RTX 3000+, RX 6000+), "
                "and an updated BIOS and GPU driver. Has no negative effects if all requirements are met."),
        }
    },
    "wake_on_lan": {
        "name": "Wake On LAN",
        "category": "Power",
        "risk_if_nondefault": "caution",
        "default": "Disabled",
        "effects": {
            "Disabled": ("safe", "Network cannot wake the system.",
                "The network card is powered off in S4/S5 sleep states. System can only be woken by power button or "
                "scheduled wake timers. Slightly lower idle power draw."),
            "Enabled": ("caution", "Network card remains powered in sleep — can be woken by magic packet.",
                "Wake-on-LAN keeps the network card partially powered even when the PC is off or sleeping. "
                "A 'magic packet' (a specific broadcast containing the MAC address) sent from another device on the "
                "network will power on the PC. Useful for: IT admins managing remote PCs, home server wake-on-demand, "
                "gaming PCs that should be accessible for remote desktop. "
                "Security consideration on a real PC: if your router is compromised or you're on an untrusted network, "
                "WoL can be abused to wake your PC without your consent. Also adds ~1-3W of standby power draw. "
                "The feature only works on the same local network by default — remote WoL over the internet requires "
                "router port forwarding configuration."),
        }
    },
    "pw_on_boot": {
        "name": "Password On Boot",
        "category": "Security",
        "risk_if_nondefault": "caution",
        "default": "Disabled",
        "effects": {
            "Disabled": ("safe", "No password prompt at boot.",
                "System boots directly to the OS or login screen without a BIOS-level password challenge. Standard setting."),
            "Enabled": ("caution", "BIOS password required before OS loads.",
                "With Password on Boot enabled and a User Password set, the BIOS displays a password prompt before "
                "the operating system begins loading. This is a pre-boot authentication layer separate from Windows login. "
                "On a real PC, this provides a layer of physical security: someone who steals your laptop cannot even "
                "begin loading the OS without the password. However: this password is stored in CMOS and can be bypassed "
                "on desktop PCs by removing the CMOS battery (which clears all BIOS settings). On laptops, modern BIOS "
                "passwords are stored in flash and cannot be cleared by the battery trick — they require manufacturer tools. "
                "If you forget this password on a laptop, it typically requires a motherboard replacement or paid vendor reset."),
        }
    },
    "fast_boot": {
        "name": "Fast Boot",
        "category": "Boot",
        "risk_if_nondefault": "safe",
        "default": "Enabled",
        "effects": {
            "Enabled": ("safe", "Skips some POST checks for faster boot.",
                "Fast Boot skips non-essential POST initialization steps: USB device enumeration, optical drive detection, "
                "and some memory tests. Reduces boot time by 1-4 seconds. Safe for daily use. "
                "Note: with Fast Boot enabled, you may need to be quick with F2/Del to enter BIOS setup, "
                "and some USB devices (keyboards in particular) may not be recognized during POST."),
            "Disabled": ("safe", "Full POST — better for troubleshooting.",
                "Full POST initialization — all devices are detected and initialized before booting. "
                "Adds 2-5 seconds to boot time but is recommended when troubleshooting hardware issues, "
                "when adding new hardware, or when a USB device isn't being recognized at boot."),
        }
    },
    "cpu_fan_ctrl": {
        "name": "CPU Fan Control",
        "category": "Cooling",
        "risk_if_nondefault": "danger",
        "default": "Auto",
        "effects": {
            "Auto": ("safe", "Fan speed auto-adjusts with temperature.",
                "The BIOS automatically manages fan speed using the CPU temperature sensor via a thermal curve. "
                "At idle (~30-40°C), the fan runs slowly and quietly. Under load (~70-90°C), it ramps up for cooling. "
                "This is the optimal balance of noise and cooling for all workloads."),
            "Full Speed": ("safe", "Fan always at 100% — maximum cooling, loud.",
                "Forces the CPU fan to run at full RPM constantly regardless of temperature. "
                "On a real PC: maximum thermal headroom for overclocking or hot environments. "
                "Very loud — typically 40-50 dB for most air coolers. Fan bearings wear faster due to constant full-speed operation. "
                "No thermal damage risk — this is the safest option for the CPU itself."),
            "Silent": ("danger", "Fans run slowly — CPU may overheat under load.",
                "Silent mode runs fans at minimum speed to prioritize quiet operation. "
                "On a real PC under sustained CPU load: temperatures can reach 90-100°C+ on air-cooled systems. "
                "Modern CPUs throttle (reduce speed) at ~95-100°C to prevent damage — you'll see performance drops "
                "during rendering, compilation, or gaming. On laptops or small form factor PCs with limited airflow, "
                "this can push temperatures to dangerous levels. Only safe for light workloads (web browsing, office tasks) "
                "in a well-ventilated case with an adequately sized cooler."),
            "Manual": ("caution", "Fixed percentage — user-defined curve.",
                "Manual mode sets a fixed fan speed percentage. Requires understanding of your system's thermal profile. "
                "Setting too low risks thermal throttling; too high is unnecessarily loud. Intermediate option for "
                "users who want a consistent noise level and have verified their temperatures are acceptable."),
        }
    },
}

# ── Compatibility Rules (cross-setting validation) ────────────────────────────
COMPAT_RULES = [
    {
        "id": "win11_uefi",
        "check": lambda s: s["boot_mode"] == "UEFI",
        "label": "Windows 11: UEFI Boot Mode",
        "pass_msg": "UEFI mode is active — required for Windows 11.",
        "fail_msg": "Windows 11 requires UEFI Boot Mode. Legacy mode will prevent installation.",
        "severity": "fail",
    },
    {
        "id": "win11_secureboot",
        "check": lambda s: s["secure_boot"] == "Enabled",
        "label": "Windows 11: Secure Boot",
        "pass_msg": "Secure Boot enabled — required for Windows 11.",
        "fail_msg": "Windows 11 requires Secure Boot. It will refuse to install without it.",
        "severity": "fail",
    },
    {
        "id": "win11_tpm",
        "check": lambda s: s["tpm_state"] == "Enabled",
        "label": "Windows 11: TPM 2.0",
        "pass_msg": "TPM enabled — required for Windows 11.",
        "fail_msg": "Windows 11 requires TPM 2.0. Disabled TPM blocks installation.",
        "severity": "fail",
    },
    {
        "id": "secureboot_needs_uefi",
        "check": lambda s: not (s["secure_boot"] == "Enabled" and s["boot_mode"] == "Legacy"),
        "label": "Secure Boot / UEFI conflict",
        "pass_msg": "No Secure Boot / Boot Mode conflict.",
        "fail_msg": "Secure Boot is Enabled but Boot Mode is Legacy — this is a conflict. Secure Boot only works in UEFI mode.",
        "severity": "fail",
    },
    {
        "id": "vm_support",
        "check": lambda s: s["virtualization"] == "Enabled",
        "label": "VM / WSL2 / Docker support",
        "pass_msg": "Virtualization enabled — VMs, WSL2, Docker Desktop will work.",
        "fail_msg": "Virtualization disabled — VMs (VirtualBox, VMware, Hyper-V), WSL2, and Docker Desktop will not function.",
        "severity": "warn",
    },
    {
        "id": "bitlocker",
        "check": lambda s: s["tpm_state"] == "Enabled" and s["secure_boot"] == "Enabled",
        "label": "BitLocker full compatibility",
        "pass_msg": "TPM + Secure Boot both enabled — BitLocker will work without recovery key prompts.",
        "fail_msg": "TPM or Secure Boot is disabled — BitLocker may demand recovery key on every boot.",
        "severity": "warn",
    },
    {
        "id": "ssd_health",
        "check": lambda s: s["sata_mode"] == "AHCI",
        "label": "SSD health (TRIM support)",
        "pass_msg": "AHCI mode — TRIM is active, SSD health maintained.",
        "fail_msg": "SATA in IDE mode — TRIM is disabled. SSD performance will degrade over time. AHCI is strongly recommended.",
        "severity": "warn",
    },
    {
        "id": "pwr_boot_pw",
        "check": lambda s: not (s["pw_on_boot"] == "Enabled" and not s["user_pw"]),
        "label": "Boot password configuration",
        "pass_msg": "Boot password configuration is consistent.",
        "fail_msg": "Password-on-Boot is Enabled but no User Password is set — the prompt will appear but cannot be satisfied.",
        "severity": "warn",
    },
    {
        "id": "rebar_needs_above4g",
        "check": lambda s: not (s["resizable_bar"] == "Enabled" and s["above_4g_decoding"] == "Disabled"),
        "label": "Resizable BAR dependency",
        "pass_msg": "Resizable BAR configuration is valid.",
        "fail_msg": "Resizable BAR is Enabled but Above 4G Decoding is Disabled — Resizable BAR requires Above 4G Decoding to function.",
        "severity": "warn",
    },
    {
        "id": "oc_cooling",
        "check": lambda s: not (s["cpu_multiplier"] != "Auto" and s["cpu_fan_ctrl"] == "Silent"),
        "label": "Overclocking + cooling config",
        "pass_msg": "Fan control is appropriate for your clock settings.",
        "fail_msg": "CPU is overclocked (manual multiplier) but fan is in Silent mode — serious overheating risk. Use Auto or Full Speed fan control when overclocking.",
        "severity": "fail",
    },
    {
        "id": "voltage_risk",
        "check": lambda s: s["cpu_voltage"] == "Auto",
        "label": "CPU voltage safety",
        "pass_msg": "CPU voltage on Auto — safe VRM management.",
        "fail_msg": "CPU voltage is manually set. Excessive voltage causes permanent CPU degradation and heat. Ensure you understand safe voltage limits for your specific CPU.",
        "severity": "warn",
    },
]


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest() if text else ""


# ── Simulated Hardware Monitor Data ──────────────────────────────────────────
def get_simulated_hw_data(settings):
    """Return plausible simulated hardware values based on settings."""
    random.seed(int(time.time()) // 5)  # changes every 5 seconds
    base_cpu_temp = 38
    if settings.get("cpu_fan_ctrl") == "Silent":
        base_cpu_temp += 22
    elif settings.get("cpu_fan_ctrl") == "Full Speed":
        base_cpu_temp -= 8
    if settings.get("cpu_multiplier") not in ("Auto", None):
        base_cpu_temp += 15
    cpu_temp = base_cpu_temp + random.randint(-3, 3)

    fan_rpm_base = {"Auto": 1200, "Full Speed": 2400, "Silent": 450, "Manual": 900}
    fan_rpm = fan_rpm_base.get(settings.get("cpu_fan_ctrl", "Auto"), 1200) + random.randint(-80, 80)

    vcore_base = 1.18 if settings.get("cpu_voltage") == "Auto" else 1.35
    vcore = round(vcore_base + random.uniform(-0.015, 0.015), 3)

    return {
        "cpu_temp": cpu_temp,
        "mb_temp": 32 + random.randint(-2, 2),
        "cpu_fan_rpm": fan_rpm,
        "sys_fan_rpm": 950 + random.randint(-50, 50),
        "vcore": vcore,
        "v3_3": round(3.30 + random.uniform(-0.02, 0.02), 3),
        "v5": round(5.00 + random.uniform(-0.05, 0.05), 3),
        "v12": round(12.0 + random.uniform(-0.15, 0.15), 3),
        "dram_v": round(1.35 + random.uniform(-0.01, 0.01), 3),
    }


# ═══════════════════════════════════════════════════════════════════════════════
class BiosApp:

    def __init__(self, root):
        self.root = root
        self.root.title("PhoenixBIOS Setup Utility Simulator — Enhanced Edition")
        self.root.geometry("1100x800")
        self.root.resizable(False, False)
        self.root.configure(bg=PHX_BLACK)

        for seq, cb in [
            ('<F2>', self.on_bios_key), ('<Delete>', self.on_bios_key),
            ('<F9>', self.load_defaults), ('<F10>', self.global_save_exit),
            ('<Escape>', self.global_exit),
            ('<Up>', self.nav_up), ('<Down>', self.nav_down),
            ('<Left>', self.nav_left), ('<Right>', self.nav_right),
            ('<Return>', self.nav_enter),
            ('<plus>', self.nav_plus), ('<KP_Add>', self.nav_plus),
            ('<minus>', self.nav_minus), ('<KP_Subtract>', self.nav_minus),
            ('<Tab>', self.nav_tab), ('<Prior>', self.nav_pgup),
            ('<Next>', self.nav_pgdn),
        ]:
            self.root.bind(seq, cb)

        self.tabs = ["Main", "Advanced", "Security", "Boot", "Power",
                     "Overclock", "PCI/Onboard", "Monitor", "Update", "Exit", "Lab"]
        self.current_tab_index = 0
        self.current_item_index = 0
        self.ui_items   = []
        self.ui_widgets = []

        self.in_bios_ui       = False
        self.post_active      = False
        self.bios_opportunity = False
        self.boot_timer       = None
        self.boot_canvas      = None
        self.spinner_step     = 0
        self.clock_job        = None
        self.hw_job           = None
        self.current_scenario = None
        self.submenu_open     = False
        self.selected_bios_file = "None"

        self.settings = deepcopy(DEFAULT_SETTINGS)
        self._saved_settings = deepcopy(DEFAULT_SETTINGS)
        self.load_cmos()

        self.sys_info = {}
        self.collect_system_info()
        self.start_system_power_on()

    # ── CMOS ──────────────────────────────────────────────────────────────────
    def load_cmos(self):
        try:
            with open(CMOS_FILE, "r") as f:
                data = json.load(f)
            for k, v in data.items():
                if k in self.settings:
                    self.settings[k] = v
            self._saved_settings = deepcopy(self.settings)
        except Exception:
            pass

    def save_cmos(self):
        try:
            with open(CMOS_FILE, "w") as f:
                json.dump(self.settings, f, indent=2)
            self._saved_settings = deepcopy(self.settings)
        except Exception as e:
            messagebox.showerror("CMOS Error", f"Could not save CMOS: {e}")

    def discard_cmos(self):
        self.settings = deepcopy(self._saved_settings)

    # ── System Info ───────────────────────────────────────────────────────────
    def collect_system_info(self):
        si = self.sys_info
        si["os"] = platform.platform()
        try:
            si["user"] = os.getlogin()
        except Exception:
            si["user"] = "Unknown"

        if platform.system() == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                     r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                pn = winreg.QueryValueEx(key, "ProductName")[0]
                try:    dv = winreg.QueryValueEx(key, "DisplayVersion")[0]
                except: dv = ""
                ver = sys.getwindowsversion()
                if ver.build >= 22000 and "Windows 10" in pn:
                    pn = pn.replace("Windows 10", "Windows 11")
                si["os"] = f"{pn} ({dv})" if dv else pn
                key.Close()
            except Exception:
                pass
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                     r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                si["processor"] = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
                key.Close()
            except Exception:
                si["processor"] = platform.processor()
        else:
            si["processor"] = platform.processor() or "Unknown CPU"

        ram = psutil.virtual_memory()
        si["ram_total_kb"] = int(ram.total / 1024)
        si["ram_total"]    = f"{si['ram_total_kb']:,} KB"
        si["ram_total_mb"] = f"{int(ram.total / 1024**2)} MB"
        pc = psutil.cpu_count(logical=False) or 1
        lc = psutil.cpu_count(logical=True)  or 1
        si["cores"] = f"{pc}C / {lc}T"

        si["disks"] = []
        if platform.system() == "Windows":
            try:
                cmd = ('powershell -Command "Get-CimInstance Win32_DiskDrive | '
                       'ForEach-Object { $_.Model + \'||\' + $_.Size + \'||\' + $_.InterfaceType }"')
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                out, _ = proc.communicate(timeout=5)
                for line in out.decode("utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if "||" in line:
                        parts = line.split("||")
                        if len(parts) >= 2:
                            model = parts[0].strip()
                            try:   size_gb = round(float(parts[1]) / 1024**3, 1)
                            except: size_gb = 0
                            itype = parts[2].strip() if len(parts) > 2 else "SATA"
                            si["disks"].append({"model": model, "size": size_gb, "iface": itype})
            except Exception:
                pass
        if not si["disks"]:
            si["disks"] = [{"model": "Generic Hard Disk", "size": 256.0, "iface": "SATA"}]

        if self.settings.get("bios_flashed", False):
            si["bios_version"] = "PhoenixBIOS 4.0 r7.0 (Flashed)"
            si["bios_date"]    = "10/25/2024"
        else:
            si["bios_version"] = "PhoenixBIOS 4.0 r6.0 (Simulated)"
            si["bios_date"]    = "03/01/2024"

        try:
            freq = psutil.cpu_freq()
            si["cpu_freq"] = f"{freq.max/1000:.2f} GHz" if freq else "Unknown"
        except Exception:
            si["cpu_freq"] = "Unknown"

    # ── POST ──────────────────────────────────────────────────────────────────
    def start_system_power_on(self):
        for w in self.root.winfo_children():
            w.destroy()
        if self.clock_job:
            self.root.after_cancel(self.clock_job)
            self.clock_job = None
        if self.hw_job:
            self.root.after_cancel(self.hw_job)
            self.hw_job = None

        self.root.configure(bg=PHX_BLACK)
        self.post_active      = True
        self.bios_opportunity = False
        self.in_bios_ui       = False
        self.boot_canvas      = None

        self.post_frame = tk.Frame(self.root, bg=PHX_BLACK)
        self.post_frame.pack(fill="both", expand=True)

        self.post_text = tk.Text(self.post_frame, bg=PHX_BLACK, fg=PHX_WHITE,
                                 font=FONT_MAIN, bd=0, state="disabled",
                                 insertbackground=PHX_WHITE, width=95, height=32)
        self.post_text.pack(pady=30, padx=40, anchor="nw")

        self.countdown_var = tk.StringVar(value="")
        tk.Label(self.post_frame, textvariable=self.countdown_var,
                 fg=PHX_YELLOW, bg=PHX_BLACK, font=FONT_MAIN).pack(anchor="sw", padx=40)

        threading.Thread(target=self._run_post, daemon=True).start()

    def _post_write(self, text, color=PHX_WHITE, end="\n"):
        def _do():
            self.post_text.config(state="normal")
            tag = f"c_{id(color)}_{color}"
            self.post_text.tag_configure(tag, foreground=color)
            self.post_text.insert("end", text + end, tag)
            self.post_text.config(state="disabled")
            self.post_text.see("end")
        self.root.after(0, _do)

    def _run_post(self):
        s = self.sys_info
        ram_kb = s.get("ram_total_kb", 655360)
        rel_ver = "Release 7.0" if self.settings.get("bios_flashed") else "Release 6.0"
        self._post_write(f"PhoenixBIOS 4.0 {rel_ver}", PHX_CYAN)
        self._post_write("Copyright 1985-2024 Phoenix Technologies Ltd. All Rights Reserved.", PHX_WHITE)
        self._post_write(f"BIOS Version : {s.get('bios_version','')}", PHX_WHITE)
        self._post_write(f"BIOS Date    : {s.get('bios_date','')}", PHX_WHITE)
        self._post_write("")
        time.sleep(0.3)
        self._post_write(f"CPU Type  : {s.get('processor','Unknown')}", PHX_WHITE)
        self._post_write(f"CPU Speed : {s.get('cpu_freq','Unknown')}", PHX_WHITE)
        self._post_write(f"CPU Cores : {s.get('cores','')}", PHX_WHITE)
        oc = self.settings.get("cpu_multiplier","Auto")
        if oc != "Auto":
            self._post_write(f"CPU OC    : Multiplier manually set to {oc}", PHX_YELLOW)
        time.sleep(0.2)
        self._post_write("")
        self._post_write("Testing Memory ", PHX_WHITE, end="")
        for kb in range(0, ram_kb + 1, max(1, ram_kb // 30)):
            def _upd(k=kb):
                self.post_text.config(state="normal")
                idx = self.post_text.search(r'\d+ KB', "1.0", stopindex="end", regexp=True)
                if idx:
                    end_idx = self.post_text.search(r'\s', idx, stopindex="end")
                    self.post_text.delete(idx, end_idx if end_idx else f"{idx}+20c")
                    self.post_text.insert(idx, f"{k:,} KB")
                else:
                    self.post_text.insert("end", f"{k:,} KB")
                self.post_text.config(state="disabled")
            self.root.after(0, _upd)
            time.sleep(0.02)
        xmp = self.settings.get("ram_xmp","Disabled")
        freq = self.settings.get("ram_freq","Auto")
        self._post_write(f" -> {s.get('ram_total_mb','')} OK  [XMP: {xmp}  Freq: {freq}]", PHX_YELLOW)
        time.sleep(0.1)
        self._post_write("")
        self._post_write("2048K Cache SRAM  ... Passed", PHX_WHITE)
        self._post_write("System BIOS shadowed", PHX_WHITE)
        self._post_write("Video BIOS shadowed", PHX_WHITE)
        time.sleep(0.15)
        # Onboard device init
        self._post_write("")
        audio_state = self.settings.get("onboard_audio","Enabled")
        lan_state   = self.settings.get("onboard_lan","Enabled")
        igpu_state  = self.settings.get("igpu","Auto")
        self._post_write(f"Onboard HD Audio : {audio_state}", PHX_WHITE if audio_state=="Enabled" else PHX_GREY)
        self._post_write(f"Onboard LAN      : {lan_state}",   PHX_WHITE if lan_state=="Enabled"   else PHX_GREY)
        self._post_write(f"Integrated GPU   : {igpu_state}",  PHX_WHITE)
        time.sleep(0.1)
        self._post_write("")
        for i, d in enumerate(s.get("disks", [])):
            label = f"  Drive {i}: {d['model']}"
            size_str = f"  {d['size']} GB" if d['size'] else ""
            mode = self.settings.get("sata_mode","AHCI")
            self._post_write(f"{label}{size_str}  [{mode}]", PHX_WHITE)
            time.sleep(0.1)
        self._post_write("")
        bm = self.settings["boot_mode"]
        sb = self.settings["secure_boot"]
        self._post_write(f"Boot Mode    : {bm}",         PHX_CYAN)
        self._post_write(f"Secure Boot  : {sb}",         PHX_CYAN)
        self._post_write(f"TPM State    : {self.settings['tpm_state']}", PHX_CYAN)
        self._post_write(f"Virtualization: {self.settings['virtualization']}", PHX_CYAN)
        time.sleep(0.3)
        self._post_write("")
        self._post_write("Press <F2> or <Del> to enter SETUP", PHX_YELLOW)
        self.bios_opportunity = True
        self.root.after(0, self._start_countdown)

    def _start_countdown(self):
        self._countdown_sec = 5
        self._update_countdown()

    def _update_countdown(self):
        if not self.post_active: return
        if self._countdown_sec > 0:
            self.countdown_var.set(
                f"  Booting in {self._countdown_sec} second{'s' if self._countdown_sec!=1 else ''}...  "
                "  Press F2 / Del to enter BIOS Setup")
            self._countdown_sec -= 1
            self.boot_timer = self.root.after(1000, self._update_countdown)
        else:
            self.countdown_var.set("  Booting now...")
            self.boot_timer = self.root.after(500, self.attempt_os_boot)

    def on_bios_key(self, event):
        if self.post_active and self.bios_opportunity:
            if self.boot_timer:
                self.root.after_cancel(self.boot_timer)
                self.boot_timer = None
            self.bios_opportunity = False
            self.post_active = False
            self.in_bios_ui  = True
            self.root.after(0, self._check_bios_entry_password)

    def _check_bios_entry_password(self):
        stored = self.settings.get("supervisor_pw", "")
        if stored:
            entered = simpledialog.askstring("BIOS Password",
                "Enter Supervisor Password:", show="*", parent=self.root)
            if entered is None or sha256(entered) != stored:
                messagebox.showerror("Access Denied",
                    "Incorrect password.\nSystem will continue booting.")
                self.in_bios_ui = False
                self.attempt_os_boot()
                return
        self.load_bios_ui()

    # ── BIOS UI Shell ─────────────────────────────────────────────────────────
    def load_bios_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        if self.clock_job:
            self.root.after_cancel(self.clock_job)

        mc = tk.Frame(self.root, bg=PHX_CYAN)
        mc.pack(fill="both", expand=True)
        self.main_container = mc

        tk.Label(mc, text="PhoenixBIOS Setup Utility — Enhanced Edition",
                 fg=PHX_BLACK, bg=PHX_CYAN, font=FONT_TITLE).pack(pady=(4,2))

        self.menu_frame = tk.Frame(mc, bg=PHX_BLUE)
        self.menu_frame.pack(fill="x")
        tab_row = tk.Frame(self.menu_frame, bg=PHX_BLUE)
        tab_row.pack(anchor="w", padx=6)
        self.tab_labels = {}
        for tab in self.tabs:
            lbl = tk.Label(tab_row, text=f" {tab} ", font=FONT_SMALL_BOLD,
                           bg=PHX_BLUE, fg=PHX_WHITE, cursor="hand2")
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, t=tab: self.switch_tab(t))
            self.tab_labels[tab] = lbl

        co = tk.Frame(mc, bg=PHX_CYAN, padx=4, pady=2)
        co.pack(fill="both", expand=True)
        cb = tk.Frame(co, bg=PHX_BLACK, bd=1, relief="flat")
        cb.pack(fill="both", expand=True)

        lp_outer = tk.Frame(cb, bg=PHX_GREY)
        lp_outer.pack(side="left", fill="both", expand=True)
        canvas = tk.Canvas(lp_outer, bg=PHX_GREY, highlightthickness=0)
        scrollbar = tk.Scrollbar(lp_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.left_panel = tk.Frame(canvas, bg=PHX_GREY)
        self._lp_window = canvas.create_window((0,0), window=self.left_panel, anchor="nw")
        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.left_panel.bind("<Configure>", _on_configure)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self._lp_canvas = canvas

        tk.Frame(cb, bg=PHX_BLACK, width=1).pack(side="left", fill="y")

        rp = tk.Frame(cb, bg=PHX_GREY, width=320)
        rp.pack(side="right", fill="y")
        rp.pack_propagate(False)
        tk.Label(rp, text="Item Specific Help", fg=PHX_BLACK, bg=PHX_GREY,
                 font=FONT_MAIN).pack(pady=8)
        tk.Frame(rp, bg=PHX_BLACK, height=1).pack(fill="x")
        self.help_label = tk.Label(rp, text="", fg=PHX_BLACK, bg=PHX_GREY,
                                   font=("Consolas", 10), wraplength=300,
                                   justify="left", anchor="nw")
        self.help_label.pack(fill="both", expand=True, padx=10, pady=8)

        tk.Frame(rp, bg=PHX_BLACK, height=1).pack(fill="x", side="bottom")
        si_frame = tk.Frame(rp, bg=PHX_GREY)
        si_frame.pack(side="bottom", fill="x", padx=6, pady=4)
        s = self.sys_info
        for line in [
            f"OS: {s.get('os','')[:38]}",
            f"CPU: {s.get('processor','')[:38]}",
            f"RAM: {s.get('ram_total_mb','')}",
            f"BIOS: {s.get('bios_version','')}",
        ]:
            tk.Label(si_frame, text=line, fg=PHX_BLUE, bg=PHX_GREY,
                     font=FONT_SMALL, anchor="w").pack(fill="x")

        ff = tk.Frame(mc, bg=PHX_CYAN, pady=3)
        ff.pack(fill="x", side="bottom")
        keys = [("↑↓","Select"), ("←→","Tab"), ("+/-","Value"), ("Enter","Execute"),
                ("F9","Defaults"), ("F10","Save+Diagnose"), ("Esc","Exit")]
        krow = tk.Frame(ff, bg=PHX_CYAN)
        krow.pack()
        for k, d in keys:
            tk.Label(krow, text=k, fg=PHX_WHITE, bg=PHX_CYAN, font=FONT_MAIN).pack(side="left", padx=(6,2))
            tk.Label(krow, text=d, fg=PHX_BLACK, bg=PHX_CYAN, font=FONT_MAIN).pack(side="left", padx=(0,6))

        self.switch_tab(self.tabs[self.current_tab_index])
        self._tick_clock()

    def _tick_clock(self):
        if not self.in_bios_ui: return
        if self.tabs[self.current_tab_index] == "Main":
            for i, item in enumerate(self.ui_items):
                if item.get("id") == "sys_time":
                    new_val = f"[{time.strftime('%H:%M:%S')}]"
                    wp = self.ui_widgets[i]
                    if wp and wp.get("val") and i != self.current_item_index:
                        wp["val"].config(text=new_val)
                elif item.get("id") == "sys_date":
                    new_val = f"[{time.strftime('%m/%d/%Y')}]"
                    wp = self.ui_widgets[i]
                    if wp and wp.get("val") and i != self.current_item_index:
                        wp["val"].config(text=new_val)
        self.clock_job = self.root.after(1000, self._tick_clock)

    def _tick_hw_monitor(self):
        """Refresh hardware monitor values every 3 seconds."""
        if not self.in_bios_ui: return
        if self.tabs[self.current_tab_index] == "Monitor":
            self.switch_tab("Monitor")
        self.hw_job = self.root.after(3000, self._tick_hw_monitor)

    def switch_tab(self, tab_name):
        if tab_name not in self.tabs: return
        self.current_tab_index = self.tabs.index(tab_name)

        for t, lbl in self.tab_labels.items():
            lbl.config(bg=(PHX_GREY if t == tab_name else PHX_BLUE),
                       fg=(PHX_BLUE if t == tab_name else PHX_WHITE))

        for w in self.left_panel.winfo_children():
            w.destroy()

        self.ui_items   = []
        self.ui_widgets = []
        self.current_item_index = 0
        self.help_label.config(text="")

        renderers = {
            "Main":        self.render_main_tab,
            "Advanced":    self.render_advanced_tab,
            "Security":    self.render_security_tab,
            "Boot":        self.render_boot_tab,
            "Power":       self.render_power_tab,
            "Overclock":   self.render_overclock_tab,
            "PCI/Onboard": self.render_pci_tab,
            "Monitor":     self.render_monitor_tab,
            "Update":      self.render_update_tab,
            "Exit":        self.render_exit_tab,
            "Lab":         self.render_lab_tab,
        }
        renderers[tab_name]()
        self._draw_ui_items()

        for i, item in enumerate(self.ui_items):
            if item.get("selectable"):
                self.current_item_index = i
                break
        self._update_visuals()

        # Start HW monitor ticker if needed
        if tab_name == "Monitor":
            if self.hw_job:
                self.root.after_cancel(self.hw_job)
            self.hw_job = self.root.after(3000, self._tick_hw_monitor)

    # ── TAB RENDERERS ─────────────────────────────────────────────────────────
    def _S(self, key):
        return self.settings.get(key, "")

    def render_main_tab(self):
        self.ui_items = [
            {"type":"header","label":"── System Information ─────────────────────────────"},
            {"type":"ro","label":"BIOS Version   :", "val": self.sys_info.get("bios_version",""), "help":"Current BIOS firmware version."},
            {"type":"ro","label":"BIOS Date      :", "val": self.sys_info.get("bios_date",""),    "help":"BIOS release date."},
            {"type":"ro","label":"Processor      :", "val": self.sys_info.get("processor",""),    "help":"Installed CPU model and speed."},
            {"type":"ro","label":"CPU Cores      :", "val": self.sys_info.get("cores",""),        "help":"Physical cores / logical threads."},
            {"type":"ro","label":"System Memory  :", "val": self.sys_info.get("ram_total_mb",""), "help":"Total installed system RAM."},
            {"type":"space"},
            {"type":"header","label":"── Date & Time ────────────────────────────────────"},
            {"id":"sys_time","type":"edit","label":"System Time    :", "val": time.strftime('%H:%M:%S'),
             "help":"Set system time (HH:MM:SS).\nPress Enter to edit.", "selectable":True, "action": self._edit_time},
            {"id":"sys_date","type":"edit","label":"System Date    :", "val": time.strftime('%m/%d/%Y'),
             "help":"Set system date (MM/DD/YYYY).\nPress Enter to edit.", "selectable":True, "action": self._edit_date},
            {"type":"space"},
            {"type":"header","label":"── Storage Devices ────────────────────────────────"},
        ]
        for i, d in enumerate(self.sys_info.get("disks", [])):
            val = f"{d['model']} ({d['size']} GB)" if d['size'] else d['model']
            self.ui_items.append({"type":"ro","label":f"Drive {i}        :","val":val,"help":"Detected storage device."})
        self.ui_items += [
            {"type":"space"},
            {"type":"header","label":"── Floppy Drives ─────────────────────────────────"},
            {"type":"val","label":"Legacy Diskette A:", "val_key":"diskette_a",
             "options":["Disabled","360 KB 5¼\"","1.2 MB 5¼\"","720 KB 3½\"","1.44/1.25 MB 3½\"","2.88 MB 3½\""],
             "help":"Select diskette drive A type.", "selectable":True},
            {"type":"val","label":"Legacy Diskette B:", "val_key":"diskette_b",
             "options":["Disabled","360 KB 5¼\"","1.2 MB 5¼\"","720 KB 3½\"","1.44/1.25 MB 3½\"","2.88 MB 3½\""],
             "help":"Select diskette drive B type.", "selectable":True},
            {"type":"space"},
            {"type":"val","label":"Boot Diagnostic  :", "val_key":"diag_screen",
             "options":["Disabled","Enabled"],
             "help":"Show POST diagnostic screen during boot.", "selectable":True},
        ]

    def render_advanced_tab(self):
        self.ui_items = [
            {"type":"header","label":"── Processor / Chipset ───────────────────────────"},
            {"type":"val","label":"MP Specification :", "val_key":"mp_spec", "options":["1.1","1.4"],
             "help":"Multiprocessor spec. 1.4 for modern OS.", "selectable":True},
            {"type":"val","label":"Installed O/S    :", "val_key":"installed_os",
             "options":["Other","Win95/98/ME","Win2000/XP","Win7/8/10","Win11"],
             "help":"Select your OS for optimal ACPI settings.", "selectable":True},
            {"type":"val","label":"Reset Config Data:", "val_key":"reset_config", "options":["No","Yes"],
             "help":"Clear extended config data (PnP). Resets to No after POST.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── Cache Memory ──────────────────────────────────"},
            {"type":"val","label":"Internal Cache   :", "val_key":"cache_internal", "options":["Enabled","Disabled"],
             "help":"L1/L2 CPU internal cache. Disabling severely reduces performance.", "selectable":True},
            {"type":"val","label":"External Cache   :", "val_key":"cache_external", "options":["Enabled","Disabled"],
             "help":"L3 external cache. Keep Enabled.", "selectable":True},
            {"type":"val","label":"Cache Size       :", "val_key":"cache_size",
             "options":["256 KB","512 KB","1 MB","2 MB","4 MB"],
             "help":"External cache size assignment.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── I/O Device Configuration ──────────────────────"},
            {"type":"val","label":"COM1 Port        :", "val_key":"com1_port",
             "options":["Disabled","3F8h/IRQ4","2F8h/IRQ3","3E8h/IRQ4","2E8h/IRQ3"],
             "help":"Serial Port 1 address and IRQ.", "selectable":True},
            {"type":"val","label":"COM2 Port        :", "val_key":"com2_port",
             "options":["Disabled","2F8h/IRQ3","3F8h/IRQ4","3E8h/IRQ4","2E8h/IRQ3"],
             "help":"Serial Port 2 address and IRQ.", "selectable":True},
            {"type":"val","label":"LPT Port         :", "val_key":"lpt_port",
             "options":["Disabled","378h/IRQ7","278h/IRQ5","3BCh/IRQ7"],
             "help":"Parallel port address and IRQ.", "selectable":True},
            {"type":"val","label":"LPT Mode         :", "val_key":"lpt_mode",
             "options":["Normal","EPP","ECP","ECP+EPP"],
             "help":"Parallel port operating mode.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── USB Configuration ─────────────────────────────"},
            {"type":"val","label":"USB Legacy Supp  :", "val_key":"usb_legacy", "options":["Enabled","Disabled"],
             "help":"Allow USB keyboard/mouse in pre-boot environments.", "selectable":True},
            {"type":"val","label":"USB 2.0 Support  :", "val_key":"usb_2_support", "options":["Enabled","Disabled"],
             "help":"Enable USB Hi-Speed (480 Mb/s) support.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── Disk Configuration ────────────────────────────"},
            {"type":"val","label":"Large Disk Mode  :", "val_key":"disk_access_mode",
             "options":["DOS","Other","LBA","Auto"],
             "help":"LBA mode for large disk support.", "selectable":True},
            {"type":"val","label":"Local Bus IDE    :", "val_key":"local_bus_ide",
             "options":["Both","Primary","Secondary","Disabled"],
             "help":"Enable integrated IDE controller channels.", "selectable":True},
        ]

    def render_security_tab(self):
        sv_set = bool(self._S("supervisor_pw"))
        uv_set = bool(self._S("user_pw"))
        self.ui_items = [
            {"type":"header","label":"── Passwords ─────────────────────────────────────"},
            {"type":"ro","label":"Supervisor PW   :", "val":"Set" if sv_set else "Clear", "help":"Supervisor password status."},
            {"type":"ro","label":"User PW         :", "val":"Set" if uv_set else "Clear", "help":"User password status."},
            {"type":"space"},
            {"type":"action","label":"Set Supervisor Password",
             "help":"Set/change/clear the supervisor password.", "selectable":True, "action": self._set_supervisor_pw},
            {"type":"action","label":"Set User Password",
             "help":"Set/change/clear the user password.", "selectable":True, "action": self._set_user_pw},
            {"type":"space"},
            {"type":"val","label":"Password On Boot:", "val_key":"pw_on_boot", "options":["Disabled","Enabled"],
             "help":"Require password at every boot.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── Platform Security ─────────────────────────────"},
            {"type":"val","label":"Secure Boot     :", "val_key":"secure_boot", "options":["Enabled","Disabled"],
             "help":"UEFI Secure Boot. Required for Windows 11.", "selectable":True},
            {"type":"val","label":"TPM State       :", "val_key":"tpm_state", "options":["Enabled","Disabled"],
             "help":"Trusted Platform Module. Required for Windows 11 and BitLocker.", "selectable":True},
            {"type":"val","label":"Chassis Intrusion:", "val_key":"chassis_intrusion",
             "options":["Disabled","Enabled","Reset"],
             "help":"Detect if chassis cover was removed.", "selectable":True},
        ]

    def render_boot_tab(self):
        order = self.settings["boot_order"]
        self.ui_items = [
            {"type":"header","label":"── Boot Device Priority ──────────────────────────"},
            {"type":"header","label":"  Use +/- to move device. Enter to toggle enable."},
            {"type":"space"},
        ]
        for i, dev in enumerate(order):
            self.ui_items.append({
                "type":"boot_item","label":f"  {i+1}.","val":dev,
                "boot_idx": i,
                "help": f"Boot priority {i+1}.\n+ = move UP, - = move DOWN.\nEnter = Enable/Disable.",
                "selectable":True,
                "enabled": not dev.startswith("[Disabled]"),
            })
        self.ui_items += [
            {"type":"space"},
            {"type":"header","label":"── Boot Settings ─────────────────────────────────"},
            {"type":"val","label":"NumLock State   :", "val_key":"boot_num_lock", "options":["On","Off"],
             "help":"Set NumLock state after POST.", "selectable":True},
            {"type":"val","label":"Fast Boot        :", "val_key":"fast_boot", "options":["Enabled","Disabled"],
             "help":"Skip some POST checks for faster boot.", "selectable":True},
        ]

    def render_power_tab(self):
        self.ui_items = [
            {"type":"header","label":"── Boot Mode / Firmware ──────────────────────────"},
            {"type":"val","label":"Boot Mode        :", "val_key":"boot_mode", "options":["UEFI","Legacy"],
             "help":"UEFI: modern mode, GPT disks, Secure Boot.\nLegacy: MBR, older OS.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── CPU Features ──────────────────────────────────"},
            {"type":"val","label":"Virtualization   :", "val_key":"virtualization", "options":["Enabled","Disabled"],
             "help":"Intel VT-x / AMD-V. Required for VMs, WSL2, Docker.", "selectable":True},
            {"type":"val","label":"Hyper-Threading  :", "val_key":"hyperthreading", "options":["Enabled","Disabled"],
             "help":"Intel SMT / Hyper-Threading. Doubles thread count.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── Memory ────────────────────────────────────────"},
            {"type":"val","label":"RAM Frequency    :", "val_key":"ram_freq",
             "options":["Auto","1600 MHz","2133 MHz","2400 MHz","2666 MHz","3200 MHz","3600 MHz","4800 MHz"],
             "help":"Memory bus frequency. Auto = SPD default.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── Storage ───────────────────────────────────────"},
            {"type":"val","label":"SATA Mode        :", "val_key":"sata_mode", "options":["AHCI","IDE","RAID"],
             "help":"AHCI: modern, TRIM, hot-swap.\nIDE: legacy.\nRAID: hardware RAID.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── Power Management ──────────────────────────────"},
            {"type":"val","label":"CPU Fan Control  :", "val_key":"cpu_fan_ctrl",
             "options":["Auto","Full Speed","Silent","Manual"],
             "help":"CPU fan speed control mode.", "selectable":True},
            {"type":"val","label":"Power On with AC :", "val_key":"pwr_on_ac",
             "options":["Disabled","Enabled","Last State"],
             "help":"Auto-power on when AC power is restored.", "selectable":True},
            {"type":"val","label":"Wake On LAN      :", "val_key":"wake_on_lan", "options":["Disabled","Enabled"],
             "help":"Allow network magic-packet to wake system.", "selectable":True},
        ]

    def render_overclock_tab(self):
        self.ui_items = [
            {"type":"header","label":"── CPU Overclocking ──────────────────────────────"},
            {"type":"header","label":"  ⚠  Changes here can damage hardware if misused."},
            {"type":"space"},
            {"type":"val","label":"CPU Multiplier   :", "val_key":"cpu_multiplier",
             "options":["Auto","38x","40x","42x","44x","46x","48x","50x","52x","54x","56x"],
             "help":"CPU clock multiplier.\nAuto = Turbo Boost managed.\nManual = fixed OC. Requires K-CPU + Z-board.\nRisk: instability, degradation, heat.", "selectable":True},
            {"type":"val","label":"CPU Base Clock   :", "val_key":"cpu_base_clock",
             "options":["100 MHz","102 MHz","105 MHz","110 MHz","115 MHz","120 MHz"],
             "help":"BCLK (base clock). Affects CPU, PCIe, and memory.\nEven small increases affect everything — dangerous on non-K CPUs.", "selectable":True},
            {"type":"val","label":"CPU Vcore        :", "val_key":"cpu_voltage",
             "options":["Auto","1.100V","1.150V","1.200V","1.250V","1.300V","1.350V","1.400V","1.450V","1.500V"],
             "help":"CPU core voltage.\nAuto = VRM manages safely.\nManual: >1.4V risks permanent CPU damage.\nKeep below 1.35V for daily use.", "selectable":True},
            {"type":"val","label":"CPU Power Limit  :", "val_key":"cpu_power_limit",
             "options":["Auto","65W","95W","125W","150W","175W","200W","Unlimited"],
             "help":"PL1/PL2 power limit for CPU.\nAuto = Intel/AMD default.\nUnlimited: max sustained boost, may overheat.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── Memory Overclocking ───────────────────────────"},
            {"type":"val","label":"XMP / DOCP       :", "val_key":"ram_xmp",
             "options":["Disabled","Profile 1","Profile 2"],
             "help":"Enables manufacturer RAM overclock profile.\nDisabled = JEDEC default (safe).\nProfile 1/2 = advertised speed (requires Z/X board).", "selectable":True},
            {"type":"val","label":"RAM Voltage      :", "val_key":"ram_voltage",
             "options":["Auto","1.200V","1.250V","1.300V","1.350V","1.400V","1.450V","1.500V"],
             "help":"DRAM voltage.\nDDR4 standard: 1.2V (JEDEC), 1.35V (XMP).\n>1.45V risks RAM and IMC damage.", "selectable":True},
            {"type":"val","label":"RAM Timings      :", "val_key":"ram_timings",
             "options":["Auto","14-14-14-34","15-15-15-35","16-18-18-38","18-22-22-42"],
             "help":"CAS latency - tRCD - tRP - tRAS.\nAuto = SPD values (safe).\nTighter timings = lower latency but may be unstable.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── Miscellaneous ─────────────────────────────────"},
            {"type":"val","label":"Spread Spectrum  :", "val_key":"spread_spectrum",
             "options":["Enabled","Disabled"],
             "help":"Spreads clock frequency to reduce EMI.\nDisable for extreme overclocking (cleaner signal).\nKeep Enabled for normal use.", "selectable":True},
        ]

    def render_pci_tab(self):
        self.ui_items = [
            {"type":"header","label":"── Onboard Devices ───────────────────────────────"},
            {"type":"val","label":"Onboard HD Audio :", "val_key":"onboard_audio",
             "options":["Enabled","Disabled"],
             "help":"Integrated Realtek/ALC audio codec.\nDisable only if using a dedicated PCIe sound card.", "selectable":True},
            {"type":"val","label":"Onboard LAN 1    :", "val_key":"onboard_lan",
             "options":["Enabled","Disabled"],
             "help":"Primary onboard Gigabit Ethernet controller.\nDisabling removes the main RJ45 port.", "selectable":True},
            {"type":"val","label":"Onboard LAN 2    :", "val_key":"onboard_lan2",
             "options":["Disabled","Enabled"],
             "help":"Secondary LAN (if present on board).\nUsed for dual-NIC server/router builds.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── Integrated Graphics ───────────────────────────"},
            {"type":"val","label":"Integrated GPU   :", "val_key":"igpu",
             "options":["Auto","Enabled","Disabled"],
             "help":"CPU integrated graphics (Intel UHD / AMD Radeon).\nAuto = active only when no dGPU present.\nEnabled = always on (multi-monitor with dGPU).\nDisabled = rear video ports dead.", "selectable":True},
            {"type":"val","label":"iGPU Memory      :", "val_key":"igpu_memory",
             "options":["32 MB","64 MB","128 MB","256 MB","512 MB"],
             "help":"Shared system RAM reserved for iGPU frame buffer.\nOnly relevant when iGPU is active.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── PCIe Slots ────────────────────────────────────"},
            {"type":"val","label":"PCIe x16 Slot    :", "val_key":"pcie_x16_slot",
             "options":["Auto","x16","x8","x4","Disabled"],
             "help":"Primary PCIe x16 slot for discrete GPU.\nAuto recommended. x8 mode used for PCIe bifurcation.\nDisabling slot disables discrete GPU.", "selectable":True},
            {"type":"val","label":"PCIe x1 Slot 1   :", "val_key":"pcie_x1_slot1",
             "options":["Enabled","Disabled"],
             "help":"First PCIe x1 slot (sound cards, NICs, capture cards).\nDisable to free IRQ resources if slot is unused.", "selectable":True},
            {"type":"val","label":"PCIe x1 Slot 2   :", "val_key":"pcie_x1_slot2",
             "options":["Enabled","Disabled"],
             "help":"Second PCIe x1 slot.", "selectable":True},
            {"type":"space"},
            {"type":"header","label":"── PCI / Memory Mapping ──────────────────────────"},
            {"type":"val","label":"PCI Latency Timer:", "val_key":"pci_latency",
             "options":["32","64","96","128"],
             "help":"PCI bus latency timer in PCI clock units.\n32 = standard. Higher values improve PCI device\nthroughput but may cause IRQ conflicts.", "selectable":True},
            {"type":"val","label":"Above 4G Decoding:", "val_key":"above_4g_decoding",
             "options":["Disabled","Enabled"],
             "help":"Maps PCIe BARs above 4 GB address space.\nRequired for GPUs with 8GB+ VRAM and Resizable BAR.\nNeeds 64-bit OS.", "selectable":True},
            {"type":"val","label":"Resizable BAR    :", "val_key":"resizable_bar",
             "options":["Disabled","Enabled"],
             "help":"Allows CPU full VRAM access in one transaction.\nProvides 2-15% gaming performance boost.\nRequires: Above 4G Decoding ON, modern GPU + driver.", "selectable":True},
        ]

    def render_monitor_tab(self):
        hw = get_simulated_hw_data(self.settings)

        def temp_color(t):
            if t < 55: return PHX_GREEN
            elif t < 75: return PHX_YELLOW
            else: return PHX_RED

        def volt_color(v, nominal, tolerance=0.08):
            if abs(v - nominal) / nominal < tolerance: return PHX_GREEN
            elif abs(v - nominal) / nominal < 0.12: return PHX_YELLOW
            else: return PHX_RED

        self.ui_items = [
            {"type":"header","label":"── Temperature ───────────────────────────────────"},
            {"type":"ro_color","label":"CPU Temperature  :", "val": f"{hw['cpu_temp']} °C",
             "color": temp_color(hw['cpu_temp']),
             "help":"CPU package temperature.\n<55°C: Normal  55-75°C: Warm  >75°C: Hot/Throttling\nRefreshes every 3 seconds."},
            {"type":"ro_color","label":"Motherboard Temp :", "val": f"{hw['mb_temp']} °C",
             "color": temp_color(hw['mb_temp']),
             "help":"Motherboard PCH/chipset temperature."},
            {"type":"space"},
            {"type":"header","label":"── Fan Speeds ────────────────────────────────────"},
            {"type":"ro_color","label":"CPU Fan Speed    :", "val": f"{hw['cpu_fan_rpm']} RPM",
             "color": PHX_GREEN if hw['cpu_fan_rpm'] > 300 else PHX_RED,
             "help":"CPU cooler fan RPM.\n<300 RPM: Fan may have stopped — check immediately!"},
            {"type":"ro_color","label":"System Fan Speed :", "val": f"{hw['sys_fan_rpm']} RPM",
             "color": PHX_GREEN if hw['sys_fan_rpm'] > 300 else PHX_YELLOW,
             "help":"Case/chassis fan RPM."},
            {"type":"space"},
            {"type":"header","label":"── Voltages ──────────────────────────────────────"},
            {"type":"ro_color","label":"CPU Vcore        :", "val": f"{hw['vcore']:.3f} V",
             "color": volt_color(hw['vcore'], 1.18),
             "help":"CPU core voltage.\nExpected range: 1.00–1.35V under load.\nAbnormally high = overheating risk."},
            {"type":"ro_color","label":"DRAM Voltage     :", "val": f"{hw['dram_v']:.3f} V",
             "color": volt_color(hw['dram_v'], 1.35),
             "help":"DDR4 DRAM supply voltage.\nStandard DDR4: 1.2V (JEDEC), XMP: 1.35–1.45V."},
            {"type":"ro_color","label":"+3.3V Rail       :", "val": f"{hw['v3_3']:.3f} V",
             "color": volt_color(hw['v3_3'], 3.30),
             "help":"+3.3V power rail for PCIe and some devices.\nNormal range: 3.14–3.47V."},
            {"type":"ro_color","label":"+5V Rail         :", "val": f"{hw['v5']:.3f} V",
             "color": volt_color(hw['v5'], 5.00),
             "help":"+5V rail for USB and storage.\nNormal range: 4.75–5.25V."},
            {"type":"ro_color","label":"+12V Rail        :", "val": f"{hw['v12']:.3f} V",
             "color": volt_color(hw['v12'], 12.0, 0.05),
             "help":"+12V rail for CPU and GPU.\nNormal range: 11.4–12.6V. Most critical rail."},
            {"type":"space"},
            {"type":"header","label":"── Status ────────────────────────────────────────"},
            {"type":"ro","label":"Fan Control Mode :", "val": self._S("cpu_fan_ctrl"),
             "help":"Current fan control mode (from Power tab)."},
            {"type":"ro","label":"XMP Profile      :", "val": self._S("ram_xmp"),
             "help":"Memory overclock profile status."},
            {"type":"ro","label":"CPU Multiplier   :", "val": self._S("cpu_multiplier"),
             "help":"CPU clock multiplier (from Overclock tab)."},
            {"type":"space"},
            {"type":"action","label":"  ↻  Refresh Readings",
             "help":"Refresh all hardware monitor readings now.\nAuto-refreshes every 3 seconds.", "selectable":True,
             "action": lambda: self.switch_tab("Monitor")},
        ]

    def render_update_tab(self):
        self.ui_items = [
            {"type":"header","label":"── EZ Flash BIOS Update Utility ──────────────────"},
            {"type":"ro","label":"Motherboard Model:", "val": "Phoenix SimBoard X99",
             "help":"Identify your exact motherboard model before downloading updates."},
            {"type":"ro","label":"Current BIOS Ver :", "val": self.sys_info.get("bios_version",""),
             "help":"Currently installed BIOS firmware version."},
            {"type":"ro","label":"Current BIOS Date:", "val": self.sys_info.get("bios_date",""),
             "help":"Release date of current BIOS."},
            {"type":"space"},
            {"type":"header","label":"── Select Update Medium ──────────────────────────"},
            {"type":"action","label":"Scan USB Drives",
             "help":"Scan USB flash drives (FAT32) for .CAP/.ROM update files.",
             "selectable":True, "action": self._scan_usb_drives},
            {"type":"ro","label":"Selected File    :", "val": self.selected_bios_file,
             "help":"BIOS file found on USB drive."},
            {"type":"space"},
            {"type":"header","label":"── Flash Operation ───────────────────────────────"},
            {"type":"action","label":"Start Firmware Update",
             "help":"Begin flashing.\nWARNING: Do not power off!", "selectable":True, "action": self._start_bios_flash},
            {"type":"space"},
            {"type":"action","label":"View Flashing Guide",
             "help":"Step-by-step BIOS flashing procedure.", "selectable":True, "action": self._show_flash_advice},
        ]

    def render_exit_tab(self):
        self.ui_items = [
            {"type":"action","label":"Exit Saving Changes + Diagnose",
             "help":"Save all changes, show full diagnostic report, then reboot.",
             "selectable":True,"action":self.global_save_exit},
            {"type":"action","label":"Exit Discarding Changes",
             "help":"Discard unsaved changes and exit.",
             "selectable":True,"action":self.global_exit},
            {"type":"space"},
            {"type":"action","label":"Load Setup Defaults",
             "help":"Restore factory defaults. Not saved until you Exit Saving.",
             "selectable":True,"action":self.load_defaults},
            {"type":"action","label":"Load Optimal Defaults",
             "help":"Load optimised performance defaults.",
             "selectable":True,"action":self._load_optimal_defaults},
            {"type":"space"},
            {"type":"action","label":"Discard Changes",
             "help":"Reload last-saved CMOS without exiting.", "selectable":True,"action":self._discard_changes_only},
            {"type":"action","label":"Save Changes",
             "help":"Save current settings to CMOS without exiting.", "selectable":True,"action":self._save_changes_only},
        ]

    def render_lab_tab(self):
        self.ui_items = [
            {"type":"header","label":"── IT Lab — BIOS Troubleshooting Scenarios ───────"},
            {"type":"space"},
            {"type":"ro","label":"Active Scenario :",
             "val": f"Scenario {self.current_scenario}" if self.current_scenario else "None",
             "help":"Currently loaded training scenario."},
            {"type":"space"},
            {"type":"action","label":"▶ Scenario 1 — Windows 11 Won't Install",
             "help":"Problem: 'This PC can't run Windows 11'\nFix: Enable UEFI + Secure Boot + TPM.",
             "selectable":True,"action":self._lab_scenario1},
            {"type":"action","label":"▶ Scenario 2 — PXE Boot Loop",
             "help":"Error: 'PXE-E61: Media test failure'\nFix: Set HDD as first boot device.",
             "selectable":True,"action":self._lab_scenario2},
            {"type":"action","label":"▶ Scenario 3 — SATA Drive Not Detected by OS",
             "help":"Problem: SATA HDD visible in BIOS but not in Windows.\nFix: SATA mode IDE → AHCI.",
             "selectable":True,"action":self._lab_scenario3},
            {"type":"action","label":"▶ Scenario 4 — VM Hypervisor Error",
             "help":"Error: 'VT-x is not available'\nFix: Enable CPU Virtualization.",
             "selectable":True,"action":self._lab_scenario4},
            {"type":"action","label":"▶ Scenario 5 — BitLocker Recovery Key Every Boot",
             "help":"Problem: BitLocker asks for 48-digit key every boot.\nFix: Enable TPM + Secure Boot.",
             "selectable":True,"action":self._lab_scenario5},
            {"type":"action","label":"▶ Scenario 6 — RAM Running at Wrong Speed",
             "help":"Problem: 3200MHz RAM running at 2133MHz.\nFix: Enable XMP Profile 1.",
             "selectable":True,"action":self._lab_scenario6},
            {"type":"action","label":"▶ Scenario 7 — GPU VRAM Not Fully Accessible",
             "help":"Problem: 8GB GPU shows only 4GB usable VRAM.\nFix: Enable Above 4G Decoding + Resizable BAR.",
             "selectable":True,"action":self._lab_scenario7},
            {"type":"action","label":"▶ Scenario 8 — PC Overheating During OC",
             "help":"Problem: CPU throttling and crashing during overclock.\nFix: Fan control not set correctly for OC workload.",
             "selectable":True,"action":self._lab_scenario8},
            {"type":"space"},
            {"type":"action","label":"✔ Verify My Solution",
             "help":"Check if current settings correctly resolve the active scenario.",
             "selectable":True,"action":self._lab_verify},
            {"type":"action","label":"✖ Clear Scenario",
             "help":"Dismiss scenario and restore defaults.",
             "selectable":True,"action":self._lab_clear},
        ]

    # ── DRAW & SELECTION ──────────────────────────────────────────────────────
    def _draw_ui_items(self):
        self.ui_widgets = []
        for i, item in enumerate(self.ui_items):
            t = item["type"]
            if t == "space":
                tk.Label(self.left_panel, text="", bg=PHX_GREY, height=1
                         ).grid(row=i, column=0, columnspan=3)
                self.ui_widgets.append(None)
                continue
            if t == "header":
                lbl = tk.Label(self.left_panel, text=item["label"],
                               fg=PHX_BLUE, bg=PHX_GREY, font=FONT_SMALL, anchor="w")
                lbl.grid(row=i, column=0, columnspan=3, sticky="w", padx=4, pady=(4,0))
                self.ui_widgets.append(None)
                continue

            lbl = tk.Label(self.left_panel, text=item.get("label",""),
                           bg=PHX_GREY, fg=PHX_BLUE, font=FONT_MAIN, anchor="w", width=20)
            lbl.grid(row=i, column=0, sticky="w", padx=(16,6), pady=1)

            val_lbl = None
            if t in ("val","ro","edit","boot_item","ro_color"):
                if t == "val":
                    raw = self._S(item["val_key"])
                elif t in ("ro","edit"):
                    raw = item.get("val","")
                elif t == "ro_color":
                    raw = item.get("val","")
                elif t == "boot_item":
                    dev = item["val"]
                    if not item.get("enabled", True):
                        dev = f"[Disabled] {dev.replace('[Disabled] ','')}"
                    raw = dev

                fg = PHX_BLACK
                if t == "ro_color":
                    fg = item.get("color", PHX_GREEN)
                elif t == "boot_item" and not item.get("enabled", True):
                    fg = "#888888"

                val_lbl = tk.Label(self.left_panel, text=f"[{raw}]",
                                   bg=PHX_GREY, fg=fg, font=FONT_MAIN, anchor="w")
                val_lbl.grid(row=i, column=1, sticky="w", padx=(0,10))
            elif t == "action":
                lbl.config(fg=PHX_BLUE, width=40)

            self.ui_widgets.append({"label":lbl,"val":val_lbl,"item":item})

            if item.get("selectable"):
                for w in [lbl, val_lbl]:
                    if w:
                        w.bind("<Button-1>",       lambda e, idx=i: self._mouse_select(idx))
                        w.bind("<Double-Button-1>", lambda e, idx=i: self._mouse_activate(idx))

    def _mouse_select(self, idx):
        self.current_item_index = idx
        self._update_visuals()

    def _mouse_activate(self, idx):
        self.current_item_index = idx
        self._update_visuals()
        self._activate_item(self.ui_items[idx])

    def _update_visuals(self):
        for i, wp in enumerate(self.ui_widgets):
            if wp is None: continue
            lbl  = wp["label"]
            val  = wp["val"]
            item = wp["item"]

            if i == self.current_item_index:
                self.help_label.config(text=item.get("help",""))
                lbl.config(fg=PHX_WHITE, bg=PHX_BLUE)
                if val: val.config(fg=PHX_WHITE, bg=PHX_BLUE)
            else:
                is_disabled_boot = (item["type"]=="boot_item" and not item.get("enabled",True))
                is_color = (item["type"] == "ro_color")
                base_fg = "#888888" if is_disabled_boot else PHX_BLUE
                lbl.config(fg=base_fg, bg=PHX_GREY)
                if val:
                    if is_color:
                        val.config(fg=item.get("color", PHX_GREEN), bg=PHX_GREY)
                    elif is_disabled_boot:
                        val.config(fg="#888888", bg=PHX_GREY)
                    else:
                        val.config(fg=PHX_BLACK, bg=PHX_GREY)
        try:
            wp = self.ui_widgets[self.current_item_index]
            if wp:
                lbl = wp["label"]
                lbl.update_idletasks()
                y = lbl.winfo_y()
                h = self.left_panel.winfo_height()
                self._lp_canvas.yview_moveto(max(0, (y - 50) / max(h, 1)))
        except Exception:
            pass

    def _activate_item(self, item):
        t = item["type"]
        if t == "action" and item.get("action"):  item["action"]()
        elif t == "edit" and item.get("action"):  item["action"]()
        elif t == "val":                           self._cycle_value(item)
        elif t == "boot_item":                     self._toggle_boot_device(item)

    def _cycle_value(self, item, reverse=False):
        key  = item["val_key"]
        opts = item["options"]
        cur  = self._S(key)
        try:    idx = opts.index(cur)
        except: idx = 0
        idx = (idx + (-1 if reverse else 1)) % len(opts)
        self.settings[key] = opts[idx]
        self.switch_tab(self.tabs[self.current_tab_index])
        for i, it in enumerate(self.ui_items):
            if it.get("val_key") == key:
                self.current_item_index = i
                self._update_visuals()
                break

    # ── Navigation ────────────────────────────────────────────────────────────
    def nav_up(self, e=None):
        if not self.in_bios_ui: return
        self._move(-1)
    def nav_down(self, e=None):
        if not self.in_bios_ui: return
        self._move(1)
    def _move(self, d):
        idx = self.current_item_index + d
        while 0 <= idx < len(self.ui_items):
            if self.ui_items[idx].get("selectable"):
                self.current_item_index = idx
                self._update_visuals()
                return
            idx += d
    def nav_left(self, e=None):
        if not self.in_bios_ui: return
        self.current_tab_index = (self.current_tab_index - 1) % len(self.tabs)
        self.switch_tab(self.tabs[self.current_tab_index])
    def nav_right(self, e=None):
        if not self.in_bios_ui: return
        self.current_tab_index = (self.current_tab_index + 1) % len(self.tabs)
        self.switch_tab(self.tabs[self.current_tab_index])
    def nav_tab(self, e=None):
        if not self.in_bios_ui: return
        self._move(1)
    def nav_pgup(self, e=None):
        if not self.in_bios_ui: return
        for _ in range(5): self._move(-1)
    def nav_pgdn(self, e=None):
        if not self.in_bios_ui: return
        for _ in range(5): self._move(1)
    def nav_enter(self, e=None):
        if not self.in_bios_ui or not self.ui_items: return
        self._activate_item(self.ui_items[self.current_item_index])
    def nav_plus(self, e=None):
        if not self.in_bios_ui or not self.ui_items: return
        item = self.ui_items[self.current_item_index]
        if item["type"] == "val": self._cycle_value(item, reverse=False)
        elif item["type"] == "boot_item": self._move_boot_device(item["boot_idx"], -1)
    def nav_minus(self, e=None):
        if not self.in_bios_ui or not self.ui_items: return
        item = self.ui_items[self.current_item_index]
        if item["type"] == "val": self._cycle_value(item, reverse=True)
        elif item["type"] == "boot_item": self._move_boot_device(item["boot_idx"], 1)

    # ── Boot order ────────────────────────────────────────────────────────────
    def _move_boot_device(self, idx, direction):
        order = self.settings["boot_order"]
        new_idx = idx + direction
        if 0 <= new_idx < len(order):
            order[idx], order[new_idx] = order[new_idx], order[idx]
            self.switch_tab("Boot")
            for i, item in enumerate(self.ui_items):
                if item.get("type") == "boot_item" and item.get("boot_idx") == new_idx:
                    self.current_item_index = i
                    self._update_visuals()
                    break

    def _toggle_boot_device(self, item):
        idx = item["boot_idx"]
        order = self.settings["boot_order"]
        dev = order[idx]
        if dev.startswith("[Disabled] "):
            order[idx] = dev[len("[Disabled] "):]
        else:
            order[idx] = f"[Disabled] {dev}"
        self.switch_tab("Boot")
        for i, it in enumerate(self.ui_items):
            if it.get("type") == "boot_item" and it.get("boot_idx") == idx:
                self.current_item_index = i
                self._update_visuals()
                break

    # ── Main tab actions ──────────────────────────────────────────────────────
    def _edit_time(self):
        t = simpledialog.askstring("System Time", "Enter new time (HH:MM:SS):",
            initialvalue=time.strftime('%H:%M:%S'), parent=self.root)
        if t:
            parts = t.strip().split(":")
            if len(parts) == 3:
                try:
                    h,m,s = int(parts[0]),int(parts[1]),int(parts[2])
                    assert 0<=h<24 and 0<=m<60 and 0<=s<60
                    if platform.system() == "Windows":
                        try: subprocess.run(f'time {h:02d}:{m:02d}:{s:02d}', shell=True, check=False)
                        except: pass
                    messagebox.showinfo("System Time", f"Time set to {h:02d}:{m:02d}:{s:02d}.")
                    self.switch_tab("Main")
                except (ValueError, AssertionError):
                    messagebox.showerror("Invalid Time", "Please enter a valid time HH:MM:SS.")

    def _edit_date(self):
        d = simpledialog.askstring("System Date", "Enter new date (MM/DD/YYYY):",
            initialvalue=time.strftime('%m/%d/%Y'), parent=self.root)
        if d:
            parts = d.strip().split("/")
            if len(parts) == 3:
                try:
                    m,dy,y = int(parts[0]),int(parts[1]),int(parts[2])
                    assert 1<=m<=12 and 1<=dy<=31 and 1900<=y<=2099
                    if platform.system() == "Windows":
                        try: subprocess.run(f'date {m:02d}-{dy:02d}-{y}', shell=True, check=False)
                        except: pass
                    messagebox.showinfo("System Date", f"Date set to {m:02d}/{dy:02d}/{y}.")
                    self.switch_tab("Main")
                except (ValueError, AssertionError):
                    messagebox.showerror("Invalid Date", "Please enter a valid date MM/DD/YYYY.")

    # ── Security actions ──────────────────────────────────────────────────────
    def _set_password(self, role):
        stored_key = "supervisor_pw" if role == "Supervisor" else "user_pw"
        stored = self.settings.get(stored_key, "")
        if stored:
            old = simpledialog.askstring(f"{role} Password",
                "Enter current password to change/clear:", show="*", parent=self.root)
            if old is None: return
            if sha256(old) != stored:
                messagebox.showerror("Error", "Incorrect current password.")
                return
        pw1 = simpledialog.askstring(f"{role} Password",
            "Enter new password (blank = clear):", show="*", parent=self.root)
        if pw1 is None: return
        if pw1:
            pw2 = simpledialog.askstring(f"{role} Password",
                "Confirm new password:", show="*", parent=self.root)
            if pw2 is None: return
            if pw1 != pw2:
                messagebox.showerror("Mismatch", "Passwords do not match.")
                return
            self.settings[stored_key] = sha256(pw1)
            messagebox.showinfo("Password Set", f"{role} password has been set.")
        else:
            self.settings[stored_key] = ""
            messagebox.showinfo("Password Cleared", f"{role} password has been cleared.")
        self.switch_tab("Security")

    def _set_supervisor_pw(self): self._set_password("Supervisor")
    def _set_user_pw(self):
        sp = self.settings.get("supervisor_pw","")
        if sp:
            entered = simpledialog.askstring("Authorization",
                "Enter Supervisor Password to manage User PW:", show="*", parent=self.root)
            if entered is None or sha256(entered) != sp:
                messagebox.showerror("Access Denied", "Incorrect supervisor password.")
                return
        self._set_password("User")

    # ── Update tab actions ────────────────────────────────────────────────────
    def _show_flash_advice(self):
        messagebox.showinfo("BIOS Flashing Guide",
            "Standard BIOS Flashing Procedure:\n\n"
            "Step 1: Identify your exact motherboard model and current BIOS version.\n"
            "Step 2: Download the correct BIOS update from the manufacturer's official support page.\n"
            "Step 3: Format an empty USB flash drive to FAT32.\n"
            "Step 4: Extract the downloaded BIOS file (.CAP, .ROM) to the root of the USB drive.\n"
            "Step 5: Restart into BIOS and navigate to the Update / EZ-Flash utility.\n"
            "Step 6: Select your USB drive, choose the BIOS file, and confirm.\n"
            "Step 7: Wait 3-5 minutes — do NOT power off!\n\n"
            "CRITICAL WARNING: Never turn off the PC during a BIOS flash. This will permanently brick the motherboard!",
            parent=self.root)

    def _scan_usb_drives(self):
        msg = ("Found USB Drive: 'KINGSTON_16GB' (FAT32)\n"
               "Found update file: 'PHX_X99_V7.CAP'\n\n"
               "Would you like to select this file for the update?")
        if messagebox.askyesno("USB Drive Detected", msg, parent=self.root):
            self.selected_bios_file = "PHX_X99_V7.CAP"
            messagebox.showinfo("Selected", "File successfully loaded from USB.", parent=self.root)
            self.switch_tab("Update")

    def _start_bios_flash(self):
        if self.selected_bios_file == "None":
            messagebox.showerror("No File", "Please select an update file from a USB drive first.", parent=self.root)
            return
        warn_msg = ("CRITICAL WARNING!\n\nYou are about to flash the BIOS. DO NOT turn off or reset the system "
                    "during this process. A power loss may permanently brick the motherboard.\n\n"
                    "Are you completely sure you want to proceed?")
        if not messagebox.askyesno("Confirm BIOS Flash", warn_msg, parent=self.root, icon='warning'):
            return
        self.in_bios_ui = False
        if self.clock_job:
            self.root.after_cancel(self.clock_job)
            self.clock_job = None
        for w in self.root.winfo_children(): w.destroy()
        self.root.configure(bg=PHX_BLACK)
        f = tk.Frame(self.root, bg=PHX_BLACK)
        f.pack(fill="both", expand=True, padx=50, pady=100)
        tk.Label(f, text="PHOENIX EZ FLASH UTILITY", fg=PHX_WHITE, bg=PHX_BLUE,
                 font=("Consolas", 24, "bold"), padx=20, pady=10).pack(pady=40)
        tk.Label(f, text="WARNING: DO NOT TURN OFF POWER OR RESTART THE SYSTEM!",
                 fg=PHX_RED, bg=PHX_BLACK, font=("Consolas", 16, "bold")).pack(pady=10)
        self.flash_progress_var = tk.StringVar(value="Erasing Flash Block... 0%")
        tk.Label(f, textvariable=self.flash_progress_var, fg=PHX_YELLOW, bg=PHX_BLACK,
                 font=("Consolas", 14)).pack(pady=30)
        self.pb_canvas = tk.Canvas(f, width=600, height=30, bg=PHX_BLACK,
                                   highlightthickness=2, highlightbackground=PHX_WHITE)
        self.pb_canvas.pack()
        self.pb_rect = self.pb_canvas.create_rectangle(0, 0, 0, 30, fill=PHX_CYAN)
        self.flash_step = 0
        self._do_flash_step()

    def _do_flash_step(self):
        self.flash_step += 1
        pct = self.flash_step
        self.pb_canvas.coords(self.pb_rect, 0, 0, pct * 6, 30)
        if pct < 25:   self.flash_progress_var.set(f"Erasing Flash Block... {pct}%")
        elif pct < 85: self.flash_progress_var.set(f"Writing New BIOS Image... {pct}%")
        else:          self.flash_progress_var.set(f"Verifying Integrity... {pct}%")
        if pct < 100:
            self.root.after(80, self._do_flash_step)
        else:
            self.flash_progress_var.set("Update Complete! System will automatically reboot.")
            self.settings["bios_flashed"] = True
            self.save_cmos()
            self.collect_system_info()
            self.root.after(3000, self.restart_system)

    # ═══════════════════════════════════════════════════════════════════════════
    #  UNIVERSAL DIAGNOSTIC ENGINE
    # ═══════════════════════════════════════════════════════════════════════════
    def build_diagnostic_report(self):
        """
        Analyses ALL settings vs defaults and SETTING_META.
        Returns: (changed_items, risky_unchanged, compat_results, overall_risk)
        """
        default = DEFAULT_SETTINGS
        cur     = self.settings

        changed_items    = []   # settings that differ from default
        risky_unchanged  = []   # settings at default that have noteworthy info
        compat_results   = []   # compatibility checklist results

        # ── Analyse each setting with metadata ──
        for key, meta in SETTING_META.items():
            if key not in cur: continue
            cur_val     = cur[key]
            default_val = default.get(key)
            is_changed  = (cur_val != default_val)

            # Determine description for this value
            effects = meta.get("effects", {})
            dyn_note = meta.get("_dynamic_note")

            if cur_val in effects:
                risk, short, long_desc = effects[cur_val]
            elif dyn_note and cur_val != "Auto":
                risk      = dyn_note[0]
                short     = f"Manually set to {cur_val}"
                long_desc = dyn_note[1]
            else:
                risk      = "safe"
                short     = f"Set to {cur_val}"
                long_desc = ""

            entry = {
                "key":      key,
                "name":     meta["name"],
                "category": meta["category"],
                "value":    cur_val,
                "default":  default_val,
                "risk":     risk,
                "short":    short,
                "detail":   long_desc,
                "changed":  is_changed,
            }

            if is_changed:
                changed_items.append(entry)
            elif risk in ("danger","caution") and long_desc:
                # Even unchanged risky settings deserve a note
                risky_unchanged.append(entry)

        # ── Run compatibility checklist ──
        for rule in COMPAT_RULES:
            try:
                passed = rule["check"](cur)
            except Exception:
                passed = True
            compat_results.append({
                "label":    rule["label"],
                "passed":   passed,
                "msg":      rule["pass_msg"] if passed else rule["fail_msg"],
                "severity": rule["severity"],
            })

        # ── Overall risk ──
        risks = [e["risk"] for e in changed_items]
        if "danger" in risks:
            overall = "danger"
        elif "caution" in risks:
            overall = "caution"
        else:
            overall = "safe"

        return changed_items, risky_unchanged, compat_results, overall

    def show_diagnostic_report(self):
        """Full diagnostic report window shown after Save."""
        changed, risky_unch, compat, overall = self.build_diagnostic_report()

        win = tk.Toplevel(self.root)
        win.title("BIOS Diagnostic Report")
        win.geometry("980x780")
        win.configure(bg=PHX_BLACK)
        win.grab_set()

        # Header bar
        header_bg = {"safe": "#005500", "caution": "#554400", "danger": "#550000"}[overall]
        header_fg = {"safe": PHX_GREEN, "caution": PHX_YELLOW, "danger": PHX_RED}[overall]
        header_txt = {"safe": "✔  ALL SETTINGS — LOW RISK",
                      "caution": "⚠  REPORT COMPLETE — REVIEW CAUTION ITEMS",
                      "danger": "✖  REPORT COMPLETE — DANGER ITEMS DETECTED"}[overall]

        tk.Label(win, text="PhoenixBIOS — CMOS Save & Diagnostic Report",
                 fg=PHX_CYAN, bg=PHX_BLACK, font=FONT_TITLE).pack(pady=(10,2))
        tk.Label(win, text=header_txt, fg=header_fg, bg=header_bg,
                 font=FONT_TITLE, pady=6).pack(fill="x")

        # Main scrollable content
        outer = tk.Frame(win, bg=PHX_BLACK)
        outer.pack(fill="both", expand=True, padx=8, pady=6)
        canvas = tk.Canvas(outer, bg=PHX_BLACK, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=PHX_BLACK)
        canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        def section(title, color=PHX_CYAN):
            tk.Label(inner, text=title, fg=color, bg=PHX_BLACK,
                     font=FONT_MAIN, anchor="w").pack(fill="x", padx=8, pady=(14,2))
            tk.Frame(inner, bg=color, height=1).pack(fill="x", padx=8)

        def risk_card(entry):
            risk   = entry["risk"]
            bg_map = {"safe":"#001a00","caution":"#1a1400","danger":"#1a0000","info":"#00001a"}
            fg_map = {"safe":PHX_GREEN,"caution":PHX_YELLOW,"danger":PHX_RED,"info":PHX_CYAN}
            icon   = {"safe":"✔","caution":"⚠","danger":"✖","info":"ℹ"}
            bg = bg_map.get(risk,"#0a0a0a")
            fg = fg_map.get(risk, PHX_WHITE)
            ic = icon.get(risk,"·")

            card = tk.Frame(inner, bg=bg, bd=1, relief="solid", padx=10, pady=6)
            card.pack(fill="x", padx=12, pady=3)

            # Title row
            title_row = tk.Frame(card, bg=bg)
            title_row.pack(fill="x")
            tk.Label(title_row, text=f"{ic} {entry['name']}", fg=fg, bg=bg,
                     font=FONT_MAIN, anchor="w").pack(side="left")
            if entry.get("changed"):
                tk.Label(title_row,
                         text=f"  {entry['default']}  →  {entry['value']}",
                         fg=PHX_WHITE, bg=bg, font=FONT_MAIN).pack(side="left", padx=12)

            # Category + short
            tk.Label(card, text=f"  Category: {entry['category']}   |   {entry['short']}",
                     fg="#aaaaaa", bg=bg, font=FONT_SMALL, anchor="w").pack(fill="x")

            # Long detail
            if entry.get("detail"):
                detail_frame = tk.Frame(card, bg=bg)
                detail_frame.pack(fill="x", pady=(4,0))
                tk.Label(detail_frame,
                         text=entry["detail"],
                         fg="#dddddd", bg=bg, font=("Consolas", 9),
                         wraplength=880, justify="left", anchor="nw").pack(fill="x")

        # ── SECTION 1: Changed settings ──
        if changed:
            section(f"  Changed Settings  ({len(changed)} change{'s' if len(changed)!=1 else ''} from factory default)")
            for entry in sorted(changed, key=lambda x: {"danger":0,"caution":1,"safe":2,"info":3}.get(x["risk"],4)):
                risk_card(entry)
        else:
            section("  Changed Settings")
            tk.Label(inner, text="  No settings have been changed from factory defaults.",
                     fg=PHX_GREEN, bg=PHX_BLACK, font=FONT_MAIN).pack(anchor="w", padx=16, pady=4)

        # ── SECTION 2: All settings status ──
        section("  All Settings — Current Status")
        all_entries = []
        for key, meta in SETTING_META.items():
            if key not in self.settings: continue
            cur_val = self.settings[key]
            effects = meta.get("effects", {})
            dyn_note = meta.get("_dynamic_note")
            if cur_val in effects:
                risk, short, detail = effects[cur_val]
            elif dyn_note and cur_val != "Auto":
                risk, short, detail = dyn_note[0], f"Manually set to {cur_val}", dyn_note[1]
            else:
                risk, short, detail = "safe", f"Set to {cur_val}", ""
            all_entries.append({
                "key":key,"name":meta["name"],"category":meta["category"],
                "value":cur_val,"default":DEFAULT_SETTINGS.get(key),
                "risk":risk,"short":short,"detail":detail,
                "changed": cur_val != DEFAULT_SETTINGS.get(key),
            })
        # Group by category
        categories = {}
        for e in all_entries:
            categories.setdefault(e["category"], []).append(e)
        for cat, entries in sorted(categories.items()):
            tk.Label(inner, text=f"  ─── {cat} ───",
                     fg=PHX_YELLOW, bg=PHX_BLACK, font=FONT_SMALL_BOLD, anchor="w").pack(fill="x", padx=16, pady=(8,0))
            for entry in entries:
                risk_card(entry)

        # ── SECTION 3: Risky unchanged ──
        if risky_unchanged:
            section("  Risky Default Settings — Worth Knowing", PHX_YELLOW)
            tk.Label(inner,
                     text="  These settings are at factory default but carry real-world risks you should be aware of:",
                     fg="#aaaaaa", bg=PHX_BLACK, font=FONT_SMALL).pack(anchor="w", padx=16)
            for entry in risky_unchanged:
                risk_card(entry)

        # ── SECTION 4: Compatibility checklist ──
        section("  Compatibility Checklist")
        fails = [r for r in compat if not r["passed"] and r["severity"]=="fail"]
        warns = [r for r in compat if not r["passed"] and r["severity"]=="warn"]
        passes= [r for r in compat if r["passed"]]

        for r in fails:
            f = tk.Frame(inner, bg="#1a0000", bd=1, relief="solid", padx=10, pady=4)
            f.pack(fill="x", padx=12, pady=2)
            tk.Label(f, text=f"✖  {r['label']}", fg=PHX_RED, bg="#1a0000", font=FONT_MAIN, anchor="w").pack(fill="x")
            tk.Label(f, text=f"   {r['msg']}", fg="#dddddd", bg="#1a0000", font=("Consolas",9),
                     wraplength=880, justify="left", anchor="w").pack(fill="x")
        for r in warns:
            f = tk.Frame(inner, bg="#1a1400", bd=1, relief="solid", padx=10, pady=4)
            f.pack(fill="x", padx=12, pady=2)
            tk.Label(f, text=f"⚠  {r['label']}", fg=PHX_YELLOW, bg="#1a1400", font=FONT_MAIN, anchor="w").pack(fill="x")
            tk.Label(f, text=f"   {r['msg']}", fg="#dddddd", bg="#1a1400", font=("Consolas",9),
                     wraplength=880, justify="left", anchor="w").pack(fill="x")
        for r in passes:
            f = tk.Frame(inner, bg="#001a00", bd=1, relief="solid", padx=10, pady=3)
            f.pack(fill="x", padx=12, pady=1)
            tk.Label(f, text=f"✔  {r['label']}  —  {r['msg']}",
                     fg=PHX_GREEN, bg="#001a00", font=FONT_SMALL, anchor="w").pack(fill="x")

        # Footer summary
        tk.Frame(inner, bg=PHX_CYAN, height=1).pack(fill="x", padx=8, pady=(16,4))
        num_danger  = sum(1 for e in changed if e["risk"]=="danger")
        num_caution = sum(1 for e in changed if e["risk"]=="caution")
        num_safe    = sum(1 for e in changed if e["risk"]=="safe")
        num_fail    = len(fails)
        num_warn    = len(warns)
        summary = (f"  Summary:  {len(changed)} setting(s) changed  |  "
                   f"Danger: {num_danger}  Caution: {num_caution}  Safe: {num_safe}  |  "
                   f"Compat fails: {num_fail}  Warnings: {num_warn}")
        tk.Label(inner, text=summary, fg=PHX_WHITE, bg=PHX_BLACK,
                 font=FONT_MAIN, anchor="w").pack(fill="x", padx=8, pady=4)

        # Close button
        btn_f = tk.Frame(win, bg=PHX_BLACK)
        btn_f.pack(pady=8, side="bottom")
        tk.Button(btn_f, text="  Close & Reboot  ", font=FONT_MAIN,
                  bg=PHX_WHITE, fg=PHX_BLACK, command=win.destroy, bd=2).pack(side="left", padx=10)
        tk.Button(btn_f, text="  Back to BIOS  ", font=FONT_MAIN,
                  bg=PHX_GREY, fg=PHX_BLACK,
                  command=lambda: [win.destroy(), self.load_bios_ui()]).pack(side="left", padx=10)

    # ── Global actions ────────────────────────────────────────────────────────
    def global_save_exit(self, event=None):
        if not self.in_bios_ui: return
        if messagebox.askyesno("Save & Diagnose",
                               "Save configuration and open full diagnostic report?",
                               parent=self.root):
            self.save_cmos()
            self.in_bios_ui = False
            if self.clock_job:
                self.root.after_cancel(self.clock_job)
            if self.hw_job:
                self.root.after_cancel(self.hw_job)
            self.show_diagnostic_report()

    def global_exit(self, event=None):
        if not self.in_bios_ui: return
        if messagebox.askyesno("Exit Without Saving", "Discard changes and exit?", parent=self.root):
            self.discard_cmos()
            self.in_bios_ui = False
            if self.clock_job: self.root.after_cancel(self.clock_job)
            if self.hw_job:    self.root.after_cancel(self.hw_job)
            self.restart_system()

    def load_defaults(self, event=None):
        if not self.in_bios_ui: return
        if messagebox.askyesno("Load Defaults",
                               "Load factory default settings?\n(Not saved until F10.)", parent=self.root):
            sv = self.settings.get("supervisor_pw","")
            uv = self.settings.get("user_pw","")
            self.settings = deepcopy(DEFAULT_SETTINGS)
            self.settings["supervisor_pw"] = sv
            self.settings["user_pw"]       = uv
            self.switch_tab(self.tabs[self.current_tab_index])
            messagebox.showinfo("Defaults Loaded", "Factory defaults loaded.\nPress F10 to commit.", parent=self.root)

    def _load_optimal_defaults(self):
        if messagebox.askyesno("Optimal Defaults", "Load optimised performance defaults?", parent=self.root):
            sv = self.settings.get("supervisor_pw","")
            uv = self.settings.get("user_pw","")
            self.settings = deepcopy(DEFAULT_SETTINGS)
            self.settings["supervisor_pw"] = sv
            self.settings["user_pw"]       = uv
            self.settings["sata_mode"]       = "AHCI"
            self.settings["virtualization"]  = "Enabled"
            self.settings["hyperthreading"]  = "Enabled"
            self.settings["ram_xmp"]         = "Profile 1"
            self.settings["above_4g_decoding"] = "Enabled"
            self.settings["resizable_bar"]   = "Enabled"
            self.switch_tab(self.tabs[self.current_tab_index])

    def _discard_changes_only(self):
        if messagebox.askyesno("Discard Changes", "Reload last-saved CMOS values?", parent=self.root):
            self.discard_cmos()
            self.switch_tab(self.tabs[self.current_tab_index])
            messagebox.showinfo("Reverted", "Settings reverted to last saved values.", parent=self.root)

    def _save_changes_only(self):
        self.save_cmos()
        messagebox.showinfo("Saved", "Settings saved to CMOS.", parent=self.root)

    # ── Lab scenarios ─────────────────────────────────────────────────────────
    def _lab_scenario1(self):
        self.settings["boot_mode"]   = "Legacy"
        self.settings["secure_boot"] = "Disabled"
        self.settings["tpm_state"]   = "Disabled"
        self.current_scenario = 1
        self.switch_tab("Lab")
        messagebox.showinfo("Scenario 1 — Windows 11 Won't Install",
            "❌ Error: 'This PC can't run Windows 11'\n\n"
            "Fix required:\n"
            "  • Security tab → Secure Boot: Enabled\n"
            "  • Security tab → TPM State: Enabled\n"
            "  • Power tab → Boot Mode: UEFI\n\n"
            "Verify on the Lab tab when done.", parent=self.root)

    def _lab_scenario2(self):
        order = self.settings["boot_order"]
        if "Network: LAN PXE Boot" in order: order.remove("Network: LAN PXE Boot")
        order.insert(0, "Network: LAN PXE Boot")
        self.current_scenario = 2
        self.switch_tab("Lab")
        messagebox.showinfo("Scenario 2 — PXE Boot Loop",
            "❌ Error: 'PXE-E61: Media test failure, check cable'\n\n"
            "Fix required:\n"
            "  • Boot tab → Move 'HDD: Windows Boot Manager' to position 1\n"
            "    (select it, press + to move up)\n\n"
            "Verify on the Lab tab when done.", parent=self.root)

    def _lab_scenario3(self):
        self.settings["sata_mode"] = "IDE"
        self.current_scenario = 3
        self.switch_tab("Lab")
        messagebox.showinfo("Scenario 3 — Drive Not Detected",
            "❌ Problem: Windows cannot find the SATA hard drive\n\n"
            "Fix required:\n"
            "  • Power tab → SATA Mode: AHCI\n\n"
            "Verify on the Lab tab when done.", parent=self.root)

    def _lab_scenario4(self):
        self.settings["virtualization"] = "Disabled"
        self.current_scenario = 4
        self.switch_tab("Lab")
        messagebox.showinfo("Scenario 4 — VM Error",
            "❌ Error: 'VT-x is not available (VERR_VMX_NO_VMX)'\n\n"
            "Fix required:\n"
            "  • Power tab → Virtualization: Enabled\n\n"
            "Verify on the Lab tab when done.", parent=self.root)

    def _lab_scenario5(self):
        self.settings["tpm_state"]   = "Disabled"
        self.settings["secure_boot"] = "Disabled"
        self.current_scenario = 5
        self.switch_tab("Lab")
        messagebox.showinfo("Scenario 5 — BitLocker Recovery Key Loop",
            "❌ Problem: Windows asks for the 48-digit BitLocker recovery key on every boot.\n\n"
            "Fix required:\n"
            "  • Security tab → TPM State: Enabled\n"
            "  • Security tab → Secure Boot: Enabled\n\n"
            "Verify on the Lab tab when done.", parent=self.root)

    def _lab_scenario6(self):
        self.settings["ram_xmp"]  = "Disabled"
        self.settings["ram_freq"] = "Auto"
        self.current_scenario = 6
        self.switch_tab("Lab")
        messagebox.showinfo("Scenario 6 — RAM Running at Wrong Speed",
            "❌ Problem: Your DDR4-3200 RAM kit is running at only 2133 MHz.\n\n"
            "Fix required:\n"
            "  • Overclock tab → XMP / DOCP: Profile 1\n\n"
            "Verify on the Lab tab when done.", parent=self.root)

    def _lab_scenario7(self):
        self.settings["above_4g_decoding"] = "Disabled"
        self.settings["resizable_bar"]     = "Disabled"
        self.current_scenario = 7
        self.switch_tab("Lab")
        messagebox.showinfo("Scenario 7 — GPU VRAM Not Fully Accessible",
            "❌ Problem: RTX 4080 (16GB) only shows ~4GB usable VRAM in Task Manager.\n\n"
            "Fix required:\n"
            "  • PCI/Onboard tab → Above 4G Decoding: Enabled\n"
            "  • PCI/Onboard tab → Resizable BAR: Enabled\n\n"
            "Verify on the Lab tab when done.", parent=self.root)

    def _lab_scenario8(self):
        self.settings["cpu_multiplier"] = "52x"
        self.settings["cpu_voltage"]    = "1.400V"
        self.settings["cpu_fan_ctrl"]   = "Silent"
        self.current_scenario = 8
        self.switch_tab("Lab")
        messagebox.showinfo("Scenario 8 — CPU Overheating During OC",
            "❌ Problem: System crashes and throttles under load after overclocking.\n\n"
            "Current dangerous config:\n"
            "  CPU Multiplier = 52x  (overclocked)\n"
            "  CPU Voltage    = 1.400V  (very high)\n"
            "  CPU Fan        = Silent  (minimal cooling)\n\n"
            "Fix required:\n"
            "  • Overclock tab → CPU Fan Control: Auto or Full Speed\n"
            "  (In a real fix you'd also reduce voltage or multiplier)\n\n"
            "Verify on the Lab tab when done.", parent=self.root)

    def _lab_verify(self):
        if not self.current_scenario:
            messagebox.showinfo("No Scenario", "No active scenario loaded.", parent=self.root)
            return
        ok = False
        fail_msg = ""
        s = self.settings
        if self.current_scenario == 1:
            ok = (s["boot_mode"]=="UEFI" and s["secure_boot"]=="Enabled" and s["tpm_state"]=="Enabled")
            fail_msg = (f"Boot Mode: {s['boot_mode']} (need UEFI)\n"
                        f"Secure Boot: {s['secure_boot']} (need Enabled)\n"
                        f"TPM: {s['tpm_state']} (need Enabled)")
        elif self.current_scenario == 2:
            first = s["boot_order"][0]
            ok = "HDD" in first and not first.startswith("[Disabled]")
            fail_msg = f"First boot device: {first}\n(HDD must be first)"
        elif self.current_scenario == 3:
            ok = s["sata_mode"] == "AHCI"
            fail_msg = f"SATA Mode: {s['sata_mode']} (need AHCI)"
        elif self.current_scenario == 4:
            ok = s["virtualization"] == "Enabled"
            fail_msg = f"Virtualization: {s['virtualization']} (need Enabled)"
        elif self.current_scenario == 5:
            ok = s["tpm_state"]=="Enabled" and s["secure_boot"]=="Enabled"
            fail_msg = (f"TPM: {s['tpm_state']} (need Enabled)\n"
                        f"Secure Boot: {s['secure_boot']} (need Enabled)")
        elif self.current_scenario == 6:
            ok = s["ram_xmp"] in ("Profile 1","Profile 2")
            fail_msg = f"XMP Profile: {s['ram_xmp']} (need Profile 1 or 2)"
        elif self.current_scenario == 7:
            ok = s["above_4g_decoding"]=="Enabled" and s["resizable_bar"]=="Enabled"
            fail_msg = (f"Above 4G Decoding: {s['above_4g_decoding']} (need Enabled)\n"
                        f"Resizable BAR: {s['resizable_bar']} (need Enabled)")
        elif self.current_scenario == 8:
            ok = s["cpu_fan_ctrl"] in ("Auto","Full Speed")
            fail_msg = f"CPU Fan: {s['cpu_fan_ctrl']} (need Auto or Full Speed)"

        if ok:
            messagebox.showinfo("✅ Correct!",
                f"Scenario {self.current_scenario} solved!\n\n"
                "Well done! The configuration is now correct.\n"
                "Remember to press F10 to save and see the full diagnostic report.",
                parent=self.root)
            self.current_scenario = None
            self.switch_tab("Lab")
        else:
            messagebox.showerror("❌ Not Yet",
                f"Scenario {self.current_scenario} not resolved yet.\n\n{fail_msg}",
                parent=self.root)

    def _lab_clear(self):
        self.current_scenario = None
        self.settings = deepcopy(DEFAULT_SETTINGS)
        self.switch_tab("Lab")
        messagebox.showinfo("Cleared", "Scenario cleared. Settings restored to defaults.", parent=self.root)

    # ── Boot config validation ────────────────────────────────────────────────
    def validate_bios_configuration(self):
        errors = []
        warnings = []
        s = self.settings
        is_win11 = "Windows 11" in self.sys_info.get("os","")
        if is_win11:
            if s["boot_mode"] != "UEFI":   errors.append("Windows 11 requires UEFI Boot Mode.")
            if s["secure_boot"] != "Enabled": errors.append("Windows 11 requires Secure Boot.")
            if s["tpm_state"] != "Enabled":   errors.append("Windows 11 requires TPM Enabled.")
        if s["secure_boot"]=="Enabled" and s["boot_mode"]=="Legacy":
            errors.append("Secure Boot + Legacy Boot Mode conflict detected.")
        order = s["boot_order"]
        if order:
            first = order[0]
            if first.startswith("[Disabled]"):
                errors.append(f"First boot device is disabled: {first}")
            elif "Network" in first:
                warnings.append("First boot device is Network PXE — will cause delay if no server.")
        if s["pw_on_boot"]=="Enabled" and not s["user_pw"]:
            warnings.append("Password-on-Boot enabled but no User Password is set.")
        if s["sata_mode"] == "IDE":
            warnings.append("SATA Mode is IDE — AHCI recommended for modern drives.")
        if s.get("cpu_voltage","Auto") != "Auto" and s.get("cpu_fan_ctrl","Auto") == "Silent":
            errors.append("CPU voltage is manually elevated but fan control is Silent — overheating risk.")
        if s.get("resizable_bar","Disabled") == "Enabled" and s.get("above_4g_decoding","Disabled") == "Disabled":
            warnings.append("Resizable BAR requires Above 4G Decoding to be Enabled.")
        return errors, warnings

    # ── OS Boot sequence ──────────────────────────────────────────────────────
    def attempt_os_boot(self):
        self.post_active = False
        self.bios_opportunity = False
        try: self.post_frame.destroy()
        except: pass
        errors, warnings = self.validate_bios_configuration()
        if errors:
            self.show_error_screen(errors, warnings)
            return
        if self.settings.get("pw_on_boot")=="Enabled" and self.settings.get("user_pw"):
            entered = simpledialog.askstring("System Password", "Enter password to boot:", show="*", parent=self.root)
            if entered is None or sha256(entered) != self.settings["user_pw"]:
                messagebox.showerror("Access Denied", "Incorrect password. System halted.")
                self.restart_system()
                return
        self._show_boot_loading()

    def show_error_screen(self, errors, warnings=None):
        for w in self.root.winfo_children(): w.destroy()
        self.root.configure(bg=PHX_BLACK)
        f = tk.Frame(self.root, bg=PHX_BLACK)
        f.pack(fill="both", expand=True, padx=50, pady=40)
        tk.Label(f, text="■ SYSTEM CONFIGURATION ERROR", fg=PHX_RED, bg=PHX_BLACK,
                 font=("Consolas", 18, "bold")).pack(anchor="w", pady=(0,10))
        tk.Label(f, text="System cannot boot due to the following issues:",
                 fg=PHX_WHITE, bg=PHX_BLACK, font=FONT_MAIN).pack(anchor="w", pady=(0,10))
        for err in errors:
            tk.Label(f, text=f"  ✖  {err}", fg=PHX_YELLOW, bg=PHX_BLACK, font=FONT_MAIN).pack(anchor="w", pady=2)
        if warnings:
            tk.Label(f, text="", bg=PHX_BLACK).pack()
            tk.Label(f, text="Warnings:", fg=PHX_CYAN, bg=PHX_BLACK, font=FONT_MAIN).pack(anchor="w")
            for w in warnings:
                tk.Label(f, text=f"  ⚠  {w}", fg=PHX_CYAN, bg=PHX_BLACK, font=FONT_SMALL).pack(anchor="w", pady=1)
        tk.Label(f, text="\nPress F2 / Del to enter BIOS Setup and fix the issues above.",
                 fg=PHX_WHITE, bg=PHX_BLACK, font=FONT_MAIN).pack(pady=20)
        btn_frame = tk.Frame(f, bg=PHX_BLACK)
        btn_frame.pack()
        tk.Button(btn_frame, text="  Enter BIOS Setup  ", command=self._enter_bios_from_error,
                  bg=PHX_WHITE, fg=PHX_BLACK, font=FONT_MAIN, bd=2).pack(side="left", padx=10)
        tk.Button(btn_frame, text="  Restart  ", command=self.restart_system,
                  bg=PHX_GREY, fg=PHX_BLACK, font=FONT_MAIN).pack(side="left", padx=10)
        self.root.bind('<F2>', lambda e: self._enter_bios_from_error())
        self.root.bind('<Delete>', lambda e: self._enter_bios_from_error())

    def _enter_bios_from_error(self):
        self.root.bind('<F2>', self.on_bios_key)
        self.root.bind('<Delete>', self.on_bios_key)
        self.in_bios_ui = True
        self.load_bios_ui()

    def _show_boot_loading(self):
        for w in self.root.winfo_children(): w.destroy()
        self.root.configure(bg=PHX_BLACK)
        self.boot_canvas = tk.Canvas(self.root, width=1100, height=800, bg=PHX_BLACK, highlightthickness=0)
        self.boot_canvas.pack(fill="both", expand=True)
        cx, cy = 550, 360
        sz, gap = 70, 5
        colours = ["#F25022","#7FBA00","#00A4EF","#FFB900"]
        positions = [
            (cx-sz-gap, cy-sz-gap, cx-gap, cy-gap),
            (cx+gap,    cy-sz-gap, cx+sz+gap, cy-gap),
            (cx-sz-gap, cy+gap,    cx-gap, cy+sz+gap),
            (cx+gap,    cy+gap,    cx+sz+gap, cy+sz+gap),
        ]
        for col, pos in zip(colours, positions):
            self.boot_canvas.create_rectangle(*pos, fill=col, outline="")
        self.spinner_step = 0
        self._animate_spinner(self.boot_canvas, cx, cy + 140)
        self.root.after(3500, self._show_lock_screen)

    def _animate_spinner(self, cv, cx, cy):
        try:
            if not cv.winfo_exists() or cv is not self.boot_canvas: return
        except: return
        cv.delete("spinner")
        n, r = 5, 22
        for i in range(n):
            angle = math.radians(self.spinner_step + i * (360 / n))
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            size = 4 + (i % 2) * 2
            alpha = 255 - int(200 * (n-1-i) / n)
            grey = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
            cv.create_oval(x-size, y-size, x+size, y+size, fill=grey, outline="", tags="spinner")
        self.spinner_step = (self.spinner_step + 18) % 360
        self.root.after(60, lambda: self._animate_spinner(cv, cx, cy))

    def _show_lock_screen(self):
        self.boot_canvas = None
        for w in self.root.winfo_children(): w.destroy()
        self.root.configure(bg=WIN_LOCK_BG)
        f = tk.Frame(self.root, bg=WIN_LOCK_BG)
        f.pack(fill="both", expand=True)
        now = datetime.now()
        tk.Label(f, text=now.strftime("%H:%M"), fg="white", bg=WIN_LOCK_BG, font=FONT_WIN_CLOCK).pack(pady=(90,5))
        tk.Label(f, text=now.strftime("%A, %d %B %Y"), fg="white", bg=WIN_LOCK_BG, font=FONT_WIN_DATE).pack()
        s = self.settings
        summary = (f"Boot Mode: {s['boot_mode']}  |  Secure Boot: {s['secure_boot']}  |  "
                   f"TPM: {s['tpm_state']}  |  SATA: {s['sata_mode']}  |  "
                   f"XMP: {s['ram_xmp']}  |  vCore: {s['cpu_voltage']}")
        tk.Label(f, text=summary, fg="#aaddff", bg=WIN_LOCK_BG, font=("Segoe UI", 10)).pack(pady=(5,0))
        tk.Label(f, text=self.sys_info.get("os","Windows"), fg="lightgrey", bg=WIN_LOCK_BG,
                 font=("Segoe UI", 12)).pack(pady=2)
        btn_f = tk.Frame(f, bg=WIN_LOCK_BG)
        btn_f.pack(side="bottom", pady=40)
        tk.Button(btn_f, text="  Log In  ", font=("Segoe UI",14), bg="white", fg="black",
                  padx=20, command=self._login_dialog).pack(side="left", padx=20)
        tk.Button(btn_f, text="  Restart  ", font=("Segoe UI",11), bg="#dddddd", fg="black",
                  command=self.restart_system).pack(side="left", padx=20)
        tk.Button(btn_f, text="  Enter BIOS  ", font=("Segoe UI",11), bg="#dddddd", fg="black",
                  command=self._enter_bios_from_lock).pack(side="left", padx=20)

    def _login_dialog(self):
        upw = self.settings.get("user_pw","")
        if upw:
            entered = simpledialog.askstring("Log In",
                f"Password for {self.sys_info.get('user','User')}:", show="*", parent=self.root)
            if entered is None or sha256(entered) != upw:
                messagebox.showerror("Login Failed", "Incorrect password.")
                return
        messagebox.showinfo("Welcome",
            f"Welcome, {self.sys_info.get('user','User')}!\n\nSystem booted successfully.", parent=self.root)

    def _enter_bios_from_lock(self):
        self.in_bios_ui = True
        self.load_bios_ui()

    def restart_system(self):
        self.boot_canvas = None
        self.in_bios_ui  = False
        if self.clock_job: self.root.after_cancel(self.clock_job); self.clock_job = None
        if self.hw_job:    self.root.after_cancel(self.hw_job);    self.hw_job    = None
        self.root.bind('<F2>', self.on_bios_key)
        self.root.bind('<Delete>', self.on_bios_key)
        self.start_system_power_on()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = BiosApp(root)
    root.mainloop()