#!/usr/bin/env python3
import ast
import dis
import io
import random
import struct
import types
import marshal

BVM_MAGIC = b'VANISH_SUPREME_V8'
BVM_VER = b'\x08\x00\xff\xbb'
INT_XOR = 0x6A4F9E3C1B7D5A82
STR_XOR = 0xC3

_T_NONE      = 0x00
_T_TRUE      = 0x01
_T_FALSE     = 0x02
_T_INT       = 0x03
_T_FLOAT     = 0x04
_T_STR       = 0x05
_T_BYTES     = 0x06
_T_TUPLE     = 0x07
_T_CODE      = 0x08
_T_MARSHAL   = 0x09
_T_COMPLEX   = 0x0A
_T_LIST      = 0x0B
_T_SET       = 0x0C
_T_FROZENSET = 0x0D
_T_DICT      = 0x0E
_T_ELLIPSIS  = 0x0F
_T_SLICE     = 0x10
_T_BYTEARRAY = 0x11

BIN_MAP = {
    ast.Add: 0, ast.Sub: 1, ast.Mult: 2, ast.Div: 3,
    ast.FloorDiv: 4, ast.Mod: 5, ast.Pow: 6,
}
CMP_MAP = {
    ast.Eq: 0, ast.NotEq: 1, ast.Lt: 2, ast.LtE: 3,
    ast.Gt: 4, ast.GtE: 5, ast.Is: 6, ast.IsNot: 7,
    ast.In: 8, ast.NotIn: 9,
}


def _scramble(data, seed):
    x = (seed & 0xFFFFFFFFFFFFFFFF) or 0xDEADBEEFCAFEBABE
    out = bytearray(len(data))
    for i, b in enumerate(data):
        x ^= (x << 13) & 0xFFFFFFFFFFFFFFFF
        x ^= x >> 7
        x ^= (x << 17) & 0xFFFFFFFFFFFFFFFF
        out[i] = b ^ (x & 0xFF)
    return bytes(out)


_unscramble = _scramble


def _op_starts(co):
    skip = frozenset({'CACHE', 'COPY', 'INTRINSIC_1', 'INTRINSIC_2'})
    try:
        return {ins.offset for ins in dis.Bytecode(co) if ins.opname not in skip}
    except Exception:
        return set()


def _build_op_len_map():
    m = {}
    for name in dir(dis):
        if name.startswith('opmap') or name == 'opmap':
            opmap = getattr(dis, name)
            if isinstance(opmap, dict):
                for opname, opcode in opmap.items():
                    if opname == 'CACHE':
                        m[opcode] = 2
                    elif opcode >= dis.HAVE_ARGUMENT:
                        m[opcode] = 2
                    else:
                        m[opcode] = 1
                return m
    return {}


_OP_LEN_MAP = _build_op_len_map()


def _swap_ops(raw, starts):
    raw = bytearray(raw)
    fwd = {}
    rev = {}
    for pos in sorted(starts):
        if pos >= len(raw):
            continue
        b = raw[pos]
        b_len = _OP_LEN_MAP.get(b, 2)
        if b not in fwd:
            for _ in range(1000):
                nb = random.randint(1, 254)
                nb_len = _OP_LEN_MAP.get(nb, 2)
                if nb_len == b_len and nb not in rev:
                    break
            else:
                continue
            fwd[b] = nb
            rev[nb] = b
        raw[pos] = fwd[b]
    return bytes(raw), rev


def _restore_ops(raw, starts, rev):
    raw = bytearray(raw)
    for pos in starts:
        if pos < len(raw):
            b = raw[pos]
            if b in rev:
                raw[pos] = rev[b]
    return bytes(raw)


def pack_consts(vals):
    out = io.BytesIO()
    for v in vals:
        try:
            _pack_one(out, v)
        except Exception:
            try:
                m = marshal.dumps(v)
                out.write(bytes([_T_MARSHAL]) + struct.pack('>I', len(m)) + m)
            except Exception:
                out.write(bytes([_T_NONE]))
    return out.getvalue()


def _pack_one(out, v):
    if v is None:
        out.write(bytes([_T_NONE]))
    elif v is Ellipsis:
        out.write(bytes([_T_ELLIPSIS]))
    elif v is True:
        out.write(bytes([_T_TRUE]))
    elif v is False:
        out.write(bytes([_T_FALSE]))
    elif isinstance(v, int):
        if -(2**63) <= v <= 2**63 - 1:
            out.write(bytes([_T_INT]) + struct.pack('>q', v ^ INT_XOR))
        else:
            m = marshal.dumps(v)
            out.write(bytes([_T_MARSHAL]) + struct.pack('>I', len(m)) + m)
    elif isinstance(v, float):
        out.write(bytes([_T_FLOAT]) + struct.pack('>d', v))
    elif isinstance(v, complex):
        out.write(bytes([_T_COMPLEX]) + struct.pack('>dd', v.real, v.imag))
    elif isinstance(v, str):
        raw = v.encode('utf-8')
        enc = bytes(b ^ STR_XOR for b in raw)
        out.write(bytes([_T_STR]) + struct.pack('>I', len(enc)) + enc)
    elif isinstance(v, bytes):
        enc = bytes(b ^ STR_XOR for b in v)
        out.write(bytes([_T_BYTES]) + struct.pack('>I', len(enc)) + enc)
    elif isinstance(v, slice):
        out.write(bytes([_T_SLICE]))
        _pack_one(out, v.start)
        _pack_one(out, v.stop)
        _pack_one(out, v.step)
    elif isinstance(v, bytearray):
        enc = bytes(b ^ STR_XOR for b in v)
        out.write(bytes([_T_BYTEARRAY]) + struct.pack('>I', len(enc)) + enc)
    elif isinstance(v, tuple):
        out.write(bytes([_T_TUPLE]) + struct.pack('>I', len(v)))
        for e in v:
            _pack_one(out, e)
    elif isinstance(v, list):
        out.write(bytes([_T_LIST]) + struct.pack('>I', len(v)))
        for e in v:
            _pack_one(out, e)
    elif isinstance(v, frozenset):
        items = sorted(v, key=lambda x: repr(x))
        out.write(bytes([_T_FROZENSET]) + struct.pack('>I', len(items)))
        for e in items:
            _pack_one(out, e)
    elif isinstance(v, set):
        items = sorted(v, key=lambda x: repr(x))
        out.write(bytes([_T_SET]) + struct.pack('>I', len(items)))
        for e in items:
            _pack_one(out, e)
    elif isinstance(v, dict):
        out.write(bytes([_T_DICT]) + struct.pack('>I', len(v)))
        for k, val in v.items():
            _pack_one(out, k)
            _pack_one(out, val)
    elif isinstance(v, types.CodeType):
        try:
            sub = pack_co(v)
            out.write(bytes([_T_CODE]) + struct.pack('>I', len(sub)) + sub)
        except Exception:
            m = marshal.dumps(v)
            out.write(bytes([_T_MARSHAL]) + struct.pack('>I', len(m)) + m)
    else:
        try:
            m = marshal.dumps(v)
            out.write(bytes([_T_MARSHAL]) + struct.pack('>I', len(m)) + m)
        except Exception:
            out.write(bytes([_T_NONE]))


def unpack_consts(data):
    stream = io.BytesIO(data)
    end = len(data)
    out = []
    while stream.tell() < end:
        out.append(_unpack_one(stream))
    return out


def _unpack_one(h):
    t = h.read(1)
    if not t:
        return None
    t = t[0]
    if t == _T_NONE:
        return None
    if t == _T_ELLIPSIS:
        return ...
    if t == _T_TRUE:
        return True
    if t == _T_FALSE:
        return False
    if t == _T_INT:
        return struct.unpack('>q', h.read(8))[0] ^ INT_XOR
    if t == _T_FLOAT:
        return struct.unpack('>d', h.read(8))[0]
    if t == _T_COMPLEX:
        r, i = struct.unpack('>dd', h.read(16))
        return complex(r, i)
    if t == _T_STR:
        n = struct.unpack('>I', h.read(4))[0]
        return bytes(b ^ STR_XOR for b in h.read(n)).decode('utf-8')
    if t == _T_BYTES:
        n = struct.unpack('>I', h.read(4))[0]
        return bytes(b ^ STR_XOR for b in h.read(n))
    if t == _T_BYTEARRAY:
        n = struct.unpack('>I', h.read(4))[0]
        return bytearray(b ^ STR_XOR for b in h.read(n))
    if t == _T_TUPLE:
        n = struct.unpack('>I', h.read(4))[0]
        return tuple(_unpack_one(h) for _ in range(n))
    if t == _T_LIST:
        n = struct.unpack('>I', h.read(4))[0]
        return [_unpack_one(h) for _ in range(n)]
    if t == _T_FROZENSET:
        n = struct.unpack('>I', h.read(4))[0]
        return frozenset(_unpack_one(h) for _ in range(n))
    if t == _T_SET:
        n = struct.unpack('>I', h.read(4))[0]
        return set(_unpack_one(h) for _ in range(n))
    if t == _T_DICT:
        n = struct.unpack('>I', h.read(4))[0]
        d = {}
        for _ in range(n):
            k = _unpack_one(h)
            v = _unpack_one(h)
            d[k] = v
        return d
    if t == _T_CODE:
        n = struct.unpack('>I', h.read(4))[0]
        return rebuild_co(h.read(n))
    if t == _T_MARSHAL:
        n = struct.unpack('>I', h.read(4))[0]
        return marshal.loads(h.read(n))
    return None


def pack_names(names):
    out = io.BytesIO()
    for n in names:
        b = n.encode('utf-8')
        out.write(struct.pack('>I', len(b)) + b)
    return out.getvalue()


def unpack_names(data):
    stream = io.BytesIO(data)
    out = []
    while stream.tell() < len(data):
        n = struct.unpack('>I', stream.read(4))[0]
        out.append(stream.read(n).decode('utf-8'))
    return out


def pack_revmap(rev):
    out = io.BytesIO()
    for nb, ob in rev.items():
        out.write(struct.pack('>BB', nb, ob))
    return out.getvalue()


def unpack_revmap(data):
    rev = {}
    for i in range(0, len(data), 2):
        nb, ob = struct.unpack('>BB', data[i:i + 2])
        rev[nb] = ob
    return rev


def pack_starts(starts):
    if not starts:
        return b''
    return struct.pack('>' + 'I' * len(starts), *starts)


def unpack_starts(data):
    n = len(data) // 4
    return struct.unpack('>' + 'I' * n, data) if n else ()


def pack_co(co):
    seed = random.getrandbits(64)
    try:
        starts = sorted(_op_starts(co))
        raw_code = bytes(co.co_code) if hasattr(co, 'co_code') else b''
        swapped, rev = _swap_ops(raw_code, set(starts))
    except Exception:
        starts = []
        raw_code = bytes(co.co_code) if hasattr(co, 'co_code') else b''
        swapped = raw_code
        rev = {}
    scrambled = _scramble(swapped, seed)
    blob = io.BytesIO()
    blob.write(struct.pack('>6I',
        co.co_argcount,
        co.co_posonlyargcount,
        co.co_kwonlyargcount,
        co.co_nlocals,
        co.co_stacksize,
        co.co_flags))
    blob.write(struct.pack('>Q', seed))
    sb = pack_starts(starts)
    blob.write(struct.pack('>I', len(sb)) + sb)
    rb = pack_revmap(rev)
    blob.write(struct.pack('>I', len(rb)) + rb)
    cb = pack_consts(list(co.co_consts))
    blob.write(struct.pack('>I', len(cb)) + cb)
    nb = pack_names(list(co.co_names))
    blob.write(struct.pack('>I', len(nb)) + nb)
    vb = pack_names(list(co.co_varnames))
    blob.write(struct.pack('>I', len(vb)) + vb)
    fb = pack_names(list(co.co_freevars))
    blob.write(struct.pack('>I', len(fb)) + fb)
    cb2 = pack_names(list(co.co_cellvars))
    blob.write(struct.pack('>I', len(cb2)) + cb2)
    fn = co.co_filename.encode('utf-8')
    blob.write(struct.pack('>I', len(fn)) + fn)
    cn = co.co_name.encode('utf-8')
    blob.write(struct.pack('>I', len(cn)) + cn)
    qn = getattr(co, 'co_qualname', co.co_name).encode('utf-8')
    blob.write(struct.pack('>I', len(qn)) + qn)
    blob.write(struct.pack('>I', co.co_firstlineno))
    lt = bytes(co.co_linetable) if hasattr(co, 'co_linetable') else b''
    blob.write(struct.pack('>I', len(lt)) + lt)
    et = bytes(co.co_exceptiontable) if hasattr(co, 'co_exceptiontable') else b''
    blob.write(struct.pack('>I', len(et)) + et)
    blob.write(struct.pack('>I', len(scrambled)) + scrambled)
    return blob.getvalue()


def rebuild_co(blob):
    stream = io.BytesIO(blob)
    ac, pc, kc, nl, ss, fl = struct.unpack('>6I', stream.read(24))
    seed = struct.unpack('>Q', stream.read(8))[0]
    sl = struct.unpack('>I', stream.read(4))[0]
    starts = set(unpack_starts(stream.read(sl)))
    rl = struct.unpack('>I', stream.read(4))[0]
    rev = unpack_revmap(stream.read(rl))
    csz = struct.unpack('>I', stream.read(4))[0]
    consts = tuple(unpack_consts(stream.read(csz)))
    nsz = struct.unpack('>I', stream.read(4))[0]
    names = tuple(unpack_names(stream.read(nsz)))
    vsz = struct.unpack('>I', stream.read(4))[0]
    varnames = tuple(unpack_names(stream.read(vsz)))
    fsz = struct.unpack('>I', stream.read(4))[0]
    freevars = tuple(unpack_names(stream.read(fsz)))
    csz2 = struct.unpack('>I', stream.read(4))[0]
    cellvars = tuple(unpack_names(stream.read(csz2)))
    fnl = struct.unpack('>I', stream.read(4))[0]
    filename = stream.read(fnl).decode('utf-8')
    cnl = struct.unpack('>I', stream.read(4))[0]
    co_name = stream.read(cnl).decode('utf-8')
    qnl = struct.unpack('>I', stream.read(4))[0]
    qualname = stream.read(qnl).decode('utf-8')
    firstlineno = struct.unpack('>I', stream.read(4))[0]
    ltl = struct.unpack('>I', stream.read(4))[0]
    linetable = stream.read(ltl)
    etl = struct.unpack('>I', stream.read(4))[0]
    exceptiontable = stream.read(etl)
    bsz = struct.unpack('>I', stream.read(4))[0]
    raw = _unscramble(stream.read(bsz), seed)
    code = bytearray(raw)
    for p in starts:
        if p < len(code) and code[p] in rev:
            code[p] = rev[code[p]]
    try:
        return types.CodeType(
            ac, pc, kc, nl, ss, fl, bytes(code), consts,
            names, varnames, filename, co_name, qualname, firstlineno,
            linetable, exceptiontable, freevars, cellvars
        )
    except TypeError:
        try:
            return types.CodeType(
                ac, pc, kc, nl, ss, fl, bytes(code), consts,
                names, varnames, filename, co_name, firstlineno,
                linetable, exceptiontable, freevars, cellvars
            )
        except TypeError:
            return types.CodeType(
                ac, kc, nl, ss, fl, bytes(code), consts,
                names, varnames, filename, co_name, firstlineno,
                b'', freevars, cellvars
            )


def build_package(source):
    co = compile(source, '<vanish>', 'exec', optimize=2)
    body = pack_co(co)
    out = io.BytesIO()
    out.write(BVM_MAGIC)
    out.write(BVM_VER)
    out.write(struct.pack('>I', len(body)))
    out.write(body)
    return out.getvalue()


RUNTIME = f'''
import io as _io,struct as _st,sys as _sy,builtins as _bi,types as _ty,time as _tm,os as _os,marshal as _ms

_BVM_M={BVM_MAGIC!r}
_BVM_V={BVM_VER!r}
_IX=0x6A4F9E3C1B7D5A82
_SX=0xC3

class _b8:
 def __init__(_s):
  _s._t=_tm.perf_counter()
  _s._guard()
 def _guard(_s):
  if getattr(_sy,'gettrace',None) and _sy.gettrace() is not None:
   _bi.__dict__['print']=lambda *a,**k:None
  try:
   if not isinstance(_bi.__dict__.get('abs'),_ty.BuiltinFunctionType):
    _os._exit(255)
  except Exception:pass
  for _dm in ('pdb','debugpy','pydevd','bdb','pudb','ipdb','winpdb','rpdb','_pydevd_bundle','viztracer','pyinstrument'):
   if _dm in _sy.modules:_os._exit(0)
  for _ev in ('PYTHONDEBUG','PYTHONINSPECT','PYTHONBREAKPOINT','PYCHARM_DEBUG','DEBUGPY_LAUNCHER_PORT','PYDEVD_USE_FRAME_EVAL'):
   if _os.environ.get(_ev):_os._exit(0)
 def _x(_s,d,seed):
  x=(seed&0xFFFFFFFFFFFFFFFF) or 0xDEADBEEFCAFEBABE
  o=bytearray(len(d))
  for i,b in enumerate(d):
   x^=(x<<13)&0xFFFFFFFFFFFFFFFF;x^=x>>7;x^=(x<<17)&0xFFFFFFFFFFFFFFFF
   o[i]=b^(x&0xFF)
  return bytes(o)
 def _u1(_s,h):
  t=h.read(1)
  if not t:return None
  t=t[0]
  if t==0:return None
  if t==15:return ...
  if t==1:return True
  if t==2:return False
  if t==3:return _st.unpack('>q',h.read(8))[0]^_IX
  if t==4:return _st.unpack('>d',h.read(8))[0]
  if t==10:
   r,i=_st.unpack('>dd',h.read(16));return complex(r,i)
  if t==5:
   n=_st.unpack('>I',h.read(4))[0];return bytes(b^_SX for b in h.read(n)).decode('utf-8')
  if t==6:
   n=_st.unpack('>I',h.read(4))[0];return bytes(b^_SX for b in h.read(n))
  if t==17:
   n=_st.unpack('>I',h.read(4))[0];return bytearray(b^_SX for b in h.read(n))
  if t==7:
   n=_st.unpack('>I',h.read(4))[0];return tuple(_s._u1(h) for _ in range(n))
  if t==11:
   n=_st.unpack('>I',h.read(4))[0];return [_s._u1(h) for _ in range(n)]
  if t==13:
   n=_st.unpack('>I',h.read(4))[0];return frozenset(_s._u1(h) for _ in range(n))
  if t==12:
   n=_st.unpack('>I',h.read(4))[0];return set(_s._u1(h) for _ in range(n))
  if t==14:
   n=_st.unpack('>I',h.read(4))[0]
   d={{}}
   for _ in range(n):
    k=_s._u1(h);v=_s._u1(h);d[k]=v
   return d
  if t==16:
   start=_s._u1(h);stop=_s._u1(h);step=_s._u1(h)
   return slice(start,stop,step)
  if t==8:
   n=_st.unpack('>I',h.read(4))[0];return _s._rc(h.read(n))
  if t==9:
   n=_st.unpack('>I',h.read(4))[0];return _ms.loads(h.read(n))
  return None
 def _uc(_s,data):
  h=_io.BytesIO(data);e=len(data);o=[]
  while h.tell()<e:o.append(_s._u1(h))
  return o
 def _un(_s,d):
  h=_io.BytesIO(d);o=[]
  while h.tell()<len(d):
   n=_st.unpack('>I',h.read(4))[0];o.append(h.read(n).decode('utf-8'))
  return o
 def _rc(_s,b):
  h=_io.BytesIO(b)
  ac,pc,kc,nl,ss,fl=_st.unpack('>6I',h.read(24))
  sd=_st.unpack('>Q',h.read(8))[0]
  sl=_st.unpack('>I',h.read(4))[0]
  st=set(_st.unpack('>'+'I'*(sl//4),h.read(sl))) if sl else set()
  rl=_st.unpack('>I',h.read(4))[0]
  rv={{}};rd=h.read(rl)
  for i in range(0,rl,2):
   a,bb=_st.unpack('>BB',rd[i:i+2]);rv[a]=bb
  csz=_st.unpack('>I',h.read(4))[0]
  cn=tuple(_s._uc(h.read(csz)))
  nsz=_st.unpack('>I',h.read(4))[0];nm=tuple(_s._un(h.read(nsz)))
  vsz=_st.unpack('>I',h.read(4))[0];vn=tuple(_s._un(h.read(vsz)))
  fsz=_st.unpack('>I',h.read(4))[0];fv=tuple(_s._un(h.read(fsz)))
  csz2=_st.unpack('>I',h.read(4))[0];cv=tuple(_s._un(h.read(csz2)))
  fnl=_st.unpack('>I',h.read(4))[0];fn=h.read(fnl).decode('utf-8')
  cnl=_st.unpack('>I',h.read(4))[0];cnm=h.read(cnl).decode('utf-8')
  qnl=_st.unpack('>I',h.read(4))[0];qn=h.read(qnl).decode('utf-8')
  fln=_st.unpack('>I',h.read(4))[0]
  ltl=_st.unpack('>I',h.read(4))[0];lt=h.read(ltl)
  etl=_st.unpack('>I',h.read(4))[0];et=h.read(etl)
  bsz=_st.unpack('>I',h.read(4))[0]
  raw=_s._x(h.read(bsz),sd)
  code=bytearray(raw)
  for p in st:
   if p<len(code) and code[p] in rv:code[p]=rv[code[p]]
  if _tm.perf_counter()-_s._t>60.0:
   _os._exit(0)
  try:
   return _ty.CodeType(ac,pc,kc,nl,ss,fl,bytes(code),cn,nm,vn,fn,cnm,qn,fln,lt,et,fv,cv)
  except TypeError:
   try:
    return _ty.CodeType(ac,pc,kc,nl,ss,fl,bytes(code),cn,nm,vn,fn,cnm,fln,lt,et,fv,cv)
   except TypeError:
    return _ty.CodeType(ac,kc,nl,ss,fl,bytes(code),cn,nm,vn,fn,cnm,fln,b'',fv,cv)
 def run(_s,pkg):
  h=_io.BytesIO(pkg)
  if h.read(17)!=_BVM_M or h.read(4)!=_BVM_V:_os._exit(0)
  bl=_st.unpack('>I',h.read(4))[0]
  co=_s._rc(h.read(bl))
  g={{'__builtins__':_bi,'__name__':'__main__','__file__':'<vanish>','__spec__':None}}
  exec(co,g)

_b8().run({{payload}})
'''

RUNTIME_CORE = RUNTIME.split('_b8().run(')[0]


def make_runtime(payload_bytes):
    return RUNTIME.replace('{{payload}}', repr(payload_bytes)).replace('{payload}', repr(payload_bytes))
