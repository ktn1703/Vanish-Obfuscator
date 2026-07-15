<div align="center">
 
```

 ██▒   █▓ ▄▄▄       ███▄    █  ██▓  ██████  ██░ ██     ▄████▄   ██▓     █    ██  ▄▄▄▄   
▓██░   █▒▒████▄     ██ ▀█   █ ▓██▒▒██    ▒ ▓██░ ██▒   ▒██▀ ▀█  ▓██▒     ██  ▓██▒▓█████▄ 
 ▓██  █▒░▒██  ▀█▄  ▓██  ▀█ ██▒▒██▒░ ▓██▄   ▒██▀▀██░   ▒▓█    ▄ ▒██░    ▓██  ▒██░▒██▒ ▄██
  ▒██ █░░░██▄▄▄▄██ ▓██▒  ▐▌██▒░██░  ▒   ██▒░▓█ ░██    ▒▓▓▄ ▄██▒▒██░    ▓▓█  ░██░▒██░█▀  
   ▒▀█░   ▓█   ▓██▒▒██░   ▓██░░██░▒██████▒▒░▓█▒░██▓   ▒ ▓███▀ ░░██████▒▒▒█████▓ ░▓█  ▀█▓
   ░ ▐░   ▒▒   ▓▒█░░ ▒░   ▒ ▒ ░▓  ▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒   ░ ░▒ ▒  ░░ ▒░▓  ░░▒▓▒ ▒ ▒ ░▒▓███▀▒
   ░ ░░    ▒   ▒▒ ░░ ░░   ░ ▒░ ▒ ░░ ░▒  ░ ░ ▒ ░▒░ ░     ░  ▒   ░ ░ ▒  ░░░▒░ ░ ░ ▒░▒   ░ 
     ░░    ░   ▒      ░   ░ ░  ▒ ░░  ░  ░   ░  ░░ ░   ░          ░ ░    ░░░ ░ ░  ░    ░ 
      ░        ░  ░         ░  ░        ░   ░  ░  ░   ░ ░          ░  ░   ░      ░      
     ░                                                ░                               ░                                               
```

# VANISH v1.0

### Python Obfuscator | Next-Gen Protection

**Author:** KTN (Trương Nhật Bảo Nam)  
**Version:** 1.0  
**Status:** Public Release (Outdated)  
**GitHub:** [github.com/ktn1703/Vanish-Obfuscator](https://github.com/ktn1703/Vanish-Obfuscator)
**Discord:** [ktn1703](https://discord.com/users/1234144932176855040) or [ktn0755](https://discord.com/users/1524999162871943248)

---

*"Don't Read This Code Because You Will Be Dizzy By My Magic!"*

</div>

---

## ⚠️ Disclaimer

> **This is an outdated version of Vanish, released to the public.**  
> A more powerful successor has already been built — this version is no longer maintained.  
> Use at your own discretion. For educational and authorized security research purposes only.

---

## Overview

Vanish v1.0 is a **military-grade Python obfuscator** that transforms readable Python source code into virtually untraceable, tamper-proof bytecode. It combines a custom **Bytecode Virtual Machine (BVM)** with multi-layer cryptographic encryption and advanced anti-analysis techniques to create outputs that resist static analysis, decompilation, debugging, and reverse engineering.

---

## Features

### 🔒 BVM Engine (Bytecode Virtual Machine)
A fully custom virtual machine that lifts Python bytecode into a proprietary format. The original opcodes are **scrambled, encrypted, and reconstructed** at runtime — making traditional decompilers completely useless.

### 🛡️ 5-Layer Cryptographic Protection
Every payload is protected by five nested encryption layers, each using independently derived keys via **HKDF-SHA256**:

| Layer | Algorithm | Purpose |
|-------|-----------|---------|
| 1 | **Byte Shuffle** | Deterministic permutation of the entire payload |
| 2 | **XOR-Shift Stream** | Pseudo-random stream cipher with 64-bit state |
| 3 | **ChaCha20** | Authenticated stream cipher (10-round) |
| 4 | **AES-256-GCM** | Authenticated encryption with GHASH integrity |
| 5 | **zlib Compression** | Maximum compression (level 9) before encryption |

### 🧬 AST-Level Obfuscation
- **String Encryption** — 5 different XOR-based schemes (positional, reversed, split, RC4-like, modular addition)
- **Integer Obfuscation** — MBA (Mixed Boolean-Arithmetic) expressions, XOR decomposition, opaque predicates, trilinear transforms
- **Variable Renaming** — Confusable character pool (`I`, `l`, `1`, `O`, `0`) for maximum confusion
- **Control Flow Flattening** — Converts sequential logic into a state-machine `while/switch` pattern
- **Junk Code Injection** — 14–22 dead functions with opaque predicates and try/except noise

### 🔐 Anti-Analysis Arsenal

| Protection | What It Blocks |
|------------|----------------|
| **Anti-Debug** | `pdb`, `debugpy`, `pydevd`, `winpdb`, `frida`, VS Code / PyCharm debuggers |
| **Anti-Hook** | Function hooking, import interception, monkey-patching |
| **Anti-Frame** | Stack inspection, frame walking, file descriptor monitoring |
| **Anti-VM** | VMware, VirtualBox, QEMU, Hyper-V, Docker, Parallels, KVM |
| **Anti-Proxy** | mitmproxy, Charles, Fiddler, Burp Suite, HTTP Toolkit |
| **Anti-Decompiler** | Crashes `pycdc`, recursion bombs, corrupted marshal data |
| **Tamper Guard** | SHA-256 integrity checks, header validation, burn-on-modify |
| **Hardware Binding** | Optional machine-locked execution (HW fingerprint) |
| **Python Version Lock** | Optional lock to specific Python minor version |

### 🧊 Self-Destruct Mechanism
If any tampering, debugging, or hooking is detected, the program **immediately burns** — consuming all CPU cores, spawning infinite loops, and force-killing itself via `TerminateProcess` / `os._exit(137)`.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   SOURCE CODE                    │
└──────────────────────┬──────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │    AST Transformation    │
          │  ┌────────────────────┐  │
          │  │  Rename Variables  │  │
          │  │  Encrypt Strings   │  │
          │  │  Obfuscate Ints    │  │
          │  │  Inject Junk Code  │  │
          │  │  Flatten Control   │  │
          │  └────────────────────┘  │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   BVM Engine (bvm.py)   │
          │  ┌────────────────────┐  │
          │  │  Opcode Scramble   │  │
          │  │  Const Encryption  │  │
          │  │  Custom Packaging  │  │
          │  └────────────────────┘  │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │  5-Layer Crypto Chain   │
          │                         │
          │  Shuffle → XOR → ChaCha │
          │  → AES-GCM → Compress   │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   Loader Generation     │
          │  ┌────────────────────┐  │
          │  │  Anti-Debug        │  │
          │  │  Anti-Hook/VM      │  │
          │  │  Tamper Guards     │  │
          │  │  Self-Destruct     │  │
          │  └────────────────────┘  │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │     OUTPUT (.py)        │
          │   Obfuscated Payload    │
          └─────────────────────────┘
```

---

## Installation

### Requirements
- Python 3.8+
- Optional: [`pystyle`](https://pypi.org/project/pystyle/) (for colored terminal output)

### Setup
```bash
git clone https://github.com/ktn1703/Vanish-Obfuscator.git
cd Vanish-Obfuscator
pip install pystyle  # optional
```

---

## Usage

### Interactive Mode
```bash
python aevanish.py
```
The tool will guide you through a beautiful terminal interface with gradient banners and step-by-step prompts.

### Command-Line Mode
```bash
python aevanish.py --file input.py --output output.py
```

### CLI Options

| Flag | Description |
|------|-------------|
| `--file`, `-f` | Input Python file path |
| `--output`, `-o` | Output file path (default: `input_obf.py`) |
| `--no-anti-debug` | Disable anti-debug protection |
| `--no-anti-hook` | Disable anti-hook protection |
| `--no-anti-frame` | Disable anti-frame / GC wipe |
| `--no-junk` | Disable junk code injection |
| `--hw-bind` | Enable hardware-key binding |
| `--py-lock` | Lock to current Python version |
| `--no-anti-vm` | Disable anti-VM/sandbox detection |
| `--no-anti-proxy` | Disable anti-proxy/MITM detection |
| `--no-anti-httptoolkit` | Disable anti-HTTP Toolkit detection |
| `--no-anti-pydc` | Disable anti-decompiler crash |
| `--silent` | No output |
| `--banner` | Show banner |

### Example
```bash
python aevanish.py --file my_script.py --output protected.py --hw-bind
```

---

## Protection Summary

When you run Vanish, your output file will contain:

```
╔══════════════════════════════════════════════════════╗
║  ALWAYS ON                                         ║
║  ├── 5-Layer AES-GCM + ChaCha20 + XOR + Shuffle   ║
║  ├── HKDF-SHA256 Key Derivation                   ║
║  ├── BVM v8 Poly-Opcode Engine                     ║
║  ├── MBA Integer Obfuscation                       ║
║  ├── Multi-Scheme String Encryption                ║
║  └── Tamper-Burn Integrity Guard                   ║
║                                                    ║
║  CONFIGURABLE (all ON by default)                  ║
║  ├── Anti-Debug Detection                          ║
║  ├── Anti-Hook / Anti-Import                       ║
║  ├── Anti-Frame / Stack Inspection                 ║
║  ├── Anti-VM / Sandbox Evasion                     ║
║  ├── Anti-Proxy / MITM Detection                   ║
║  ├── Anti-HTTP Toolkit                             ║
║  ├── Anti-Decompiler Crash (pycdc)                 ║
║  ├── Junk Code Injection (14-22 dead functions)    ║
║  ├── Control Flow Flattening                       ║
║  ├── Hardware Binding (optional)                   ║
║  └── Python Version Lock (optional)                ║
╚══════════════════════════════════════════════════════╝
```

---

## File Structure

```
├── aevanish.py          # Main obfuscator (CLI, AST transforms, loader builder)
├── bvm_engine.py        # BVM bytecode virtual machine engine
└── README.md            # This file
```

---

## How It Works

1. **Parse** — Source is parsed into an AST (Abstract Syntax Tree)
2. **Transform** — Variables renamed, strings encrypted (5 schemes), integers obfuscated (MBA expressions), junk code injected, control flow flattened
3. **Lift** — Transformed AST is compiled and lifted into BVM's custom binary format with opcode scrambling
4. **Encrypt** — The BVM payload passes through 5 nested encryption layers with independently derived keys
5. **Wrap** — A self-protecting loader is generated containing anti-debug, anti-hook, tamper checks, and a self-destruct mechanism
6. **Output** — A single `.py` file that runs independently with zero dependencies

---

## Technical Details

### Crypto Implementation
All cryptographic primitives are implemented **from scratch** in pure Python with zero external dependencies:
- **AES-256-GCM** — Full S-Box, key expansion, GF(2^128) multiplication, GHASH
- **ChaCha20** — Quarter-round operations, 10-round block function
- **HKDF** — Extract-then-expand with SHA-256
- **XOR-Shift** — 64-bit state PRNG with configurable seed
- **Byte Shuffle** — Deterministic Fisher-Yates with SHA-256 seeded RNG

### BVM Engine
- Custom opcode scrambling with reverse-map restoration
- XOR-based code encryption with 64-bit seed
- Full constant pool serialization (ints, floats, complex, strings, bytes, tuples, lists, dicts, sets, code objects)
- Multi-version `CodeType` reconstruction for Python 3.8–3.12+

---

## Version History

| Version | Status |
|---------|--------|
| **v1.0** | This release — public, outdated |
| **v2.0+** | Private — significantly more powerful |

---

## License

[Here](https://github.com/ktn1703/Vanish-Obfuscator?tab=Apache-2.0-1-ov-file)

---

<div align="center">

**Built by KTN — 2026**

</div>
