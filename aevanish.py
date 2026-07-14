#!/usr/bin/env python3
import ast
import sys
import os
import re
import zlib
import hashlib
import hmac
import random
import struct
import time
import base64
import types
import builtins
import string
import platform
import uuid
import gc
import marshal
import argparse
import warnings
from pathlib import Path

from bvm_engine import build_package, RUNTIME_CORE

try:
    from pystyle import Colors, Colorate
    _HAS_PYSTYLE = True
except ImportError:
    _HAS_PYSTYLE = False

def _init_terminal() -> bool:
    if sys.platform == 'win32':
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            h = k32.GetStdHandle(-11)
            mode = ctypes.c_ulong(0)
            if k32.GetConsoleMode(h, ctypes.byref(mode)):
                k32.SetConsoleMode(h, mode.value | 0x0004)
        except Exception:
            pass
    if os.environ.get('NO_COLOR'):
        return False
    if os.environ.get('FORCE_COLOR'):
        return True
    try:
        return bool(sys.stdout.isatty())
    except Exception:
        return False


_TC = _init_terminal()
_R   = '\033[0m'
_BLD = '\033[1m'
_DIM = '\033[2m'
_RED  = '\033[91m'; _GRN  = '\033[92m'; _YLW  = '\033[93m'
_BLU  = '\033[94m'; _MAG  = '\033[95m'; _CYN  = '\033[96m'; _WHT  = '\033[97m'
_DRED = '\033[31m'; _DGRN = '\033[32m'; _DYLW = '\033[33m'
_DBLU = '\033[34m'; _DMAG = '\033[35m'; _DCYN = '\033[36m'

_PAL_BANNER  = [_MAG, _DMAG, _DBLU, _BLU, _DCYN, _CYN, _DGRN, _GRN, _DYLW, _YLW, _RED, _MAG]
_PAL_TITLE   = [_CYN, _DCYN, _DGRN, _GRN, _DYLW, _YLW]
_PAL_STEP    = [_BLU, _DBLU, _DCYN, _CYN, _DGRN, _GRN]


def _gradient(text: str, palette: list) -> str:
    if not _TC:
        return text
    out, ci = [], 0
    for ch in text:
        if ch in '\n\r':
            out.append(_R + ch); ci = 0
        elif ch == ' ':
            out.append(ch)
        else:
            out.append(palette[ci % len(palette)] + ch); ci += 1
    return ''.join(out) + _R


def _c(text: str, code: str) -> str:
    return f"{code}{text}{_R}" if _TC else text


def _bold(text: str) -> str:
    return f"{_BLD}{text}{_R}" if _TC else text


def _pystyle_gradient(text: str) -> str:
    if _HAS_PYSTYLE and _TC:
        return Colorate.Horizontal(Colors.purple_to_red, text, 1)
    return _gradient(text, _PAL_BANNER)


def _pystyle_diagonal(text: str) -> str:
    if _HAS_PYSTYLE and _TC:
        return Colorate.Diagonal(Colors.DynamicMIX((Colors.red, Colors.cyan)), text, 1)
    return text


def cprint(text: str, color: str = 'cyan') -> None:
    cm = {
        'red': _RED, 'green': _GRN, 'yellow': _YLW, 'blue': _BLU,
        'magenta': _MAG, 'purple': _MAG, 'cyan': _CYN, 'white': _WHT,
        'dred': _DRED, 'dgreen': _DGRN, 'dyellow': _DYLW,
        'dblue': _DBLU, 'dmagenta': _DMAG, 'dcyan': _DCYN,
    }
    print(f"{cm.get(color, _CYN)}{text}{_R}" if _TC else text)


def ask(prompt: str) -> str:
    if _TC:
        try:
            tag = Colorate.Diagonal(Colors.DynamicMIX((Colors.red, Colors.cyan)), ">> ", 1) if _HAS_PYSTYLE else f"{_RED}{_BLD}>> {_R}"
            ans = input(f"  {tag}{_YLW}{prompt}{_R} {_CYN}:{_R} ")
        except (EOFError, KeyboardInterrupt):
            ans = ''
    else:
        try:
            ans = input(f"  >> {prompt}: ")
        except (EOFError, KeyboardInterrupt):
            ans = ''
    return str(ans).strip()


_BANNER_ART_DEFAULT = r"""
 ██▒   █▓ ▄▄▄       ███▄    █  ██▓  ██████  ██░ ██    
▓██░   █▒▒████▄     ██ ▀█   █ ▓██▒▒██    ▒ ▓██░ ██▒   
 ▓██  █▒░▒██  ▀█▄  ▓██  ▀█ ██▒▒██▒░ ▓██▄   ▒██▀▀██░   
  ▒██ █░░░██▄▄▄▄██ ▓██▒  ▐▌██▒░██░  ▒   ██▒░▓█ ░██    
   ▒▀█░   ▓█   ▓██▒▒██░   ▓██░░██░▒██████▒▒░▓█▒░██▓   
   ░ ▐░   ▒▒   ▓▒█░░ ▒░   ▒ ▒ ░▓  ▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒   
   ░ ░░    ▒   ▒▒ ░░ ░░   ░ ▒░ ▒ ░░ ░▒  ░ ░ ▒ ░▒░ ░   
     ░░    ░   ▒      ░   ░ ░  ▒ ░░  ░  ░   ░  ░░ ░   
      ░        ░  ░         ░  ░        ░   ░  ░  ░   
     ░                                                
"""

def print_banner() -> None:
    os.system('cls' if sys.platform == 'win32' else 'clear')
    banner_txt = _BANNER_ART_DEFAULT
    lines = [l for l in banner_txt.splitlines() if l.strip()]
    try:
        tw = os.get_terminal_size().columns
    except Exception:
        tw = 80
    ml = max(len(l) for l in lines) if lines else 0
    pad = max(0, (tw - ml) // 2)
    for line in lines:
        centered = " " * pad + line
        print(_pystyle_gradient(centered))
    print()
    sep = "─" * 60
    print(f"  {_pystyle_gradient(sep)}")
    print(f"  {_pystyle_gradient('  VANISH v1.0 by KTN  -  Python Obfuscator Next-Gen  ')}")
    print(f"  {_c('  github.com/ktn1703/Vanish-Obfuscator', _DCYN)}")
    print(f"  {_pystyle_gradient(sep)}")
    print()


_FP_FN_SRC = (
    "import uuid as _vu,platform as _vhpl,hashlib as _vhh\n"
    "def _vhwf():\n"
    "    _vp=[]\n"
    "    try:_vp.append(str(_vu.getnode()))\n"
    "    except:pass\n"
    "    try:_vp.append(_vhpl.node())\n"
    "    except:pass\n"
    "    _vhs=_vhpl.system()\n"
    "    if _vhs=='Windows':\n"
    "        try:\n"
    "            import ctypes as _vhct\n"
    "            _vhbuf=_vhct.create_unicode_buffer(256);_vhser=_vhct.c_ulong(0)\n"
    "            _vhct.windll.kernel32.GetVolumeInformationW(_vhct.c_wchar_p('C:\\\\'),_vhbuf,256,_vhct.byref(_vhser),None,None,None,0)\n"
    "            _vp.append(str(_vhser.value))\n"
    "        except:pass\n"
    "        try:\n"
    "            import subprocess as _vhsp2\n"
    "            _vr2=_vhsp2.run(['wmic','csproduct','get','UUID'],capture_output=True,text=True,timeout=3)\n"
    "            _vlines=[l.strip() for l in _vr2.stdout.splitlines() if l.strip() and 'UUID' not in l]\n"
    "            if _vlines:_vp.append(_vlines[0])\n"
    "        except:pass\n"
    "    elif _vhs=='Linux':\n"
    "        for _vmp in('/etc/machine-id','/var/lib/dbus/machine-id'):\n"
    "            try:\n"
    "                with open(_vmp) as _vmf:_vp.append(_vmf.read().strip()[:64]);break\n"
    "            except:pass\n"
    "        try:\n"
    "            with open('/sys/class/dmi/id/product_uuid') as _vmf2:_vp.append(_vmf2.read().strip()[:64])\n"
    "        except:pass\n"
    "    elif _vhs=='Darwin':\n"
    "        try:\n"
    "            import subprocess as _vhsp\n"
    "            _vhr=_vhsp.run(['ioreg','-rd1','-c','IOPlatformExpertDevice'],capture_output=True,text=True,timeout=5)\n"
    "            for _vhl in _vhr.stdout.splitlines():\n"
    "                if 'IOPlatformUUID' in _vhl and '\"' in _vhl:_vp.append(_vhl.split('\"')[-2]);break\n"
    "        except:pass\n"
    "    _vs3='|'.join(_x for _x in _vp if _x) or str(_vu.getnode())\n"
    "    return _vhh.sha256(_vs3.encode()).digest()\n"
)


def get_hardware_fingerprint() -> bytes:
    ns: dict = {}
    exec(_FP_FN_SRC, ns)
    return ns['_vhwf']()


_AES_SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]

_AES_RCON = [0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36,0x6c,0xd8,0xab,0x4d,0x9a,0x2f]


def _aes_xtime(a):
    return ((a << 1) ^ 0x1b) & 0xff if a & 0x80 else (a << 1) & 0xff


def _aes_key_expansion(key):
    assert len(key) == 32
    w = list(key)
    for i in range(8, 60):
        temp = w[(i-1)*4:i*4]
        if i % 8 == 0:
            temp = [_AES_SBOX[temp[1]] ^ _AES_RCON[i//8-1],
                    _AES_SBOX[temp[2]],
                    _AES_SBOX[temp[3]],
                    _AES_SBOX[temp[0]]]
        elif i % 8 == 4:
            temp = [_AES_SBOX[b] for b in temp]
        for j in range(4):
            w.append(w[(i-8)*4+j] ^ temp[j])
    return [w[i*4:(i+1)*4] for i in range(60)]


def _aes_add_round_key(state, rk):
    for i in range(4):
        for j in range(4):
            state[i][j] ^= rk[i][j]


def _aes_sub_bytes(state):
    for i in range(4):
        for j in range(4):
            state[i][j] = _AES_SBOX[state[i][j]]


def _aes_shift_rows(state):
    state[1] = state[1][1:] + state[1][:1]
    state[2] = state[2][2:] + state[2][:2]
    state[3] = state[3][3:] + state[3][:3]


def _aes_mix_col(col):
    a = col[:]
    col[0] = _aes_xtime(a[0]) ^ _aes_xtime(a[1]) ^ a[1] ^ a[2] ^ a[3]
    col[1] = a[0] ^ _aes_xtime(a[1]) ^ _aes_xtime(a[2]) ^ a[2] ^ a[3]
    col[2] = a[0] ^ a[1] ^ _aes_xtime(a[2]) ^ _aes_xtime(a[3]) ^ a[3]
    col[3] = _aes_xtime(a[0]) ^ a[0] ^ a[1] ^ a[2] ^ _aes_xtime(a[3])


def _aes_mix_cols(state):
    for i in range(4):
        col = [state[j][i] for j in range(4)]
        _aes_mix_col(col)
        for j in range(4):
            state[j][i] = col[j]


def _aes_encrypt_block(block, expanded_key):
    state = [[block[i*4+j] for j in range(4)] for i in range(4)]
    rk = [[expanded_key[i][j] for j in range(4)] for i in range(4)]
    _aes_add_round_key(state, rk)
    for r in range(1, 14):
        _aes_sub_bytes(state)
        _aes_shift_rows(state)
        _aes_mix_cols(state)
        rk = [[expanded_key[r*4+i][j] for j in range(4)] for i in range(4)]
        _aes_add_round_key(state, rk)
    _aes_sub_bytes(state)
    _aes_shift_rows(state)
    rk = [[expanded_key[56+i][j] for j in range(4)] for i in range(4)]
    _aes_add_round_key(state, rk)
    return bytes(state[i][j] for j in range(4) for i in range(4))


def _ghash(h_bytes, aad, ciphertext):
    def _gf128_mul(x, y):
        r = 0
        for _ in range(128):
            if y & 1:
                r ^= x
            lsb = x & 1
            x >>= 1
            if lsb:
                x ^= (0xe1 << 120)
            y >>= 1
        return r

    h = int.from_bytes(h_bytes, 'big')

    def pad16(data):
        r = len(data) % 16
        return data + b'\x00' * (16 - r if r else 0)

    X = 0
    for chunk in [pad16(aad), pad16(ciphertext)]:
        for i in range(0, len(chunk), 16):
            block = int.from_bytes(chunk[i:i+16], 'big')
            X = _gf128_mul(X ^ block, h)

    lengths = struct.pack('>QQ', len(aad) * 8, len(ciphertext) * 8)
    X = _gf128_mul(X ^ int.from_bytes(lengths, 'big'), h)
    return X.to_bytes(16, 'big')


def aes256_gcm_encrypt(key, plaintext, aad=b''):
    assert len(key) == 32
    expanded = _aes_key_expansion(list(key))
    iv = os.urandom(12)
    h_bytes = _aes_encrypt_block(b'\x00' * 16, expanded)

    def _ctr_block(counter):
        block = iv + struct.pack('>I', counter)
        return _aes_encrypt_block(block, expanded)

    j0 = iv + b'\x00\x00\x00\x01'
    j0_enc = _aes_encrypt_block(j0, expanded)

    ct = bytearray()
    for i in range(0, len(plaintext), 16):
        ks = _ctr_block(i // 16 + 2)
        chunk = plaintext[i:i+16]
        ct.extend(b ^ k for b, k in zip(chunk, ks))
    ct = bytes(ct)

    tag = _ghash(h_bytes, aad, ct)
    tag = bytes(a ^ b for a, b in zip(tag, j0_enc))
    return iv, ct, tag


def aes256_gcm_decrypt(key, iv, ciphertext, tag, aad=b''):
    assert len(key) == 32
    expanded = _aes_key_expansion(list(key))
    h_bytes = _aes_encrypt_block(b'\x00' * 16, expanded)

    expected_tag = _ghash(h_bytes, aad, ciphertext)
    j0 = iv + b'\x00\x00\x00\x01'
    j0_enc = _aes_encrypt_block(j0, expanded)
    expected_tag = bytes(a ^ b for a, b in zip(expected_tag, j0_enc))

    if not hmac.compare_digest(expected_tag, tag):
        raise ValueError("AES-GCM authentication tag mismatch")

    def _ctr_block(counter):
        block = iv + struct.pack('>I', counter)
        return _aes_encrypt_block(block, expanded)

    pt = bytearray()
    for i in range(0, len(ciphertext), 16):
        ks = _ctr_block(i // 16 + 2)
        chunk = ciphertext[i:i+16]
        pt.extend(b ^ k for b, k in zip(chunk, ks))
    return bytes(pt)


def _chacha20_quarter(a, b, c, d):
    a = (a + b) & 0xFFFFFFFF; d ^= a; d = ((d << 16) | (d >> 16)) & 0xFFFFFFFF
    c = (c + d) & 0xFFFFFFFF; b ^= c; b = ((b << 12) | (b >> 20)) & 0xFFFFFFFF
    a = (a + b) & 0xFFFFFFFF; d ^= a; d = ((d << 8)  | (d >> 24)) & 0xFFFFFFFF
    c = (c + d) & 0xFFFFFFFF; b ^= c; b = ((b << 7)  | (b >> 25)) & 0xFFFFFFFF
    return a, b, c, d


def _chacha20_block(key, counter, nonce):
    assert len(key) == 32 and len(nonce) == 12
    const = b'expand 32-byte k'
    state = list(struct.unpack('<4I', const))
    state += list(struct.unpack('<8I', key))
    state += [counter]
    state += list(struct.unpack('<3I', nonce))
    working = state[:]
    for _ in range(10):
        working[0],working[4],working[8],working[12]  = _chacha20_quarter(working[0],working[4],working[8],working[12])
        working[1],working[5],working[9],working[13]  = _chacha20_quarter(working[1],working[5],working[9],working[13])
        working[2],working[6],working[10],working[14] = _chacha20_quarter(working[2],working[6],working[10],working[14])
        working[3],working[7],working[11],working[15] = _chacha20_quarter(working[3],working[7],working[11],working[15])
        working[0],working[5],working[10],working[15] = _chacha20_quarter(working[0],working[5],working[10],working[15])
        working[1],working[6],working[11],working[12] = _chacha20_quarter(working[1],working[6],working[11],working[12])
        working[2],working[7],working[8],working[13]  = _chacha20_quarter(working[2],working[7],working[8],working[13])
        working[3],working[4],working[9],working[14]  = _chacha20_quarter(working[3],working[4],working[9],working[14])
    return struct.pack('<16I', *((working[i] + state[i]) & 0xFFFFFFFF for i in range(16)))


def chacha20_encrypt(data: bytes, key: bytes, nonce: bytes = None) -> tuple:
    assert len(key) == 32
    if nonce is None:
        nonce = os.urandom(12)
    out = bytearray()
    for i, off in enumerate(range(0, len(data), 64)):
        ks = _chacha20_block(key, i, nonce)
        chunk = data[off:off+64]
        out.extend(b ^ k for b, k in zip(chunk, ks))
    return nonce, bytes(out)


chacha20_decrypt = chacha20_encrypt


def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    if not salt:
        salt = b'\x00' * 32
    return hmac.new(salt, ikm, hashlib.sha256).digest()


def hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
    t = b''
    okm = b''
    i = 1
    while len(okm) < length:
        t = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
        okm += t
        i += 1
    return okm[:length]


def hkdf(ikm: bytes, length: int, salt: bytes = b'', info: bytes = b'') -> bytes:
    prk = hkdf_extract(salt, ikm)
    return hkdf_expand(prk, info, length)


def xorshift_stream(data: bytes, key_b: bytes) -> bytes:
    seed = int.from_bytes(key_b[:8], 'big')
    if seed == 0:
        seed = 0xDEADBEEFCAFEBABE
    x = seed
    out = bytearray(len(data))
    for i, byte in enumerate(data):
        x ^= (x << 13) & 0xFFFFFFFFFFFFFFFF
        x ^= (x >> 7)
        x ^= (x << 17) & 0xFFFFFFFFFFFFFFFF
        out[i] = byte ^ (x & 0xFF)
    return bytes(out)


xorshift_unstream = xorshift_stream


def _seed_from_key(key_c: bytes) -> int:
    return int.from_bytes(hashlib.sha256(key_c + b'permute_v8').digest()[:8], 'big')


def byte_shuffle(data: bytes, key_c: bytes) -> bytes:
    n = len(data)
    if n == 0:
        return data
    rng = random.Random(_seed_from_key(key_c))
    indices = list(range(n))
    rng.shuffle(indices)
    out = bytearray(n)
    for new_pos, old_pos in enumerate(indices):
        out[new_pos] = data[old_pos]
    return bytes(out)


def byte_unshuffle(data: bytes, key_c: bytes) -> bytes:
    n = len(data)
    if n == 0:
        return data
    rng = random.Random(_seed_from_key(key_c))
    indices = list(range(n))
    rng.shuffle(indices)
    out = bytearray(n)
    for new_pos, old_pos in enumerate(indices):
        out[old_pos] = data[new_pos]
    return bytes(out)


def build_payload_v8(source: str, hw_bind: bool = False):
    try:
        raw = build_package(source)
    except Exception:
        raw = b'\x09' + marshal.dumps(compile(source, '<vanish>', 'exec'))

    compressed = zlib.compress(raw, level=9)

    master_key = os.urandom(32)
    salt = os.urandom(16)

    aes_key    = hkdf(master_key, 32, salt + b'aes', b'aes256gcm-key-v8')
    chacha_key = hkdf(master_key, 32, salt + b'cc20', b'chacha20-key-v8')
    xor_key    = hkdf(master_key, 16, salt + b'xors', b'xorshift-key-v8')
    shuf_key   = hkdf(master_key, 16, salt + b'shuf', b'shuffle-key-v8')

    aad = b'vanish-v8-aad'
    iv_aes, ct_aes, tag_aes = aes256_gcm_encrypt(aes_key, compressed, aad)

    aes_blob = iv_aes + tag_aes + ct_aes

    nonce_cc, ct_cc = chacha20_encrypt(aes_blob, chacha_key)
    cc_blob = nonce_cc + ct_cc

    xs_data = xorshift_stream(cc_blob, xor_key)

    sh_data = byte_shuffle(xs_data, shuf_key)

    encoded = base64.b85encode(sh_data).decode('ascii')

    fp_key = salt + b'VANISH_V8_MASTER_KEY_PROTECT'
    mask = hashlib.sha256(fp_key).digest()[:32]
    stored_master = bytes(a ^ b for a, b in zip(master_key, mask))
    if hw_bind:
        fp = get_hardware_fingerprint()
        fp_mask = hashlib.sha256(fp + b'VANISH_V8_HW').digest()[:32]
        stored_master = bytes(a ^ b ^ c for a, b, c in zip(stored_master, fp_mask, mask))

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"

    return (
        encoded,
        stored_master.hex(),
        salt.hex(),
        py_ver,
    )


_USED_NAMES: set = set()
_CONFUSE_CHARS = list('IlI1lI0OIlI1OlI')


def _reset_names():
    global _USED_NAMES
    _USED_NAMES = set()


def rand_confuse_name(length=18) -> str:
    for _ in range(10000):
        name = '_' + ''.join(random.choices(_CONFUSE_CHARS, k=length))
        if name not in _USED_NAMES and name.isidentifier():
            _USED_NAMES.add(name)
            return name
    n = f"_vns_{random.getrandbits(64):016x}"
    _USED_NAMES.add(n)
    return n


def rand_hex_name(length=16) -> str:
    return f"_0x{int.from_bytes(os.urandom(length * 4 // 8), 'big'):0{length}x}"


PYTHON_BUILTINS = set(dir(builtins)) | {
    '__name__', '__file__', '__doc__', '__package__', '__spec__',
    '__loader__', '__builtins__', '__cached__', 'self', 'cls',
    '__init__', '__new__', '__del__', '__repr__', '__str__',
    '__bytes__', '__format__', '__lt__', '__le__', '__eq__',
    '__ne__', '__gt__', '__ge__', '__hash__', '__bool__',
    '__getattr__', '__getattribute__', '__setattr__', '__delattr__',
    '__dir__', '__get__', '__set__', '__delete__', '__call__',
    '__len__', '__getitem__', '__setitem__', '__delitem__',
    '__iter__', '__next__', '__contains__', '__add__', '__sub__',
    '__mul__', '__truediv__', '__floordiv__', '__mod__', '__pow__',
    '__enter__', '__exit__', '__await__', '__aiter__', '__anext__',
    '__aenter__', '__aexit__', '__class__', '__bases__', '__mro__',
    '__abstractmethods__', 'args', 'kwargs', '__all__',
    '__version__', '__author__', 'main',
}

MAGIC_METHODS = {
    '__init__', '__new__', '__del__', '__repr__', '__str__', '__len__',
    '__getitem__', '__setitem__', '__delitem__', '__iter__', '__next__',
    '__contains__', '__call__', '__enter__', '__exit__', '__get__', '__set__',
    '__delete__', '__add__', '__sub__', '__mul__', '__truediv__', '__eq__',
    '__ne__', '__lt__', '__le__', '__gt__', '__ge__', '__hash__', '__bool__',
    '__getattr__', '__setattr__', '__delattr__', '__class__', '__name__',
    '__all__', '__slots__',
}


class NameCollector(ast.NodeVisitor):
    def __init__(self):
        self.names: set = set()
        self._attr_names: set = set()
        self._class_method_names: set = set()
        self._in_class: int = 0

    def _collect_attrs(self, tree):
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute):
                self._attr_names.add(n.attr)

    def visit_Module(self, node):
        self._collect_attrs(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if node.name not in PYTHON_BUILTINS:
            self.names.add(node.name)
        self._in_class += 1
        self.generic_visit(node)
        self._in_class -= 1

    def visit_FunctionDef(self, node):
        if self._in_class > 0:
            self._class_method_names.add(node.name)
        elif node.name not in PYTHON_BUILTINS and not node.name.startswith('__'):
            self.names.add(node.name)
        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            if (arg.arg not in PYTHON_BUILTINS
                    and not arg.arg.startswith('__')
                    and arg.arg not in ('self', 'cls')):
                self.names.add(arg.arg)
        if node.args.vararg and node.args.vararg.arg not in PYTHON_BUILTINS:
            self.names.add(node.args.vararg.arg)
        if node.args.kwarg and node.args.kwarg.arg not in PYTHON_BUILTINS:
            self.names.add(node.args.kwarg.arg)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Name(self, node):
        if (isinstance(node.ctx, (ast.Store, ast.Load))
                and node.id not in PYTHON_BUILTINS
                and not node.id.startswith('__')
                and node.id not in ('self', 'cls')):
            self.names.add(node.id)
            if self._in_class > 0:
                self._class_method_names.add(node.id)
        self.generic_visit(node)

    def visit_Global(self, node): pass
    def visit_Nonlocal(self, node): pass

    def visit_Call(self, node):
        for kw in node.keywords:
            if kw.arg:
                self._attr_names.add(kw.arg)
        self.generic_visit(node)

    def visit_Import(self, node):
        for a in node.names:
            self._attr_names.add(a.asname if a.asname else a.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for a in node.names:
            self._attr_names.add(a.asname if a.asname else a.name)
        self.generic_visit(node)

    def safe_names(self):
        return self.names - self._attr_names - self._class_method_names - PYTHON_BUILTINS


class VariableRenamer(ast.NodeTransformer):
    def __init__(self, nm):
        self.nm = nm
        self._ic = 0

    def _r(self, n):
        return self.nm.get(n, n)

    def visit_Name(self, node):
        if self._ic == 0 and node.id not in ('self', 'cls'):
            node.id = self._r(node.id)
        return node

    def visit_FunctionDef(self, node):
        if self._ic > 0:
            self.generic_visit(node)
            return node
        original_name = node.name
        if node.name not in MAGIC_METHODS and node.name in self.nm:
            node.name = self._r(node.name)
        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            if arg.arg not in ('self', 'cls'):
                arg.arg = self._r(arg.arg)
        if node.args.vararg and node.args.vararg.arg not in ('self', 'cls'):
            node.args.vararg.arg = self._r(node.args.vararg.arg)
        if node.args.kwarg and node.args.kwarg.arg not in ('self', 'cls'):
            node.args.kwarg.arg = self._r(node.args.kwarg.arg)
        new_name = node.name
        if original_name != new_name and node.decorator_list:
            decos = [self.visit(d) for d in node.decorator_list]
            node.decorator_list = []
            self.generic_visit(node)
            name_restore = ast.Assign(
                targets=[ast.Attribute(
                    value=ast.Name(id=new_name, ctx=ast.Load()),
                    attr='__name__', ctx=ast.Store())],
                value=ast.Constant(value=original_name),
                lineno=node.lineno, col_offset=node.col_offset)
            ast.fix_missing_locations(name_restore)
            result = [node, name_restore]
            for deco in reversed(decos):
                app = ast.Assign(
                    targets=[ast.Name(id=new_name, ctx=ast.Store())],
                    value=ast.Call(
                        func=deco,
                        args=[ast.Name(id=new_name, ctx=ast.Load())],
                        keywords=[]),
                    lineno=node.lineno, col_offset=node.col_offset)
                ast.fix_missing_locations(app)
                result.append(app)
            return result
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        if node.name in self.nm:
            node.name = self._r(node.name)
        self._ic += 1
        self.generic_visit(node)
        self._ic -= 1
        return node

    def visit_Attribute(self, node):
        self.visit(node.value)
        return node

    def visit_Global(self, node):
        if self._ic == 0:
            node.names = [self._r(n) for n in node.names]
        return node

    def visit_Nonlocal(self, node):
        if self._ic == 0:
            node.names = [self._r(n) for n in node.names]
        return node

    def visit_arg(self, node):
        if self._ic == 0 and node.arg not in ('self', 'cls'):
            node.arg = self._r(node.arg)
        return node

    def visit_NamedExpr(self, node):
        if isinstance(node.target, ast.Name) and node.target.id not in ('self', 'cls'):
            node.target.id = self._r(node.target.id)
        self.generic_visit(node)
        return node

    def visit_MatchAs(self, node):
        if node.name and node.name not in ('self', 'cls'):
            node.name = self._r(node.name)
        self.generic_visit(node)
        return node

    def visit_MatchStar(self, node):
        if node.name and node.name not in ('self', 'cls'):
            node.name = self._r(node.name)
        self.generic_visit(node)
        return node

    def visit_MatchClass(self, node):
        self.generic_visit(node)
        return node

    def visit_ExceptHandler(self, node):
        if self._ic == 0 and node.name and node.name in self.nm:
            node.name = self._r(node.name)
        self.generic_visit(node)
        return node


class StringEncryptor(ast.NodeTransformer):
    def __init__(self, key: int):
        self.key = key
        self._in_fstring = 0

    def visit_JoinedStr(self, node):
        self._in_fstring += 1
        self.generic_visit(node)
        self._in_fstring -= 1
        return node

    def _xor_pos(self, s: str):
        key = self.key
        enc = [x ^ ((key + i) % 256) for i, x in enumerate(s.encode('utf-8', errors='replace'))]
        en = ast.List(elts=[ast.Constant(value=v) for v in enc], ctx=ast.Load())
        return ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id='bytes', ctx=ast.Load()),
                    args=[ast.ListComp(
                        elt=ast.BinOp(
                            left=ast.Name(id='_v', ctx=ast.Load()),
                            op=ast.BitXor(),
                            right=ast.BinOp(
                                left=ast.BinOp(
                                    left=ast.Constant(value=key),
                                    op=ast.Add(),
                                    right=ast.Name(id='_i', ctx=ast.Load())),
                                op=ast.Mod(),
                                right=ast.Constant(value=256))),
                        generators=[ast.comprehension(
                            target=ast.Tuple(
                                elts=[ast.Name(id='_i', ctx=ast.Store()),
                                      ast.Name(id='_v', ctx=ast.Store())],
                                ctx=ast.Store()),
                            iter=ast.Call(
                                func=ast.Name(id='enumerate', ctx=ast.Load()),
                                args=[en], keywords=[]),
                            ifs=[], is_async=0)])],
                    keywords=[]),
                attr='decode', ctx=ast.Load()),
            args=[ast.Constant(value='utf-8'), ast.Constant(value='replace')],
            keywords=[])

    def _xor_rev(self, s: str):
        key = self.key
        b = s.encode('utf-8', errors='replace')
        enc = [x ^ ((key * 7 + i) % 256) for i, x in enumerate(reversed(b))]
        en = ast.List(elts=[ast.Constant(value=v) for v in enc], ctx=ast.Load())
        return ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id='bytes', ctx=ast.Load()),
                    args=[ast.Call(
                        func=ast.Name(id='reversed', ctx=ast.Load()),
                        args=[ast.ListComp(
                            elt=ast.BinOp(
                                left=ast.Name(id='_v', ctx=ast.Load()),
                                op=ast.BitXor(),
                                right=ast.BinOp(
                                    left=ast.BinOp(
                                        left=ast.BinOp(
                                            left=ast.Constant(value=key),
                                            op=ast.Mult(),
                                            right=ast.Constant(value=7)),
                                        op=ast.Add(),
                                        right=ast.Name(id='_i', ctx=ast.Load())),
                                    op=ast.Mod(),
                                    right=ast.Constant(value=256))),
                            generators=[ast.comprehension(
                                target=ast.Tuple(
                                    elts=[ast.Name(id='_i', ctx=ast.Store()),
                                          ast.Name(id='_v', ctx=ast.Store())],
                                    ctx=ast.Store()),
                                iter=ast.Call(
                                    func=ast.Name(id='enumerate', ctx=ast.Load()),
                                    args=[en], keywords=[]),
                                ifs=[], is_async=0)])],
                        keywords=[])],
                    keywords=[]),
                attr='decode', ctx=ast.Load()),
            args=[ast.Constant(value='utf-8'), ast.Constant(value='replace')],
            keywords=[])

    def _xor_split(self, s: str):
        key = self.key
        b = s.encode('utf-8', errors='replace')
        mid = len(b) // 2
        h1 = [x ^ ((key + i * 3) % 256) for i, x in enumerate(b[:mid])]
        h2 = [x ^ ((key * 2 + i * 5) % 256) for i, x in enumerate(b[mid:])]
        enc = h1 + h2
        en = ast.List(elts=[ast.Constant(value=v) for v in enc], ctx=ast.Load())
        h1_len = ast.Constant(value=len(h1))

        def make_lc(start_expr, key_mul, key_add_mul):
            return ast.ListComp(
                elt=ast.BinOp(
                    left=ast.Name(id='_v', ctx=ast.Load()),
                    op=ast.BitXor(),
                    right=ast.BinOp(
                        left=ast.BinOp(
                            left=ast.BinOp(
                                left=ast.Constant(value=key),
                                op=ast.Mult(),
                                right=ast.Constant(value=key_mul)),
                            op=ast.Add(),
                            right=ast.BinOp(
                                left=ast.Name(id='_i', ctx=ast.Load()),
                                op=ast.Mult(),
                                right=ast.Constant(value=key_add_mul))),
                        op=ast.Mod(),
                        right=ast.Constant(value=256))),
                generators=[ast.comprehension(
                    target=ast.Tuple(
                        elts=[ast.Name(id='_i', ctx=ast.Store()),
                              ast.Name(id='_v', ctx=ast.Store())],
                        ctx=ast.Store()),
                    iter=ast.Call(
                        func=ast.Name(id='enumerate', ctx=ast.Load()),
                        args=[ast.Subscript(
                            value=en,
                            slice=start_expr,
                            ctx=ast.Load())],
                        keywords=[]),
                    ifs=[], is_async=0)])

        lc1 = make_lc(ast.Slice(upper=h1_len), 1, 3)
        lc2 = make_lc(ast.Slice(lower=h1_len), 2, 5)

        return ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id='bytes', ctx=ast.Load()),
                    args=[ast.BinOp(left=lc1, op=ast.Add(), right=lc2)],
                    keywords=[]),
                attr='decode', ctx=ast.Load()),
            args=[ast.Constant(value='utf-8'), ast.Constant(value='replace')],
            keywords=[])

    def _rc4_scheme(self, s: str):
        key = self.key
        b = s.encode('utf-8', errors='replace')
        k = [(key * 3 + i * 7) % 256 for i in range(len(b))]
        enc = [x ^ k[i] for i, x in enumerate(b)]
        k_lit = ast.List(elts=[ast.Constant(value=v) for v in k], ctx=ast.Load())
        enc_lit = ast.List(elts=[ast.Constant(value=v) for v in enc], ctx=ast.Load())
        return ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id='bytes', ctx=ast.Load()),
                    args=[ast.ListComp(
                        elt=ast.BinOp(
                            left=ast.Name(id='_e', ctx=ast.Load()),
                            op=ast.BitXor(),
                            right=ast.Name(id='_k', ctx=ast.Load())),
                        generators=[ast.comprehension(
                            target=ast.Tuple(
                                elts=[ast.Name(id='_e', ctx=ast.Store()),
                                      ast.Name(id='_k', ctx=ast.Store())],
                                ctx=ast.Store()),
                            iter=ast.Call(
                                func=ast.Name(id='zip', ctx=ast.Load()),
                                args=[enc_lit, k_lit], keywords=[]),
                            ifs=[], is_async=0)])],
                    keywords=[]),
                attr='decode', ctx=ast.Load()),
            args=[ast.Constant(value='utf-8'), ast.Constant(value='replace')],
            keywords=[])

    def _modadd_scheme(self, s: str):
        key = self.key
        b = s.encode('utf-8', errors='replace')
        k2 = (key * 31 + 17) % 256
        enc = [(x + k2 + i) % 256 for i, x in enumerate(b)]
        en = ast.List(elts=[ast.Constant(value=v) for v in enc], ctx=ast.Load())
        k2_node = ast.Constant(value=k2)
        return ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id='bytes', ctx=ast.Load()),
                    args=[ast.ListComp(
                        elt=ast.BinOp(
                            left=ast.BinOp(
                                left=ast.Name(id='_v', ctx=ast.Load()),
                                op=ast.Sub(),
                                right=ast.BinOp(
                                    left=ast.BinOp(left=k2_node, op=ast.Add(), right=ast.Name(id='_i', ctx=ast.Load())),
                                    op=ast.Mod(),
                                    right=ast.Constant(value=256))),
                            op=ast.Mod(),
                            right=ast.Constant(value=256)),
                        generators=[ast.comprehension(
                            target=ast.Tuple(
                                elts=[ast.Name(id='_i', ctx=ast.Store()),
                                      ast.Name(id='_v', ctx=ast.Store())],
                                ctx=ast.Store()),
                            iter=ast.Call(
                                func=ast.Name(id='enumerate', ctx=ast.Load()),
                                args=[en], keywords=[]),
                            ifs=[], is_async=0)])],
                    keywords=[]),
                attr='decode', ctx=ast.Load()),
            args=[ast.Constant(value='utf-8'), ast.Constant(value='replace')],
            keywords=[])

    def visit_Constant(self, node):
        if self._in_fstring > 0:
            return node
        if not isinstance(node.value, str) or len(node.value) < 1:
            return node
        scheme = random.randint(0, 4)
        try:
            if scheme == 0:
                new = self._xor_pos(node.value)
            elif scheme == 1:
                new = self._xor_rev(node.value)
            elif scheme == 2:
                new = self._xor_split(node.value)
            elif scheme == 3:
                new = self._rc4_scheme(node.value)
            else:
                new = self._modadd_scheme(node.value)
            return ast.copy_location(new, node)
        except Exception:
            return node


class IntObfuscator(ast.NodeTransformer):
    MAX_OBFUSCATE = 0xFFFFFFFF

    def _mba_expr(self, v):
        a = random.randint(1, 0xFFFF)
        b = v ^ a
        and_val = a & b
        return ast.BinOp(
            left=ast.BinOp(
                left=ast.BinOp(left=ast.Constant(value=a), op=ast.Add(), right=ast.Constant(value=b)),
                op=ast.Sub(),
                right=ast.BinOp(
                    left=ast.Constant(value=2),
                    op=ast.Mult(),
                    right=ast.Constant(value=and_val))),
            op=ast.Add(),
            right=ast.Constant(value=0))

    def _opaque_const(self, v):
        k = random.randint(2, 15)
        a = random.randint(100, 9999)
        prod = a * k
        c = prod - v
        return ast.BinOp(
            left=ast.BinOp(
                left=ast.BinOp(left=ast.Constant(value=a), op=ast.Mult(), right=ast.Constant(value=k)),
                op=ast.Sub(),
                right=ast.Constant(value=c)),
            op=ast.Add(),
            right=ast.Constant(value=0))

    def _trilinear_mba(self, v):
        a2 = 0
        for bit_pos in range(max(v.bit_length(), 1)):
            if random.random() > 0.5 and (v >> bit_pos) & 1:
                a2 |= (1 << bit_pos)
        if a2 == 0 and v > 0:
            lsb = v & -v
            a2 = lsb
        b2 = v
        and_val = a2 & b2
        return ast.BinOp(
            left=ast.BinOp(
                left=ast.Constant(value=a2),
                op=ast.Add(),
                right=ast.Constant(value=b2)),
            op=ast.Sub(),
            right=ast.Constant(value=and_val))

    def visit_Constant(self, node):
        if (isinstance(node.value, int)
                and not isinstance(node.value, bool)
                and 0 < abs(node.value) <= self.MAX_OBFUSCATE
                and random.random() > 0.4):
            try:
                v = node.value
                if v < 0:
                    abs_v = abs(v)
                    inner = self._mba_expr(abs_v)
                    new = ast.UnaryOp(op=ast.USub(), operand=inner)
                    return ast.copy_location(new, node)
                scheme = random.randint(0, 3)
                if scheme == 0:
                    new = self._mba_expr(v)
                elif scheme == 1:
                    a = random.randint(1, 127)
                    new = ast.BinOp(
                        left=ast.Constant(value=a),
                        op=ast.BitXor(),
                        right=ast.Constant(value=v ^ a))
                elif scheme == 2:
                    new = self._opaque_const(v)
                else:
                    new = self._trilinear_mba(v)
                return ast.copy_location(new, node)
            except Exception:
                pass
        return node


def _opaque_true():
    return random.choice([
        lambda: ast.Compare(
            left=ast.BinOp(
                left=ast.BinOp(
                    left=ast.Constant(value=random.randint(2, 99)),
                    op=ast.Pow(),
                    right=ast.Constant(value=2)),
                op=ast.Add(),
                right=ast.Constant(value=1)),
            ops=[ast.Gt()],
            comparators=[ast.Constant(value=0)]),
        lambda: ast.Compare(
            left=ast.BinOp(
                left=ast.Constant(value=random.randint(1, 50)),
                op=ast.Mult(),
                right=ast.Constant(value=0)),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=0)]),
        lambda: ast.Compare(
            left=ast.Call(func=ast.Name(id='hash', ctx=ast.Load()),
                          args=[ast.Constant(value=None)], keywords=[]),
            ops=[ast.Eq()],
            comparators=[ast.Call(func=ast.Name(id='hash', ctx=ast.Load()),
                                  args=[ast.Constant(value=None)], keywords=[])]),
        lambda: ast.Compare(
            left=ast.BinOp(
                left=ast.Constant(value=random.randint(1, 99)),
                op=ast.BitAnd(),
                right=ast.Constant(value=0xFF)),
            ops=[ast.LtE()],
            comparators=[ast.Constant(value=255)]),
    ])()


def _make_junk_body():
    ns = [rand_confuse_name() for _ in range(4)]
    lines = [ast.Assign(
        targets=[ast.Name(id=n, ctx=ast.Store())],
        value=ast.BinOp(
            left=ast.Constant(value=random.randint(1, 9999)),
            op=random.choice([ast.Add, ast.Mult, ast.BitXor])(),
            right=ast.Constant(value=random.randint(1, 9999))),
        lineno=1, col_offset=0) for n in ns[:2]]
    lines.append(ast.If(
        test=_opaque_true(),
        body=[ast.Assign(
            targets=[ast.Name(id=rand_confuse_name(), ctx=ast.Store())],
            value=ast.Constant(value=random.randint(0, 999999)),
            lineno=1, col_offset=0)],
        orelse=[ast.Expr(value=ast.Constant(value=None))]))
    lines.append(ast.Return(value=ast.Constant(value=None)))
    return lines


def _make_junk_try_body():
    ns = rand_confuse_name()
    return [
        ast.Try(
            body=[ast.Assign(
                targets=[ast.Name(id=ns, ctx=ast.Store())],
                value=ast.BinOp(
                    left=ast.Constant(value=random.randint(1, 9999)),
                    op=ast.BitAnd(),
                    right=ast.Constant(value=random.randint(1, 9999))),
                lineno=1, col_offset=0)],
            handlers=[ast.ExceptHandler(
                type=ast.Name(id='Exception', ctx=ast.Load()),
                name=None,
                body=[ast.Pass()])],
            orelse=[],
            finalbody=[]),
        ast.Return(value=ast.Constant(value=None))
    ]


def make_junk_functions(count=14):
    names = [rand_confuse_name() for _ in range(count)]
    funcs = []
    for i, name in enumerate(names):
        use_try = random.random() > 0.4
        body = _make_junk_try_body() if use_try else _make_junk_body()
        if i > 0:
            body.insert(0, ast.Expr(value=ast.Call(
                func=ast.Name(id=names[i - 1], ctx=ast.Load()),
                args=[], keywords=[])))
        f = ast.FunctionDef(
            name=name,
            args=ast.arguments(
                posonlyargs=[], args=[], vararg=None,
                kwonlyargs=[], kw_defaults=[],
                kwarg=None, defaults=[]),
            body=body, decorator_list=[], returns=None,
            lineno=1, col_offset=0)
        ast.fix_missing_locations(f)
        funcs.append(f)
    return funcs


def _has_flow_break(stmt):
    for n in ast.walk(stmt):
        if isinstance(n, (ast.Return, ast.Yield, ast.YieldFrom, ast.Raise, ast.Break, ast.Continue, ast.Await)):
            return True
    return False


def _is_declaration(stmt):
    return isinstance(stmt, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))


def flatten_control_flow(tree: ast.Module) -> ast.Module:
    sv = rand_confuse_name()
    body = tree.body
    if len(body) < 3:
        return tree
    declarations = []
    executable = []
    for stmt in body:
        if _is_declaration(stmt):
            declarations.append(stmt)
        else:
            executable.append(stmt)
    if len(executable) < 2:
        return tree
    for stmt in executable:
        if _has_flow_break(stmt):
            return tree
    keys = list(range(len(executable)))
    random.shuffle(keys)
    km = {orig: shuf for orig, shuf in enumerate(keys)}
    iv = {v: k for k, v in km.items()}
    cases = []
    for si in sorted(km.values()):
        oi = iv[si]
        nk = km.get(oi + 1, -1)
        cases.append(ast.If(
            test=ast.Compare(
                left=ast.Name(id=sv, ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=si)]),
            body=[executable[oi], ast.Assign(
                targets=[ast.Name(id=sv, ctx=ast.Store())],
                value=ast.Constant(value=nk),
                lineno=1, col_offset=0)],
            orelse=[]))
    cases.append(ast.If(
        test=ast.Compare(
            left=ast.Name(id=sv, ctx=ast.Load()),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=-1)]),
        body=[ast.Break()],
        orelse=[]))
    tree.body = declarations + [
        ast.Assign(
            targets=[ast.Name(id=sv, ctx=ast.Store())],
            value=ast.Constant(value=km[0]),
            lineno=1, col_offset=0),
        ast.While(test=ast.Constant(value=True), body=cases, orelse=[])
    ]
    ast.fix_missing_locations(tree)
    return tree

_ANTI_DEBUG_STUB = r'''
import sys as _vanish_sys, os as _vanish_os, platform as _vanish_plat, time as _vanish_tm

if __name__ == '__main__':
    def _vanish_check_debug():
        if _vanish_sys.gettrace() is not None: _vanish_os._exit(0)
        if _vanish_sys.getprofile() is not None: _vanish_os._exit(0)
        _t0 = _vanish_tm.perf_counter()
        for _m in ['pdb','debugpy','pydevd','bdb','pudb','ipdb','winpdb','rpdb',
                   'pydevd_tracing','_pydevd_bundle','pydevd_breakpoints',
                   'pydevd_file_utils','epdb','remote_pdb','pyinstrument','viztracer',
                   'pydevd_concurrency_analyser','_pydevd_frame_eval']:
            if _m in _vanish_sys.modules: _vanish_os._exit(0)
        for _e in ['PYTHONDEBUG','PYTHONINSPECT','PYTHONBREAKPOINT','PYCHARM_DEBUG',
                   'VSCODE_DEBUGGER','PYDEVD_USE_FRAME_EVAL','DEBUGPY_LAUNCHER_PORT',
                   'VSCODE_PID','_DEBUGPY_SESSION_WAIT_FOR_ATTACH','PYDEVD_DISABLE_FILE_VALIDATION']:
            if _vanish_os.environ.get(_e): _vanish_os._exit(0)
        _vsn = _vanish_plat.system()
        if _vsn == 'Windows':
            try:
                import ctypes as _vct
                _pk = _vct.windll.kernel32.GetCurrentProcess()
                if _vct.windll.kernel32.IsDebuggerPresent(): _vanish_os._exit(0)
                _rb = _vct.c_bool(False)
                _vct.windll.kernel32.CheckRemoteDebuggerPresent(_pk, _vct.byref(_rb))
                if _rb.value: _vanish_os._exit(0)
                try:
                    _nt = _vct.windll.ntdll
                    _nt.NtSetInformationThread.restype = _vct.c_long
                    _ct = _vct.windll.kernel32.GetCurrentThread()
                    _nt.NtSetInformationThread(_ct, 0x11, _vct.byref(_vct.c_ulong(0)), 4)
                except: pass
                try:
                    _nt = _vct.windll.ntdll
                    _dp = _vct.c_ulong(0)
                    _rl = _vct.c_ulong(0)
                    _nt.NtQueryInformationProcess.argtypes = [_vct.c_void_p, _vct.c_ulong, _vct.c_void_p, _vct.c_ulong, _vct.POINTER(_vct.c_ulong)]
                    _nt.NtQueryInformationProcess.restype = _vct.c_long
                    if _nt.NtQueryInformationProcess(_pk, 7, _vct.byref(_dp), 4, _vct.byref(_rl)) == 0 and _dp.value:
                        _vanish_os._exit(0)
                    _df = _vct.c_ulong(0)
                    if _nt.NtQueryInformationProcess(_pk, 0x1F, _vct.byref(_df), 4, _vct.byref(_rl)) == 0 and _df.value == 0:
                        _vanish_os._exit(0)
                except: pass
                try:
                    import winreg as _wr
                    _dbg_tools = ['x64dbg','x32dbg','ollydbg','windbg','ida','idag','idaq','idaw',
                                  'ida64','idat','idat64','radare2','frida','frida-server','cheatengine',
                                  'procmon','procexp','process hacker','wireshark','fiddler','dnspy']
                    import subprocess as _sp
                    _proc_out = _sp.run(['tasklist','/FO','CSV','/NH'], capture_output=True, text=True, timeout=3)
                    _proc_lower = _proc_out.stdout.lower()
                    for _dt in _dbg_tools:
                        if _dt in _proc_lower: _vanish_os._exit(0)
                except: pass
            except: pass
        elif _vsn == 'Linux':
            try:
                _tpid = 0
                with open('/proc/self/status') as _pf:
                    for _ln in _pf:
                        if _ln.startswith('TracerPid:'):
                            _tpid = int(_ln.split(':')[1].strip()); break
                if _tpid != 0:
                    _vanish_os._exit(0)
            except: pass
            try:
                with open('/proc/self/maps') as _mf:
                    _mc = _mf.read().lower()
                    for _dbgl in ['frida','gdb','ltrace','strace','valgrind','perf']:
                        if _dbgl in _mc: _vanish_os._exit(0)
            except: pass
            try:
                import socket as _sk
                _fs = _sk.socket(_sk.AF_INET, _sk.SOCK_STREAM)
                _fs.settimeout(0.1)
                if _fs.connect_ex(('127.0.0.1', 27042)) == 0: _vanish_os._exit(0)
                _fs.close()
            except: pass
        elif _vsn == 'Darwin':
            try:
                import subprocess as _sp2
                _plist = _sp2.run(['ps','aux'], capture_output=True, text=True, timeout=3).stdout.lower()
                for _dt2 in ['frida','lldb','gdb','dtrace','instruments']:
                    if _dt2 in _plist: _vanish_os._exit(0)
            except: pass
        _t1 = _vanish_tm.perf_counter()
        if (_t1 - _t0) > 2.0: _vanish_os._exit(0)

    _vanish_check_debug()
    del _vanish_check_debug

del _vanish_plat, _vanish_tm
'''

_ANTI_HOOK_STUB = r'''
import builtins as _vanish_bi, types as _vanish_ty, sys as _vanish_hs, hashlib as _vanish_hh

def _vanish_check_hooks():
    for _fn in ('exec', 'eval', 'compile', '__import__', 'open', 'abs', 'len', 'print'):
        _ff = getattr(_vanish_bi, _fn, None)
        if _ff is None or not isinstance(_ff, _vanish_ty.BuiltinFunctionType):
            import os; os._exit(0)
    try:
        import marshal as _vm2
        _spec = getattr(_vm2, '__spec__', None)
        if _spec is not None and getattr(_spec, 'origin', 'built-in') != 'built-in':
            import os; os._exit(0)
    except Exception:
        pass
    _bad = frozenset(('pydevd','debugpy','bdb','pdb','pudb','ipdb','winpdb','rpdb','frida','inject','hookimport','traceimport','monkeyimport'))
    for _mp in _vanish_hs.meta_path:
        _mpn = (getattr(_mp, '__name__', None) or type(_mp).__name__).lower()
        if any(_b in _mpn for _b in _bad):
            import os; os._exit(0)
    if _vanish_hs.gettrace() is not None: import os; os._exit(0)
    try:
        import gc as _gc2
        for _obj in _gc2.get_referrers(_vanish_bi.__dict__):
            if isinstance(_obj, dict) and '__wrapped__' in _obj:
                import os; os._exit(0)
    except: pass

_vanish_check_hooks()
del _vanish_check_hooks, _vanish_bi, _vanish_ty, _vanish_hs, _vanish_hh
'''

_ANTI_FRAME_STUB = r'''
import sys as _vs, os as _vo, gc as _gc
if __name__=="__main__":
    for _bm in("pdb","debugpy","pydevd","bdb","pudb","ipdb","winpdb","rpdb","_pydevd_bundle","viztracer","pyinstrument","objgraph","memory_profiler","tracemalloc","line_profiler"):
        if _bm in _vs.modules:_vo._exit(1)
    if _vs.gettrace()is not None:_vo._exit(1)
    if _vs.getprofile()is not None:_vo._exit(1)
    try:
        _gc.disable();_gc.collect();_gc.garbage.clear()
    except:pass
    try:
        import inspect as _ins
        _fr=_ins.currentframe()
        while _fr:
            _fn=getattr(_fr,"f_code",None)
            if _fn:
                _fname=getattr(_fn,"co_filename","").lower()
                if any(_x in _fname for _x in["pydevd","debugpy","pdb","pycharm","vscode","ide","trace","hook"]):_vo._exit(1)
            _fr=_fr.f_back
        del _ins,_fr
    except:pass
    try:
        if _vs.platform!="win32":
            import os as _os2
            for _fd in range(3,256):
                try:
                    _lp=_os2.readlink("/proc/self/fd/"+str(_fd))
                    if any(_x in _lp.lower() for _x in["pydevd","debugpy","pipe","pty"]):
                        try:_os2.close(_fd)
                        except:pass
                except:pass
            del _os2
    except:pass
    try:
        import threading as _thr
        for _t in _thr.enumerate():
            if hasattr(_t,"_target")and _t._target:
                _tgt=str(getattr(_t,"_target","")).lower()
                if any(_x in _tgt for _x in["debug","trace","monitor","profile"]):
                    try:_t.daemon=True
                    except:pass
        del _thr
    except:pass
    try:
        _env_keys=[_ek for _ek in _vo.environ if any(_x in _ek.lower() for _x in["debug","trace","inspect","breakpoint","charles","fiddler","proxy"])]
        for _ek in _env_keys:
            try:del _vo.environ[_ek]
            except:pass
    except:pass
del _vs,_vo,_gc
'''

def _build_antipycdc_stub() -> str:
    big_consts = "(" + ",".join(
        repr(f"_vc_{i:06x}_{i*7+13:08x}") for i in range(800)
    ) + ",)"

    import marshal, base64, zlib
    try:
        co = compile("x=" + "+".join(["1"]*200), "<v>", "exec")
        marshalled = marshal.dumps(co)
        corrupted = bytearray(marshalled)
        if len(corrupted) > 20:
            corrupted[16] = (corrupted[16] + 137) % 256
        bomb_b85 = base64.b85encode(zlib.compress(bytes(corrupted), 9)).decode()
    except Exception:
        bomb_b85 = ""

    stub_lines = [
        "import marshal as _apdc_ms,types as _apdc_ty,zlib as _apdc_zl,base64 as _apdc_b64",
        "def _apdc_crash():",
        " try:",
        "  def _apdc_rec(n):",
        "   if n<=0:return 0",
        "   return _apdc_rec(n-1)+1",
        "  import sys as _apdc_sys",
        "  _old_limit=_apdc_sys.getrecursionlimit()",
        "  _apdc_sys.setrecursionlimit(max(_old_limit,5000))",
        "  _apdc_rec(4999)",
        "  _apdc_sys.setrecursionlimit(_old_limit)",
        " except:pass",
        " try:",
        f"  _apdc_pool={big_consts}",
        "  del _apdc_pool",
        " except:pass",
    ]
    if bomb_b85:
        stub_lines += [
            " try:",
            f"  _apdc_raw=_apdc_zl.decompress(_apdc_b64.b85decode({bomb_b85!r}))",
            "  _apdc_ms.loads(_apdc_raw)",
            " except:pass",
        ]
    stub_lines += [
        " try:",
        "  import sys as _apdc_sv",
        "  _apdc_junk=b'\\x09\\x00'*2048",
        "  _apdc_args=[0,0,0,0,10,64,_apdc_junk,tuple('_k'+str(i) for i in range(50)),(),(),(),()] ",
        "  _apdc_ms.loads(_apdc_junk)",
        " except:pass",
        "try:_apdc_crash()",
        "except:pass",
        "del _apdc_crash,_apdc_ms,_apdc_ty,_apdc_zl,_apdc_b64",
    ]
    return "\n".join(stub_lines) + "\n"

def _build_antivm_stub() -> str:
    return r'''
import os as _vo
def _check_vm():
    _sn=__import__("platform").system()
    if _sn=="Windows":
        try:
            import ctypes as _vc
            _bk=_vc.windll.kernel32.GetTickCount64()
            if _bk<300000:_vo._exit(0)
        except:pass
        try:
            import winreg as _wr
            _vkeys=["SOFTWARE\\VMware, Inc.\\VMware Tools","SOFTWARE\\Oracle\\VirtualBox Guest Additions","SYSTEM\\CurrentControlSet\\Services\\VBoxGuest","SYSTEM\\CurrentControlSet\\Services\\vmci","SYSTEM\\CurrentControlSet\\Services\\vmhgfs"]
            for _vk in _vkeys:
                try:_wr.OpenKey(_wr.HKEY_LOCAL_MACHINE,_vk);_vo._exit(0)
                except:pass
        except:pass
        try:
            import subprocess as _sp
            _r=_sp.run(["wmic","bios","get","serialnumber"],capture_output=True,text=True,timeout=3).stdout.upper()
            if any(_x in _r for _x in["VMWARE","VBOX","8888888888","0000000000"]):_vo._exit(0)
        except:pass
        try:
            import subprocess as _sp2
            _r2=_sp2.run(["wmic","csproduct","get","name"],capture_output=True,text=True,timeout=3).stdout.lower()
            if any(_x in _r2 for _x in["virtual","vmware","virtualbox","qemu","xen"]):_vo._exit(0)
        except:pass
        try:
            import subprocess as _sp3
            _mc=_sp3.run(["getmac","/FO","CSV","/NH"],capture_output=True,text=True,timeout=3).stdout.lower()
            _vmp=("00:0c:29","00:50:56","00:05:69","08:00:27","52:54:00","00:15:5d")
            for _ml in _mc.splitlines():
                for _vp in _vmp:
                    if _vp in _ml:_vo._exit(0)
        except:pass
        try:
            _vf=["C:\\Windows\\System32\\vmGuestLib.dll","C:\\Windows\\System32\\vboxmrdnp.dll","C:\\Windows\\System32\\VBoxHook.dll"]
            for _fp in _vf:
                if _vo.path.exists(_fp):_vo._exit(0)
        except:pass
    elif _sn=="Linux":
        try:
            with open("/proc/cpuinfo") as _f:
                _ci=_f.read().lower()
                if any(_x in _ci for _x in["qemu","vmware","virtualbox","kvm","xen"]):_vo._exit(0)
        except:pass
        try:
            for _dp in("/sys/class/dmi/id/sys_vendor","/sys/class/dmi/id/board_vendor"):
                try:
                    with open(_dp) as _f2:
                        _sv=_f2.read().lower()
                        if any(_x in _sv for _x in["vmware","qemu","xen","innotek","parallels"]):_vo._exit(0)
                except:pass
        except:pass
        try:
            with open("/proc/1/cgroup") as _f3:
                _cg=_f3.read().lower()
                if "docker" in _cg or "lxc" in _cg or "kubepods" in _cg:_vo._exit(0)
        except:pass
        if _vo.path.exists("/.dockerenv"):_vo._exit(0)
        try:
            import subprocess as _sp4
            _dv=_sp4.run(["systemd-detect-virt"],capture_output=True,text=True,timeout=3).stdout.strip().lower()
            if _dv and _dv not in("none",""):_vo._exit(0)
        except:pass
        try:
            _ramkb=0
            with open("/proc/meminfo") as _f4:
                for _ln in _f4:
                    if _ln.startswith("MemTotal:"):_ramkb=int(_ln.split()[1]);break
            _cpuc=__import__("os").cpu_count() or 1
            if _cpuc<2 or _ramkb<2097152:_vo._exit(0)
        except:pass
    elif _sn=="Darwin":
        try:
            import subprocess as _sp5
            _mr=_sp5.run(["sysctl","-n","hw.model"],capture_output=True,text=True,timeout=3).stdout.lower()
            if any(_x in _mr for _x in["vmware","virtualbox","qemu","parallels"]):_vo._exit(0)
        except:pass
    try:
        import time as _vtm
        _t1=_vtm.perf_counter()
        for _ in range(10000):pass
        _t2=_vtm.perf_counter()
        if (_t2-_t1)>0.5:_vo._exit(0)
        del _vtm
    except:pass
try:_check_vm()
except:pass
del _check_vm,_vo
'''

def _build_antiproxy_stub() -> str:
    return r'''
import os as _vo
def _check_proxy():
    _env=_vo.environ
    _px_keys=["HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy","ALL_PROXY","all_proxy","SOCKS_PROXY","socks_proxy"]
    _bad_hosts=["127.0.0.1:8080","127.0.0.1:8000","127.0.0.1:9090","127.0.0.1:1080","localhost:8080","localhost:8000","localhost:9090","0.0.0.0:8080","0.0.0.0:8000"]
    _httptoolkit_markers=["httptoolkit","http-toolkit","http_toolkit"]
    for _pk in _px_keys:
        _pv=_env.get(_pk,"").lower()
        if _pv:
            for _bh in _bad_hosts:
                if _bh in _pv:_vo._exit(0)
            for _hm in _httptoolkit_markers:
                if _hm in _pv:_vo._exit(0)
    _cert_keys=["SSL_CERT_FILE","SSL_CERT_DIR","NODE_EXTRA_CA_CERTS","REQUESTS_CA_BUNDLE","CURL_CA_BUNDLE"]
    for _ck in _cert_keys:
        _cv=_env.get(_ck,"").lower()
        if _cv and any(_x in _cv for _x in _httptoolkit_markers+["mitmproxy","charles","fiddler","burp","proxyman"]):_vo._exit(0)
    if _env.get("HTTP_TOOLKIT_ACTIVE","").lower()=="true":_vo._exit(0)
    if _env.get("HTTP_TOOLKIT_INTERCEPTED",""):_vo._exit(0)
    try:
        import subprocess as _sp
        if __import__("sys").platform=="win32":
            _pr=_sp.run(["tasklist","/FO","CSV","/NH"],capture_output=True,text=True,timeout=3).stdout.lower()
        else:
            _pr=_sp.run(["ps","aux"],capture_output=True,text=True,timeout=3).stdout.lower()
        _bad_procs=["mitmproxy","mitmweb","mitmdump","charles","fiddler","burpsuite","httpdebugger","requestly","whistle","anyproxy","proxyman"]
        for _bp in _bad_procs:
            if _bp in _pr:_vo._exit(0)
        try:
            if __import__("sys").platform!="win32":
                import glob as _gl
                for _pid_path in _gl.glob("/proc/[0-9]*/exe"):
                    try:
                        _exe=__import__("os").readlink(_pid_path).lower()
                        for _bp2 in _bad_procs:
                            if _bp2 in _exe:_vo._exit(0)
                    except:pass
        except:pass
    except:pass
    try:
        import socket as _sk
        for _port in[8080,8888,9090,1080,8000,8443]:
            _s=_sk.socket(_sk.AF_INET,_sk.SOCK_STREAM)
            _s.settimeout(0.05)
            _r=_s.connect_ex(("127.0.0.1",_port))
            _s.close()
            if _r==0:
                try:
                    import http.client
                    _hc=http.client.HTTPConnection("127.0.0.1",_port,timeout=1)
                    _hc.request("CONNECT","example.com:443")
                    _rs=_hc.getresponse()
                    _hdict=dict(_rs.getheaders())
                    _all_h=" ".join(str(k)+":"+str(v) for k,v in _hdict.items()).lower()
                    if any(_x in _all_h for _x in["proxy-agent","via","x-forwarded","mitmproxy","charles","httptoolkit","burp"]):_vo._exit(0)
                except:pass
    except:pass
try:_check_proxy()
except:pass
del _check_proxy,_vo
'''


def _build_httptoolkit_stub() -> str:
    return r'''
import os as _vo
def _check_httptoolkit():
    _env=_vo.environ
    if _env.get("HTTP_TOOLKIT_ACTIVE","").lower()=="true":_vo._exit(0)
    if _env.get("HTTP_TOOLKIT_INTERCEPTED",""):_vo._exit(0)
    _p=_env.get("PATH","").lower()
    if "httptoolkit" in _p:_vo._exit(0)
    for _ek in["SSL_CERT_FILE","SSL_CERT_DIR","NODE_EXTRA_CA_CERTS","REQUESTS_CA_BUNDLE","CURL_CA_BUNDLE"]:
        _ev=_env.get(_ek,"").lower()
        if "httptoolkit" in _ev or "http-toolkit" in _ev:_vo._exit(0)
    for _pk in["HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy","ALL_PROXY","all_proxy"]:
        _pv=_env.get(_pk,"").lower()
        if "httptoolkit" in _pv:_vo._exit(0)
        if "127.0.0.1:8000" in _pv or "localhost:8000" in _pv:_vo._exit(0)
    try:
        import subprocess as _sp
        if __import__("sys").platform=="win32":
            _pr=_sp.run(["tasklist","/FO","CSV","/NH"],capture_output=True,text=True,timeout=3).stdout.lower()
        else:
            _pr=_sp.run(["ps","aux"],capture_output=True,text=True,timeout=3).stdout.lower()
        if "httptoolkit" in _pr:_vo._exit(0)
    except:pass
    try:
        import pathlib as _pl
        _homedir=_pl.Path.home()
        _ht_dirs=[_homedir/".http-toolkit",_homedir/".httptoolkit",_homedir/"AppData"/"Roaming"/"httptoolkit",_homedir/".config"/"httptoolkit"]
        for _hd in _ht_dirs:
            if _hd.exists():_vo._exit(0)
        del _pl,_homedir,_ht_dirs
    except:pass
    try:
        import socket as _sk
        _s=_sk.socket(_sk.AF_INET,_sk.SOCK_STREAM)
        _s.settimeout(0.05)
        _r=_s.connect_ex(("127.0.0.1",8000))
        _s.close()
        if _r==0:
            try:
                import http.client
                _hc=http.client.HTTPConnection("127.0.0.1",8000,timeout=1)
                _hc.request("GET","http://httpbin.org/get")
                _rs=_hc.getresponse()
                _hd2=dict(_rs.getheaders())
                _all=" ".join(str(k)+":"+str(v) for k,v in _hd2.items()).lower()
                if "httptoolkit" in _all or "proxy" in _all:_vo._exit(0)
            except:pass
        del _sk,_s
    except:pass
try:_check_httptoolkit()
except:pass
del _check_httptoolkit,_vo
'''


_BURN_SRC = (
    "def _vburn():\n"
    " import threading as _vth,os as _vbos,signal as _vsig,sys as _vbsy\n"
    " _vstop=[False]\n"
    " def _vhandler(s,f):\n"
    "  _vstop[0]=True\n"
    " try:\n"
    "  _vsig.signal(_vsig.SIGINT,_vhandler)\n"
    "  _vsig.signal(_vsig.SIGTERM,_vhandler)\n"
    " except:pass\n"
    " def _veater():\n"
    "  _vx=0\n"
    "  try:\n"
    "   while not _vstop[0]:\n"
    "    for _vi in range(10**5):_vx=(_vx+_vi)&0xFFFFFFFF\n"
    "  except:pass\n"
    " _vcpu=min(max((_vbos.cpu_count() or 2),2),8)\n"
    " _vts=[_vth.Thread(target=_veater,daemon=True) for _ in range(_vcpu)]\n"
    " [_vt.start() for _vt in _vts]\n"
    " try:\n"
    "  import time as _vtm\n"
    "  for _ in range(20):\n"
    "   if _vstop[0]:break\n"
    "   _vtm.sleep(0.5)\n"
    " except:pass\n"
    " try:\n"
    "  import signal as _vs2\n"
    "  _vbos.kill(_vbos.getpid(),_vs2.SIGTERM)\n"
    " except:pass\n"
    " try:\n"
    "  if _vbsy.platform=='win32':\n"
    "   import ctypes as _vwct\n"
    "   _vwct.windll.kernel32.TerminateProcess(-1,137)\n"
    " except:pass\n"
    " _vbos._exit(137)\n"
)

_COMMENT_SENTINEL = (
    "# +-----------------------------------------------------------+\n"
    "# |               DO NOT EDIT CODE ABOVE                      |\n"
    "# +-----------------------------------------------------------+\n"
)
_COMMENT_SIG = "# |               DO NOT EDIT CODE ABOVE                      |"


_INLINE_AES_SRC = r'''
_AES_SB=[0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16]
_AES_RC=[0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36,0x6c,0xd8,0xab,0x4d,0x9a,0x2f]
def _axt(a):return((a<<1)^0x1b)&0xff if a&0x80 else(a<<1)&0xff
def _akx(key):
 w=list(key)
 for i in range(8,60):
  t=w[(i-1)*4:i*4]
  if i%8==0:t=[_AES_SB[t[1]]^_AES_RC[i//8-1],_AES_SB[t[2]],_AES_SB[t[3]],_AES_SB[t[0]]]
  elif i%8==4:t=[_AES_SB[b] for b in t]
  for j in range(4):w.append(w[(i-8)*4+j]^t[j])
 return [w[i*4:(i+1)*4] for i in range(60)]
def _aeb(block,ek):
 s=[[block[i*4+j] for j in range(4)] for i in range(4)]
 rk=[[ek[i][j] for j in range(4)] for i in range(4)]
 for i in range(4):
  for j in range(4):s[i][j]^=rk[i][j]
 for r in range(1,14):
  for i in range(4):
   for j in range(4):s[i][j]=_AES_SB[s[i][j]]
  s[1]=s[1][1:]+s[1][:1];s[2]=s[2][2:]+s[2][:2];s[3]=s[3][3:]+s[3][:3]
  for ci in range(4):
   col=[s[j][ci] for j in range(4)]
   a=col[:]
   col[0]=_axt(a[0])^_axt(a[1])^a[1]^a[2]^a[3]
   col[1]=a[0]^_axt(a[1])^_axt(a[2])^a[2]^a[3]
   col[2]=a[0]^a[1]^_axt(a[2])^_axt(a[3])^a[3]
   col[3]=_axt(a[0])^a[0]^a[1]^a[2]^_axt(a[3])
   for j in range(4):s[j][ci]=col[j]
  rk=[[ek[r*4+i][j] for j in range(4)] for i in range(4)]
  for i in range(4):
   for j in range(4):s[i][j]^=rk[i][j]
 for i in range(4):
  for j in range(4):s[i][j]=_AES_SB[s[i][j]]
 s[1]=s[1][1:]+s[1][:1];s[2]=s[2][2:]+s[2][:2];s[3]=s[3][3:]+s[3][:3]
 rk=[[ek[56+i][j] for j in range(4)] for i in range(4)]
 for i in range(4):
  for j in range(4):s[i][j]^=rk[i][j]
 return bytes(s[i][j] for j in range(4) for i in range(4))
def _gf128m(x,y):
 r=0
 for _ in range(128):
  if y&1:r^=x
  lsb=x&1;x>>=1
  if lsb:x^=(0xe1<<120)
  y>>=1
 return r
def _ghash(h,aad,ct):
 import struct as _st2
 if isinstance(h,bytes):h=int.from_bytes(h,'big')
 def p16(d):
  rv=len(d)%16;return d+b'\x00'*(16-rv if rv else 0)
 X=0
 for chunk in[p16(aad),p16(ct)]:
  for i in range(0,len(chunk),16):
   X=_gf128m(X^int.from_bytes(chunk[i:i+16],'big'),h)
 lengths=_st2.pack('>QQ',len(aad)*8,len(ct)*8)
 X=_gf128m(X^int.from_bytes(lengths,'big'),h)
 return X.to_bytes(16,'big')
def _agd(key,iv,ct,tag,aad=b'vanish-v8-aad'):
 import struct as _st2,hmac as _hm,hashlib as _hh
 ek=_akx(list(key))
 hb=_aeb(b'\x00'*16,ek)
 etag=_ghash(hb,aad,ct)
 j0=iv+b'\x00\x00\x00\x01';j0e=_aeb(j0,ek)
 etag=bytes(a^b for a,b in zip(etag,j0e))
 if not _hm.compare_digest(etag,tag):raise ValueError('AES-GCM tag fail')
 def cb(c):return _aeb(iv+_st2.pack('>I',c),ek)
 pt=bytearray()
 for i in range(0,len(ct),16):
  ks=cb(i//16+2);ch=ct[i:i+16];pt.extend(b^k for b,k in zip(ch,ks))
 return bytes(pt)
'''

_INLINE_CHACHA_SRC = r'''
def _cc20q(a,b,c,d):
 a=(a+b)&0xFFFFFFFF;d^=a;d=((d<<16)|(d>>16))&0xFFFFFFFF
 c=(c+d)&0xFFFFFFFF;b^=c;b=((b<<12)|(b>>20))&0xFFFFFFFF
 a=(a+b)&0xFFFFFFFF;d^=a;d=((d<<8)|(d>>24))&0xFFFFFFFF
 c=(c+d)&0xFFFFFFFF;b^=c;b=((b<<7)|(b>>25))&0xFFFFFFFF
 return a,b,c,d
def _cc20b(key,ctr,nonce):
 import struct as _st3
 cs=b'expand 32-byte k'
 st=list(_st3.unpack('<4I',cs))+list(_st3.unpack('<8I',key))+[ctr]+list(_st3.unpack('<3I',nonce))
 w=st[:]
 for _ in range(10):
  w[0],w[4],w[8],w[12]=_cc20q(w[0],w[4],w[8],w[12])
  w[1],w[5],w[9],w[13]=_cc20q(w[1],w[5],w[9],w[13])
  w[2],w[6],w[10],w[14]=_cc20q(w[2],w[6],w[10],w[14])
  w[3],w[7],w[11],w[15]=_cc20q(w[3],w[7],w[11],w[15])
  w[0],w[5],w[10],w[15]=_cc20q(w[0],w[5],w[10],w[15])
  w[1],w[6],w[11],w[12]=_cc20q(w[1],w[6],w[11],w[12])
  w[2],w[7],w[8],w[13]=_cc20q(w[2],w[7],w[8],w[13])
  w[3],w[4],w[9],w[14]=_cc20q(w[3],w[4],w[9],w[14])
 return _st3.pack('<16I',*((w[i]+st[i])&0xFFFFFFFF for i in range(16)))
def _cc20d(data,key,nonce):
 out=bytearray()
 for i,off in enumerate(range(0,len(data),64)):
  ks=_cc20b(key,i,nonce);ch=data[off:off+64];out.extend(b^k for b,k in zip(ch,ks))
 return bytes(out)
'''

_INLINE_HKDF_SRC = r'''
def _hkdf(ikm,length,salt,info):
 import hmac as _hm,hashlib as _hh
 if not salt:salt=b'\x00'*32
 prk=_hm.new(salt,ikm,_hh.sha256).digest()
 t=b'';okm=b'';i=1
 while len(okm)<length:
  t=_hm.new(prk,t+info+bytes([i]),_hh.sha256).digest();okm+=t;i+=1
 return okm[:length]
'''

_INLINE_XOR_SRC = r'''
def _xss(data,key):
 x=int.from_bytes(key[:8],'big') or 0xDEADBEEFCAFEBABE
 out=bytearray(len(data))
 for i,b in enumerate(data):
  x^=(x<<13)&0xFFFFFFFFFFFFFFFF;x^=x>>7;x^=(x<<17)&0xFFFFFFFFFFFFFFFF
  out[i]=b^(x&0xFF)
 return bytes(out)
'''

_INLINE_SHUF_SRC = r'''
def _bun(data,key):
 import random as _rnd,hashlib as _hh
 n=len(data)
 if not n:return data
 seed=int.from_bytes(_hh.sha256(key+b'permute_v8').digest()[:8],'big')
 rng=_rnd.Random(seed)
 idx=list(range(n));rng.shuffle(idx)
 out=bytearray(n)
 for np,op in enumerate(idx):out[op]=data[np]
 return bytes(out)
'''


def build_loader_v8(
    master_hex: str,
    salt_hex: str,
    core_encoded: str,
    py_ver: str,
    use_anti_debug: bool,
    use_anti_hook: bool,
    use_anti_frame: bool,
    hw_bind: bool,
    use_py_lock: bool,
    header_sha256: str,
    use_anti_pydc: bool = True,
) -> tuple:

    core_sha256 = hashlib.sha256(core_encoded.encode('ascii')).hexdigest()

    ad_block = ""
    if use_anti_debug:
        ad_block = (
            "if _vs.gettrace() is not None:_vo._exit(0)\n"
            "if _vs.getprofile() is not None:_vo._exit(0)\n"
            "_t0=__import__('time').perf_counter()\n"
            "_t0m=__import__('time').monotonic()\n"
            "for _vdm in ('pdb','debugpy','pydevd','bdb','pudb','ipdb','winpdb','rpdb','_pydevd_bundle','viztracer','pyinstrument'):\n"
            "    if _vdm in _vs.modules:_vo._exit(0)\n"
            "for _vev in ('PYTHONDEBUG','PYTHONINSPECT','PYTHONBREAKPOINT','PYCHARM_DEBUG','DEBUGPY_LAUNCHER_PORT','PYDEVD_USE_FRAME_EVAL','VSCODE_DEBUGGER'):\n"
            "    if _vo.environ.get(_vev):_vo._exit(0)\n"
            "_vsysn=__import__('platform').system()\n"
            "if _vsysn=='Windows':\n"
            "    try:\n"
            "        import ctypes as _vct\n"
            "        _vph=_vct.windll.kernel32.GetCurrentProcess()\n"
            "        if _vct.windll.kernel32.IsDebuggerPresent():_vo._exit(0)\n"
            "        _vrdb=_vct.c_bool(False)\n"
            "        _vct.windll.kernel32.CheckRemoteDebuggerPresent(_vph,_vct.byref(_vrdb))\n"
            "        if _vrdb.value:_vo._exit(0)\n"
            "        try:\n"
            "            _vnt=_vct.windll.ntdll;_vdp=_vct.c_ulong(0);_vrl=_vct.c_ulong(0)\n"
            "            _vnt.NtQueryInformationProcess.argtypes=[_vct.c_void_p,_vct.c_ulong,_vct.c_void_p,_vct.c_ulong,_vct.POINTER(_vct.c_ulong)]\n"
            "            _vnt.NtQueryInformationProcess.restype=_vct.c_long\n"
            "            if _vnt.NtQueryInformationProcess(_vph,7,_vct.byref(_vdp),4,_vct.byref(_vrl))==0 and _vdp.value:_vo._exit(0)\n"
            "        except:pass\n"
            "    except Exception:pass\n"
            "elif _vsysn=='Linux':\n"
            "    try:\n"
            "        _vtpid=0\n"
            "        with open('/proc/self/status') as _vpf:\n"
            "            for _vln in _vpf:\n"
            "                if _vln.startswith('TracerPid:'):\n"
            "                    _vtpid=int(_vln.split(':')[1].strip());break\n"
            "        if _vtpid!=0:\n"
            "            _vo._exit(0)\n"
            "    except:pass\n"
            "    try:\n"
            "        import socket as _sk\n"
            "        _fs=_sk.socket(_sk.AF_INET,_sk.SOCK_STREAM);_fs.settimeout(0.05)\n"
            "        if _fs.connect_ex(('127.0.0.1',27042))==0:_vo._exit(0)\n"
            "        _fs.close()\n"
            "    except:pass\n"
            "if (__import__('time').perf_counter()-_t0)>0.8:_vo._exit(0)\n"
            "del _vsysn\n"
        )

    ah_block = ""
    if use_anti_hook:
        ah_block = (
            "import builtins as _vbi,types as _vty\n"
            "for _vfn in ('exec','eval','compile','__import__','open','abs'):\n"
            "    _vff=getattr(_vbi,_vfn,None)\n"
            "    if _vff is None or not isinstance(_vff,_vty.BuiltinFunctionType):_vo._exit(0)\n"
            "del _vbi,_vty\n"
            "try:del _vfn,_vff\n"
            "except:pass\n"
            "_vbad=frozenset(('pydevd','debugpy','bdb','pdb','pudb','ipdb','winpdb','rpdb','frida','inject','hookimport','traceimport','monkeyimport'))\n"
            "for _vmc in _vs.meta_path:\n"
            "    _vmcn=(getattr(_vmc,'__name__',None) or type(_vmc).__name__).lower()\n"
            "    if any(_vb in _vmcn for _vb in _vbad):_vo._exit(0)\n"
            "del _vbad\n"
            "try:del _vmc,_vmcn\n"
            "except:pass\n"
        )

    py_lock_block = ""
    if use_py_lock:
        py_lock_block = (
            f"if f'{{_vs.version_info.major}}.{{_vs.version_info.minor}}'!={py_ver!r}:_vo._exit(1)\n"
        )

    if hw_bind:
        hw_block = (
            f"{_FP_FN_SRC}"
            "_vfp=_vhwf();del _vhwf,_vu,_vhpl,_vhh\n"
            "_vhwmask=__import__('hashlib').sha256(_vfp+b'VANISH_V8_HW').digest()[:32]\n"
            f"_vmk=bytes(_a^_b for _a,_b in zip(bytes.fromhex({master_hex!r}),_vhwmask))\n"
            "del _vfp,_vhwmask\n"
        )
    else:
        hw_block = (
            "_vmk_mask=__import__('hashlib').sha256(_vsl+b'VANISH_V8_MASTER_KEY_PROTECT').digest()[:32]\n"
            f"_vmk=bytes(_a^_b for _a,_b in zip(bytes.fromhex({master_hex!r}),_vmk_mask))\n"
            "del _vmk_mask\n"
        )

    salt_block = f"_vsl=bytes.fromhex({salt_hex!r})\n"

    tamper_block = (
        f"{_BURN_SRC}"
        "_vcore=globals().get('__VANISH_CORE__','')\n"
        "if not _vcore:_vburn()\n"
        f"if __import__('hashlib').sha256(_vcore.encode('ascii')).hexdigest()!={core_sha256!r}:_vburn()\n"
        "try:\n"
        "    import sys as _vfs\n"
        "    _vfpath=getattr(_vfs.modules.get('__main__'),'__file__',None) or _vfs.argv[0]\n"
        "    with open(_vfpath,'r',encoding='utf-8') as _vff2:\n"
        "        _vhlines=''.join([next(_vff2) for _ in range(5)])\n"
        f"    if __import__('hashlib').sha256(_vhlines.encode('utf-8')).hexdigest()!={header_sha256!r}:_vburn()\n"
        "    with open(_vfpath,'r',encoding='utf-8') as _vff3:\n"
        "        _vfcontent=_vff3.read()\n"
        f"    _vcmt_sig={_COMMENT_SIG!r}\n"
        "    if _vcmt_sig not in _vfcontent:_vburn()\n"
        "    del _vhlines,_vfpath,_vff2,_vff3,_vfcontent,_vcmt_sig,_vfs\n"
        "except (StopIteration,OSError):pass\n"
    )

    _pydc_inline = _build_antipycdc_stub().strip() + "\n" if use_anti_pydc else ""
    bootstrap = (
        "import sys as _vs,os as _vo,zlib as _vz,base64 as _vb\n"
        f"{_pydc_inline}"
        f"{ad_block}"
        f"{ah_block}"
        f"{py_lock_block}"
        f"{tamper_block}"
        f"{salt_block}"
        f"{hw_block}"
        f"{_INLINE_HKDF_SRC}"
        f"{_INLINE_AES_SRC}"
        f"{_INLINE_CHACHA_SRC}"
        f"{_INLINE_XOR_SRC}"
        f"{_INLINE_SHUF_SRC}"
        "_vaes_key=_hkdf(_vmk,32,_vsl+b'aes',b'aes256gcm-key-v8')\n"
        "_vcc_key=_hkdf(_vmk,32,_vsl+b'cc20',b'chacha20-key-v8')\n"
        "_vxor_key=_hkdf(_vmk,16,_vsl+b'xors',b'xorshift-key-v8')\n"
        "_vshuf_key=_hkdf(_vmk,16,_vsl+b'shuf',b'shuffle-key-v8')\n"
        "del _vmk,_vsl,_hkdf\n"
        "_vraw=_vb.b85decode(_vcore.encode('ascii'))\n"
        "del _vcore\n"
        "_vs1=_bun(_vraw,_vshuf_key);del _vraw,_bun,_vshuf_key\n"
        "_vs2=_xss(_vs1,_vxor_key);del _vs1,_xss,_vxor_key\n"
        "_vs3_blob=_vs2;del _vs2\n"
        "_nonce_cc=_vs3_blob[:12];_vs3_rest=_vs3_blob[12:]\n"
        "_vs4=_cc20d(_vs3_rest,_vcc_key,_nonce_cc);del _vs3_blob,_nonce_cc,_vs3_rest,_cc20d,_vcc_key\n"
        "_nonce_aes=_vs4[:12];_tag_aes=_vs4[12:28];_vs4_ct=_vs4[28:]\n"
        "_vs5=_agd(_vaes_key,_nonce_aes,_vs4_ct,_tag_aes);del _vs4,_nonce_aes,_tag_aes,_vs4_ct,_agd,_vaes_key\n"
        "_vpkg=_vz.decompress(_vs5)\n"
        "__import__('gc').collect()\n"
        "del _vs5,_vz,_vb,_vs\n"
        f"{RUNTIME_CORE}"
        "_b8().run(_vpkg)\n"
    )

    bootstrap_bytes = bootstrap.encode('utf-8')
    bootstrap_encoded = base64.b85encode(
        zlib.compress(bootstrap_bytes, level=9)
    ).decode('ascii')

    core_line = f"__VANISH_CORE__='{core_encoded}'"
    exec_line = f"exec(__import__('zlib').decompress(__import__('base64').b85decode(b'{bootstrap_encoded}')))"

    return core_line, exec_line


def obfuscate(
    source: str,
    use_anti_debug: bool = True,
    use_anti_hook: bool = True,
    use_junk: bool = True,
    use_anti_frame: bool = True,
    hw_bind: bool = False,
    use_py_lock: bool = False,
    use_anti_vm: bool = True,
    use_anti_proxy: bool = True,
    use_anti_httptoolkit: bool = True,
    use_anti_pydc: bool = True,
) -> str:
    _reset_names()

    source = source.lstrip('\ufeff')
    source = re.sub(r'^[ \t]*#.*coding.*$', '', source, flags=re.MULTILINE)

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in source: {e}")

    first_lines = []
    while tree.body and isinstance(tree.body[0], ast.ImportFrom) and getattr(tree.body[0], 'module', '') == '__future__':
        first_lines.append(tree.body.pop(0))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            while (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body.pop(0)
                if not node.body:
                    node.body.append(ast.Pass(lineno=1, col_offset=0))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.returns = None
            if node.args:
                for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                    arg.annotation = None
                if node.args.vararg:
                    node.args.vararg.annotation = None
                if node.args.kwarg:
                    node.args.kwarg.annotation = None
    tree.body = first_lines + tree.body
    ast.fix_missing_locations(tree)

    coll = NameCollector()
    coll.visit(tree)
    nm = {n: rand_confuse_name() for n in coll.safe_names()
          if n not in PYTHON_BUILTINS and not n.startswith('__')}

    tree = VariableRenamer(nm).visit(tree)
    ast.fix_missing_locations(tree)

    str_key = random.randint(1, 250)
    tree = StringEncryptor(str_key).visit(tree)
    ast.fix_missing_locations(tree)

    tree = IntObfuscator().visit(tree)
    ast.fix_missing_locations(tree)

    if use_junk:
        count = random.randint(14, 22)
        for jf in make_junk_functions(count=count):
            pos = random.randint(0, len(tree.body))
            tree.body.insert(pos, jf)
        ast.fix_missing_locations(tree)

    if len(tree.body) >= 3:
        try:
            tree = flatten_control_flow(tree)
        except Exception:
            pass
    ast.fix_missing_locations(tree)

    try:
        transformed = ast.unparse(tree)
    except Exception as e:
        warnings.warn(f"ast.unparse failed: {e}, using raw source (protection LOST)")
        transformed = source

    parts = []
    if use_anti_pydc:
        parts.append(_build_antipycdc_stub().strip())
    if use_anti_debug:
        parts.append(_ANTI_DEBUG_STUB.strip())
    if use_anti_hook:
        parts.append(_ANTI_HOOK_STUB.strip())
    if use_anti_frame:
        parts.append(_ANTI_FRAME_STUB.strip())
    if use_anti_vm:
        parts.append(_build_antivm_stub().strip())
    if use_anti_proxy:
        parts.append(_build_antiproxy_stub().strip())
    if use_anti_httptoolkit:
        parts.append(_build_httptoolkit_stub().strip())
    if parts:
        protected_source = '\n'.join(parts) + '\n' + transformed
    else:
        protected_source = transformed

    for attempt_source in [protected_source, transformed, source]:
        try:
            core_encoded, master_hex, salt_hex, py_ver = build_payload_v8(
                attempt_source, hw_bind=hw_bind)
            break
        except SyntaxError:
            continue
    else:
        raise RuntimeError("All compile attempts failed - unfixable syntax errors")
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    flags = (
        f"HW:{'ON' if hw_bind else 'OFF'} "
        f"AD:{'ON' if use_anti_debug else 'OFF'} "
        f"AH:{'ON' if use_anti_hook else 'OFF'} "
        f"AF:{'ON' if use_anti_frame else 'OFF'} "
        f"JK:{'ON' if use_junk else 'OFF'} "
        f"VM:{'ON' if use_anti_vm else 'OFF'} "
        f"PX:{'ON' if use_anti_proxy else 'OFF'} "
        f"HT:{'ON' if use_anti_httptoolkit else 'OFF'} "
        f"DC:{'ON' if use_anti_pydc else 'OFF'} "
        f"PY:{py_ver} BVM:v8"
    )

    header_lines = [
        '__OBF__ = "vanish"',
        '__OWN__ = "Truong Nhat Bao Nam - ktn1703"',
        f'__MODE__ = "{flags}"',
        f'__DATE__ = "{ts}"',
        '__CMT__ = "Don\'t Read This Code Because You Will Be Dizzy By My Magic!"',
    ]
    header_block = '\n'.join(header_lines) + '\n'
    header_sha256 = hashlib.sha256(header_block.encode('utf-8')).hexdigest()

    core_line, exec_line = build_loader_v8(
        master_hex=master_hex,
        salt_hex=salt_hex,
        core_encoded=core_encoded,
        py_ver=py_ver,
        use_anti_debug=use_anti_debug,
        use_anti_hook=use_anti_hook,
        use_anti_frame=use_anti_frame,
        hw_bind=hw_bind,
        use_py_lock=use_py_lock,
        header_sha256=header_sha256,
        use_anti_pydc=use_anti_pydc,
    )

    output = (
        header_block
        + core_line + '\n'
        + exec_line + '\n'
        + _COMMENT_SENTINEL
    )
    try:
        compile(output, '<verify>', 'exec')
    except SyntaxError as ve:
        raise RuntimeError(f"Output syntax error: {ve}")
    return output

def _box_line(label: str, value: str, label_col: str = _CYN, val_col: str = _YLW) -> None:
    if _TC:
        print(f"  {_MAG}╠{_R} {label_col}{label:<46}{_R} {val_col}{value}{_R}")
    else:
        print(f"  | {label:<46} {value}")


def run_obfuscation(
    input_path: Path,
    output_path: Path = None,
    use_anti_debug: bool = True,
    use_anti_hook: bool = True,
    use_anti_frame: bool = True,
    use_junk: bool = True,
    hw_bind: bool = False,
    use_py_lock: bool = False,
    silent: bool = False,
    use_anti_vm: bool = True,
    use_anti_proxy: bool = True,
    use_anti_httptoolkit: bool = True,
    use_anti_pydc: bool = True,
) -> bool:
    try:
        source = input_path.read_text(encoding='utf-8')
    except Exception as e:
        if not silent:
            cprint(f"  [x] Cannot read file: {e}", "red")
        return False

    if not source.strip():
        if not silent:
            cprint("  [x] File is empty.", "red")
        return False

    original_size = len(source.encode('utf-8'))

    if output_path is None:
        output_path = input_path.with_stem(input_path.stem + '_obf')

    t0 = time.perf_counter()
    try:
        result = obfuscate(
            source,
            use_anti_debug=use_anti_debug,
            use_anti_hook=use_anti_hook,
            use_junk=use_junk,
            use_anti_frame=use_anti_frame,
            hw_bind=hw_bind,
            use_py_lock=use_py_lock,
            use_anti_vm=use_anti_vm,
            use_anti_proxy=use_anti_proxy,
            use_anti_httptoolkit=use_anti_httptoolkit,
            use_anti_pydc=use_anti_pydc,
        )
    except Exception as e:
        if not silent:
            cprint(f"\n  [x] Obfuscation failed: {e}", "red")
            import traceback
            traceback.print_exc()
        return False
    elapsed = time.perf_counter() - t0

    try:
        output_path.write_text(result, encoding='utf-8')
    except Exception as e:
        if not silent:
            cprint(f"\n  [x] Cannot write output: {e}", "red")
        return False

    if not silent:
        obf_size  = len(result.encode('utf-8'))
        ratio_pct = obf_size / max(original_size, 1) * 100
        if _TC:
            print(f"  {_GRN}+{_R} {_WHT}{input_path.name}{_R} -> {_CYN}{output_path.name}{_R}  "
                  f"{_DIM}{original_size:,}->{obf_size:,} bytes ({ratio_pct:.0f}%){_R}  "
                  f"{_YLW}{elapsed:.2f}s{_R}")
        else:
            print(f"  + {input_path.name} -> {output_path.name}  "
                  f"{original_size:,}->{obf_size:,} bytes ({ratio_pct:.0f}%)  {elapsed:.2f}s")

    return True


def main():
    parser = argparse.ArgumentParser(
        prog='vanish',
        description='Vanish v1.0 - Python Obfuscator',
        add_help=True,
    )
    parser.add_argument('--file', '-f', type=str, help='Input Python file path')
    parser.add_argument('--output', '-o', type=str, help='Output file path')
    parser.add_argument('--no-anti-debug', action='store_true', help='Disable anti-debug')
    parser.add_argument('--no-anti-hook',  action='store_true', help='Disable anti-hook')
    parser.add_argument('--no-anti-frame', action='store_true', help='Disable anti-frame')
    parser.add_argument('--no-junk',       action='store_true', help='Disable junk injection')
    parser.add_argument('--hw-bind',       action='store_true', help='Enable hardware binding')
    parser.add_argument('--py-lock',       action='store_true', help='Lock to current Python version')
    parser.add_argument('--silent',        action='store_true', help='No output')
    parser.add_argument('--banner',        action='store_true', help='Show banner')
    parser.add_argument('--no-anti-vm',          action='store_true', help='Disable anti-VM detection')
    parser.add_argument('--no-anti-proxy',       action='store_true', help='Disable anti-proxy detection')
    parser.add_argument('--no-anti-httptoolkit', action='store_true', help='Disable anti-HTTP Toolkit')
    parser.add_argument('--no-anti-pydc',        action='store_true', help='Disable anti-decompiler crash')

    args, _ = parser.parse_known_args()

    if args.file:
        if args.banner:
            print_banner()
        input_path = Path(args.file)
        if not input_path.exists():
            cprint(f"  [x] File not found: {input_path}", "red")
            sys.exit(1)
        output_path = Path(args.output) if args.output else None
        ok = run_obfuscation(
            input_path=input_path,
            output_path=output_path,
            use_anti_debug=not args.no_anti_debug,
            use_anti_hook=not args.no_anti_hook,
            use_anti_frame=not args.no_anti_frame,
            use_junk=not args.no_junk,
            hw_bind=args.hw_bind,
            use_py_lock=args.py_lock,
            silent=args.silent,
            use_anti_vm=not args.no_anti_vm,
            use_anti_proxy=not args.no_anti_proxy,
            use_anti_httptoolkit=not args.no_anti_httptoolkit,
            use_anti_pydc=not args.no_anti_pydc,
        )
        sys.exit(0 if ok else 1)

    print_banner()

    sep = "─" * 60
    print(f"  {_pystyle_gradient(sep)}")
    print(f"  {_pystyle_gradient('  >> Protection Setup')}")
    print(f"  {_pystyle_gradient(sep)}")
    print()

    input_file = ask("Input Python file path")
    if not input_file:
        cprint("\n  [x] No file specified. Exiting.", "red")
        sys.exit(1)

    input_path = Path(input_file.strip())
    if not input_path.exists():
        cprint(f"\n  [x] File not found: {input_path}", "red")
        sys.exit(1)

    print(f"  {_GRN}+{_R} File found: {_CYN}{input_path}{_R}")
    print()

    def yn(prompt: str, default: bool = True) -> bool:
        hint = f"{'Y' if default else 'y'}/{'n' if default else 'N'}"
        raw = ask(f"{prompt} [{hint}]")
        if not raw:
            return default
        return raw.upper() in ('Y', 'YES', '1', 'TRUE')

    use_anti_debug      = yn("Anti-debug protection?", default=True)
    use_anti_hook       = yn("Anti-hook protection?",  default=True)
    use_anti_frame      = yn("Anti-frame / GC wipe?",  default=True)
    use_junk            = yn("Inject opaque junk code?", default=True)
    hw_bind             = yn("Hardware-key binding (locks to THIS machine)?", default=False)
    use_py_lock         = yn("Lock to current Python version?", default=False)
    use_anti_vm         = yn("Anti-VM / sandbox detection?", default=True)
    use_anti_proxy      = yn("Anti-proxy / MITM detection?", default=True)
    use_anti_httptoolkit= yn("Anti-HTTP Toolkit detection?", default=True)
    use_anti_pydc       = yn("Anti-decompiler (pycdc crash)?", default=True)

    print()
    print(f"  {_pystyle_gradient(sep)}")
    print(f"  {_pystyle_gradient('  >> Selected options')}")
    print(f"  {_pystyle_gradient(sep)}")

    def _bool_tag(v: bool) -> str:
        if _TC:
            return f"{_GRN}ON{_R} " if v else f"{_DRED}OFF{_R}"
        return "ON" if v else "OFF"

    _box_line("Anti-Debug",       _bool_tag(use_anti_debug))
    _box_line("Anti-Hook",        _bool_tag(use_anti_hook))
    _box_line("Anti-Frame",       _bool_tag(use_anti_frame))
    _box_line("Junk Code",        _bool_tag(use_junk))
    _box_line("HW Binding",       _bool_tag(hw_bind))
    _box_line("Python Lock",      _bool_tag(use_py_lock))
    _box_line("Anti-VM",          _bool_tag(use_anti_vm))
    _box_line("Anti-Proxy",       _bool_tag(use_anti_proxy))
    _box_line("Anti-HTTPTK",      _bool_tag(use_anti_httptoolkit))
    _box_line("Anti-Decompiler",  _bool_tag(use_anti_pydc))
    _box_line("5-Layer Crypto",   "ALWAYS ON")
    _box_line("HKDF-SHA256",      "ALWAYS ON")
    _box_line("BVM v8 Engine",    "ALWAYS ON")
    _box_line("MBA Obfuscation",  "ALWAYS ON")
    _box_line("String Encrypt",   "ALWAYS ON")
    _box_line("Tamper Guard",     "ALWAYS ON")

    print(f"  {_pystyle_gradient(sep)}")
    print()

    try:
        source = input_path.read_text(encoding='utf-8')
    except Exception as e:
        cprint(f"  [x] Cannot read file: {e}", "red")
        sys.exit(1)

    if not source.strip():
        cprint("  [x] File is empty.", "red")
        sys.exit(1)

    original_size = len(source.encode('utf-8'))

    print(f"  {_pystyle_gradient(sep)}")
    print(f"  {_pystyle_gradient(f'  >> Obfuscating  ({original_size:,} bytes)')}")
    print(f"  {_pystyle_gradient(sep)}")

    steps = [
        "Cleaning source...",
        "Renaming identifiers...",
        "Encrypting strings...",
        "Obfuscating integers...",
        "Injecting junk code...",
        "Flattening control flow...",
        "Adding anti-analysis...",
        "BVM lift...",
        "Deriving keys...",
        "Encrypting payload...",
        "Building loader...",
    ]
    for desc in steps:
        if _TC:
            print(f"  {_CYN}>{_R}  {_gradient(desc, _PAL_STEP)}")
        else:
            print(f"  >  {desc}")
        time.sleep(0.03)

    print()
    print(f"  {_YLW}Running...{_R}")

    t0 = time.perf_counter()
    try:
        result = obfuscate(
            source,
            use_anti_debug=use_anti_debug,
            use_anti_hook=use_anti_hook,
            use_junk=use_junk,
            use_anti_frame=use_anti_frame,
            hw_bind=hw_bind,
            use_py_lock=use_py_lock,
            use_anti_vm=use_anti_vm,
            use_anti_proxy=use_anti_proxy,
            use_anti_httptoolkit=use_anti_httptoolkit,
            use_anti_pydc=use_anti_pydc,
        )
    except Exception as e:
        cprint(f"\n  [x] Obfuscation failed: {e}", "red")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    elapsed = time.perf_counter() - t0

    out_path = input_path.with_stem(input_path.stem + '_obf')
    try:
        out_path.write_text(result, encoding='utf-8')
    except Exception as e:
        cprint(f"\n  [x] Cannot write output: {e}", "red")
        sys.exit(1)

    obf_size  = len(result.encode('utf-8'))
    ratio_pct = obf_size / max(original_size, 1) * 100

    print()
    print(f"  {_pystyle_gradient(sep)}")
    print(f"  {_pystyle_gradient('  >> Done!')}")
    print(f"  {_pystyle_gradient(sep)}")
    print(f"  {_GRN}+{_R} Saved: {_CYN}{out_path}{_R}")
    print(f"  {_GRN}+{_R} {original_size:,} -> {obf_size:,} bytes ({ratio_pct:.0f}%)")
    print(f"  {_GRN}+{_R} Time: {_YLW}{elapsed:.3f}s{_R}")
    print(f"  {_pystyle_gradient(sep)}")
    print(f"  {_RED}[LOCK]{_R} Tamper-burn active")
    print(f"  {_RED}[LOCK]{_R} 5-Layer AES-GCM + ChaCha20")
    print(f"  {_RED}[LOCK]{_R} BVM poly-opcode engine")
    print(f"  {_YLW}[WARN]{_R} Keep original. Obfuscated = deploy only.")
    print(f"  {_pystyle_gradient(sep)}")
    print()


if __name__ == '__main__':
    main()
