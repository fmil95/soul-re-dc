"""SH-4 instruction decoder producing GNU as (binutils 2.9-sh4) syntax.

decode(op, pc) -> Insn or None (None = not a valid SH-4 instruction; emit it as .word).

Insn fields:
  mnem      mnemonic as accepted by the SDK assembler
  ops       operand string; PC-relative operands are left as a placeholder "{}" and the target is in `target`
  kind      None, or one of: "branch" (bt/bf/bra, target), "branch_delay" (bt/s, bf/s), "call" (bsr),
            "pcrel_l" / "pcrel_w" (mov.l/mov.w @(disp,PC)), "mova", "jump" (jmp/braf/rts/rte: end of flow)
  target    absolute target address for PC-relative kinds
  delay     True if the instruction has a delay slot
  ends      True if control does not fall through (bra, jmp, braf, rts, rte)

Floating-point moves are always printed in their single-precision form (frN); the encoding does not depend on
FPSCR.SZ, so this round-trips through the assembler even where the program had SZ=1.
"""


class Insn:
    __slots__ = ("mnem", "ops", "kind", "target", "delay", "ends", "op")

    def __init__(self, mnem, ops="", kind=None, target=None, delay=False, ends=False):
        self.mnem, self.ops, self.kind, self.target, self.delay, self.ends = mnem, ops, kind, target, delay, ends

    def text(self, label=None):
        ops = self.ops.replace("{}", label) if label is not None else self.ops
        return f"{self.mnem}\t{ops}" if ops else self.mnem


def _s8(x):
    return x - 0x100 if x & 0x80 else x


def _s12(x):
    return x - 0x1000 if x & 0x800 else x


R = [f"r{i}" for i in range(16)]
FR = [f"fr{i}" for i in range(16)]

# 0nm? and 4n?? style tables: low nibble/byte -> (mnemonic, operand template)
_ZERO_NM = {
    0x4: ("mov.b", "{m},@(r0,{n})"), 0x5: ("mov.w", "{m},@(r0,{n})"), 0x6: ("mov.l", "{m},@(r0,{n})"),
    0x7: ("mul.l", "{m},{n}"),
    0xC: ("mov.b", "@(r0,{m}),{n}"), 0xD: ("mov.w", "@(r0,{m}),{n}"), 0xE: ("mov.l", "@(r0,{m}),{n}"),
    0xF: ("mac.l", "@{m}+,@{n}+"),
}
_ZERO_FIXED = {
    0x0008: ("clrt", ""), 0x0018: ("sett", ""), 0x0028: ("clrmac", ""), 0x0048: ("clrs", ""),
    0x0058: ("sets", ""), 0x0009: ("nop", ""), 0x0019: ("div0u", ""), 0x000B: ("rts", ""),
    0x001B: ("sleep", ""), 0x002B: ("rte", ""),
}
_ZERO_N = {  # low byte -> (mnem, ops) with n operand
    0x02: ("stc", "sr,{n}"), 0x12: ("stc", "gbr,{n}"), 0x22: ("stc", "vbr,{n}"), 0x32: ("stc", "ssr,{n}"),
    0x42: ("stc", "spc,{n}"), 0x3A: ("stc", "sgr,{n}"), 0xFA: ("stc", "dbr,{n}"),
    0x03: ("bsrf", "{n}"), 0x23: ("braf", "{n}"),
    0x83: ("pref", "@{n}"), 0x93: ("ocbi", "@{n}"), 0xA3: ("ocbp", "@{n}"), 0xB3: ("ocbwb", "@{n}"),
    0xC3: ("movca.l", "r0,@{n}"),
    0x29: ("movt", "{n}"),
    0x0A: ("sts", "mach,{n}"), 0x1A: ("sts", "macl,{n}"), 0x2A: ("sts", "pr,{n}"),
    0x5A: ("sts", "fpul,{n}"), 0x6A: ("sts", "fpscr,{n}"),
}
_FOUR_N = {
    0x00: ("shll", "{n}"), 0x01: ("shlr", "{n}"), 0x02: ("sts.l", "mach,@-{n}"), 0x03: ("stc.l", "sr,@-{n}"),
    0x04: ("rotl", "{n}"), 0x05: ("rotr", "{n}"), 0x06: ("lds.l", "@{n}+,mach"), 0x07: ("ldc.l", "@{n}+,sr"),
    0x08: ("shll2", "{n}"), 0x09: ("shlr2", "{n}"), 0x0A: ("lds", "{n},mach"), 0x0B: ("jsr", "@{n}"),
    0x0E: ("ldc", "{n},sr"),
    0x10: ("dt", "{n}"), 0x11: ("cmp/pz", "{n}"), 0x12: ("sts.l", "macl,@-{n}"), 0x13: ("stc.l", "gbr,@-{n}"),
    0x15: ("cmp/pl", "{n}"), 0x16: ("lds.l", "@{n}+,macl"), 0x17: ("ldc.l", "@{n}+,gbr"),
    0x18: ("shll8", "{n}"), 0x19: ("shlr8", "{n}"), 0x1A: ("lds", "{n},macl"), 0x1B: ("tas.b", "@{n}"),
    0x1E: ("ldc", "{n},gbr"),
    0x20: ("shal", "{n}"), 0x21: ("shar", "{n}"), 0x22: ("sts.l", "pr,@-{n}"), 0x23: ("stc.l", "vbr,@-{n}"),
    0x24: ("rotcl", "{n}"), 0x25: ("rotcr", "{n}"), 0x26: ("lds.l", "@{n}+,pr"), 0x27: ("ldc.l", "@{n}+,vbr"),
    0x28: ("shll16", "{n}"), 0x29: ("shlr16", "{n}"), 0x2A: ("lds", "{n},pr"), 0x2B: ("jmp", "@{n}"),
    0x2E: ("ldc", "{n},vbr"),
    0x32: ("stc.l", "sgr,@-{n}"), 0x33: ("stc.l", "ssr,@-{n}"), 0x37: ("ldc.l", "@{n}+,ssr"), 0x3E: ("ldc", "{n},ssr"),
    0x43: ("stc.l", "spc,@-{n}"), 0x47: ("ldc.l", "@{n}+,spc"), 0x4E: ("ldc", "{n},spc"),
    0x52: ("sts.l", "fpul,@-{n}"), 0x56: ("lds.l", "@{n}+,fpul"), 0x5A: ("lds", "{n},fpul"),
    0x62: ("sts.l", "fpscr,@-{n}"), 0x66: ("lds.l", "@{n}+,fpscr"), 0x6A: ("lds", "{n},fpscr"),
    0xF2: ("stc.l", "dbr,@-{n}"), 0xF6: ("ldc.l", "@{n}+,dbr"), 0xFA: ("ldc", "{n},dbr"),
}
_TWO = {
    0x0: ("mov.b", "{m},@{n}"), 0x1: ("mov.w", "{m},@{n}"), 0x2: ("mov.l", "{m},@{n}"),
    0x4: ("mov.b", "{m},@-{n}"), 0x5: ("mov.w", "{m},@-{n}"), 0x6: ("mov.l", "{m},@-{n}"),
    0x7: ("div0s", "{m},{n}"), 0x8: ("tst", "{m},{n}"), 0x9: ("and", "{m},{n}"), 0xA: ("xor", "{m},{n}"),
    0xB: ("or", "{m},{n}"), 0xC: ("cmp/str", "{m},{n}"), 0xD: ("xtrct", "{m},{n}"), 0xE: ("mulu.w", "{m},{n}"),
    0xF: ("muls.w", "{m},{n}"),
}
_THREE = {
    0x0: "cmp/eq", 0x2: "cmp/hs", 0x3: "cmp/ge", 0x4: "div1", 0x5: "dmulu.l", 0x6: "cmp/hi", 0x7: "cmp/gt",
    0x8: "sub", 0xA: "subc", 0xB: "subv", 0xC: "add", 0xD: "dmuls.l", 0xE: "addc", 0xF: "addv",
}
_SIX = {
    0x0: ("mov.b", "@{m},{n}"), 0x1: ("mov.w", "@{m},{n}"), 0x2: ("mov.l", "@{m},{n}"), 0x3: ("mov", "{m},{n}"),
    0x4: ("mov.b", "@{m}+,{n}"), 0x5: ("mov.w", "@{m}+,{n}"), 0x6: ("mov.l", "@{m}+,{n}"), 0x7: ("not", "{m},{n}"),
    0x8: ("swap.b", "{m},{n}"), 0x9: ("swap.w", "{m},{n}"), 0xA: ("negc", "{m},{n}"), 0xB: ("neg", "{m},{n}"),
    0xC: ("extu.b", "{m},{n}"), 0xD: ("extu.w", "{m},{n}"), 0xE: ("exts.b", "{m},{n}"), 0xF: ("exts.w", "{m},{n}"),
}
_F_NM = {
    0x0: ("fadd", "{fm},{fn}"), 0x1: ("fsub", "{fm},{fn}"), 0x2: ("fmul", "{fm},{fn}"), 0x3: ("fdiv", "{fm},{fn}"),
    0x4: ("fcmp/eq", "{fm},{fn}"), 0x5: ("fcmp/gt", "{fm},{fn}"),
    0x6: ("fmov.s", "@(r0,{m}),{fn}"), 0x7: ("fmov.s", "{fm},@(r0,{n})"),
    0x8: ("fmov.s", "@{m},{fn}"), 0x9: ("fmov.s", "@{m}+,{fn}"), 0xA: ("fmov.s", "{fm},@{n}"),
    0xB: ("fmov.s", "{fm},@-{n}"), 0xC: ("fmov", "{fm},{fn}"), 0xE: ("fmac", "fr0,{fm},{fn}"),
}
_F_D = {  # 1111nnnn xxxx1101
    0x0: ("fsts", "fpul,{fn}"), 0x1: ("flds", "{fn},fpul"), 0x2: ("float", "fpul,{fn}"), 0x3: ("ftrc", "{fn},fpul"),
    0x4: ("fneg", "{fn}"), 0x5: ("fabs", "{fn}"), 0x6: ("fsqrt", "{fn}"),
    0x8: ("fldi0", "{fn}"), 0x9: ("fldi1", "{fn}"),
}


def decode(op, pc):
    hi, n, m, lo = op >> 12, (op >> 8) & 15, (op >> 4) & 15, op & 15
    rn, rm = R[n], R[m]

    def f(tmpl, **kw):
        return tmpl.format(n=rn, m=rm, fn=FR[n], fm=FR[m], **kw)

    if hi == 0x0:
        if op in _ZERO_FIXED:
            mn, o = _ZERO_FIXED[op]
            i = Insn(mn, o)
            if mn in ("rts", "rte"):
                i.delay = i.ends = True
                i.kind = "jump"
            return i
        if lo in _ZERO_NM:
            mn, o = _ZERO_NM[lo]
            return Insn(mn, f(o))
        low = op & 0xFF
        if lo == 2 and m & 8:
            return Insn("stc", f(f"r{m & 7}_bank,{{n}}"))
        if low in _ZERO_N:
            mn, o = _ZERO_N[low]
            i = Insn(mn, f(o))
            if mn == "braf":
                i.delay = i.ends = True
                i.kind = "jump"
            elif mn == "bsrf":
                i.delay = True
            return i
        return None
    if hi == 0x1:
        return Insn("mov.l", f(f"{{m}},@({lo * 4},{{n}})"))
    if hi == 0x2:
        if lo in _TWO:
            mn, o = _TWO[lo]
            return Insn(mn, f(o))
        return None
    if hi == 0x3:
        if lo in _THREE:
            return Insn(_THREE[lo], f("{m},{n}"))
        return None
    if hi == 0x4:
        low = op & 0xFF
        if lo == 0xC:
            return Insn("shad", f("{m},{n}"))
        if lo == 0xD:
            return Insn("shld", f("{m},{n}"))
        if lo == 0xF:
            return Insn("mac.w", f("@{m}+,@{n}+"))
        if m & 8 and lo in (3, 7, 0xE):
            b = f"r{m & 7}_bank"
            return Insn(*{3: ("stc.l", f"{b},@-{rn}"), 7: ("ldc.l", f"@{rn}+,{b}"), 0xE: ("ldc", f"{rn},{b}")}[lo])
        if low in _FOUR_N:
            mn, o = _FOUR_N[low]
            i = Insn(mn, f(o))
            if mn == "jmp":
                i.delay = i.ends = True
                i.kind = "jump"
            elif mn == "jsr":
                i.delay = True
            return i
        return None
    if hi == 0x5:
        return Insn("mov.l", f(f"@({lo * 4},{{m}}),{{n}}"))
    if hi == 0x6:
        mn, o = _SIX[lo]
        return Insn(mn, f(o))
    if hi == 0x7:
        return Insn("add", f"#{_s8(op & 0xFF)},{rn}")
    if hi == 0x8:
        d = op & 0xFF
        sub = n
        if sub == 0x0:
            return Insn("mov.b", f"r0,@({lo},{rm})")
        if sub == 0x1:
            return Insn("mov.w", f"r0,@({lo * 2},{rm})")
        if sub == 0x4:
            return Insn("mov.b", f"@({lo},{rm}),r0")
        if sub == 0x5:
            return Insn("mov.w", f"@({lo * 2},{rm}),r0")
        if sub == 0x8:
            return Insn("cmp/eq", f"#{_s8(d)},r0")
        if sub in (0x9, 0xB, 0xD, 0xF):
            mn = {0x9: "bt", 0xB: "bf", 0xD: "bt/s", 0xF: "bf/s"}[sub]
            t = pc + 4 + _s8(d) * 2
            return Insn(mn, "{}", "branch", t, delay=sub in (0xD, 0xF))
        return None
    if hi == 0x9:
        t = pc + 4 + (op & 0xFF) * 2
        return Insn("mov.w", f"{{}},{rn}", "pcrel_w", t)
    if hi in (0xA, 0xB):
        t = pc + 4 + _s12(op & 0xFFF) * 2
        if hi == 0xA:
            return Insn("bra", "{}", "branch", t, delay=True, ends=True)
        return Insn("bsr", "{}", "call", t, delay=True)
    if hi == 0xC:
        d = op & 0xFF
        sub = n
        tbl = {
            0x0: ("mov.b", f"r0,@({d},gbr)"), 0x1: ("mov.w", f"r0,@({d * 2},gbr)"),
            0x2: ("mov.l", f"r0,@({d * 4},gbr)"), 0x3: ("trapa", f"#{d}"),
            0x4: ("mov.b", f"@({d},gbr),r0"), 0x5: ("mov.w", f"@({d * 2},gbr),r0"),
            0x6: ("mov.l", f"@({d * 4},gbr),r0"),
            0x8: ("tst", f"#{d},r0"), 0x9: ("and", f"#{d},r0"), 0xA: ("xor", f"#{d},r0"), 0xB: ("or", f"#{d},r0"),
            0xC: ("tst.b", f"#{d},@(r0,gbr)"), 0xD: ("and.b", f"#{d},@(r0,gbr)"),
            0xE: ("xor.b", f"#{d},@(r0,gbr)"), 0xF: ("or.b", f"#{d},@(r0,gbr)"),
        }
        if sub == 0x7:
            t = (pc & ~3) + 4 + d * 4
            return Insn("mova", "{},r0", "mova", t)
        return Insn(*tbl[sub])
    if hi == 0xD:
        t = (pc & ~3) + 4 + (op & 0xFF) * 4
        return Insn("mov.l", f"{{}},{rn}", "pcrel_l", t)
    if hi == 0xE:
        return Insn("mov", f"#{_s8(op & 0xFF)},{rn}")
    # 0xF: FPU
    if lo in _F_NM:
        mn, o = _F_NM[lo]
        return Insn(mn, f(o))
    if lo == 0xD:
        if m in _F_D:
            mn, o = _F_D[m]
            return Insn(mn, f(o))
        if m == 0xA:
            return Insn("fcnvsd", f"fpul,dr{n & 14}") if not n & 1 else None
        if m == 0xB:
            return Insn("fcnvds", f"dr{n & 14},fpul") if not n & 1 else None
        if m == 0xE:
            return Insn("fipr", f"fv{m_fv(op, 8)},fv{m_fv(op, 10)}")
        if m == 0xF:
            if n & 3 == 1:
                return Insn("ftrv", f"xmtrx,fv{(n >> 2) * 4}")
            if op == 0xFBFD:
                return Insn("frchg")
            if op == 0xF3FD:
                return Insn("fschg")
            if n & 1 == 0:
                return Insn("fsca", f"fpul,dr{n & 14}")
            return None
        if m == 0x7:
            return Insn("fsrra", f"{FR[n]}")
        return None
    return None


def m_fv(op, shift):
    return ((op >> shift) & 3) * 4
