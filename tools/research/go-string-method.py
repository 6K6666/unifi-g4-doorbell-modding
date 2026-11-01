#!/usr/bin/env python3
"""Print what a small Go enum String() method returns for each value, by reading its disassembly.

Usage: tools/research/go-string-method.py BINARY START END MAX
  BINARY  an aarch64 Go ELF program, for example a copy of the doorbell's ubnt_mcu
  START END  the method's address range from go-funcs.go (hex)
  MAX     the highest value to try

Handles only the switch-statement form (compare, branch, load a string address and length, return).
Needs llvm-objdump (macOS: `xcrun --find llvm-objdump`; Linux: llvm-objdump or objdump with aarch64 support).
"""
import re
import shutil
import struct
import subprocess
import sys


def find_objdump():
    for cmd in (["xcrun", "--find", "llvm-objdump"], ["which", "llvm-objdump"], ["which", "aarch64-linux-gnu-objdump"]):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
        except FileNotFoundError:
            continue
        if out:
            return out
    sys.exit("no aarch64-capable objdump found")


def segments(data):
    phoff = struct.unpack_from("<Q", data, 0x20)[0]
    phent, phnum = struct.unpack_from("<HH", data, 0x36)
    segs = []
    for i in range(phnum):
        t, _, off, va, _, fs, _, _ = struct.unpack_from("<IIQQQQQQ", data, phoff + i * phent)
        if t == 1:
            segs.append((va, off, fs))
    return segs


def read_string(data, segs, addr, n):
    for va, off, fs in segs:
        if va <= addr < va + fs:
            return data[off + addr - va: off + addr - va + n].decode("latin1")


def disassemble(objdump, binary, start, end):
    out = subprocess.run([objdump, "-d", f"--start-address={start:#x}", f"--stop-address={end:#x}", binary],
                         capture_output=True, text=True).stdout
    ins = {}
    for line in out.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+(\S+)\s*(.*)", line)
        if m:
            ins[int(m.group(1), 16)] = (m.group(2), m.group(3).split("//")[0].strip())
    return ins


def imm(text):
    return int(re.search(r"#(0x[0-9a-f]+|\d+)", text).group(1), 0)


def target(text):
    return int(re.search(r"0x[0-9a-f]+", text.split(",")[-1]).group(0), 16)


def run(ins, start, value):
    pc, x0, flags, ptr, length = start, value, None, None, None
    for _ in range(300):
        op, args = ins[pc]
        nxt = pc + 4
        if op == "ldrb":
            x0 = value
        elif op == "cmp":
            flags = (x0, imm(args))
        elif op in ("cbz", "cbnz"):
            if (x0 == 0) == (op == "cbz"):
                nxt = target(args)
        elif op.startswith("b."):
            a, b = flags
            taken = {"eq": a == b, "ne": a != b, "hi": a > b, "ls": a <= b, "hs": a >= b, "lo": a < b}[op[2:]]
            if taken:
                nxt = target(args)
        elif op == "adrp":
            x0 = int(args.split(",")[1].strip(), 16)
        elif op == "add":
            x0 += imm(args)
        elif op in ("orr", "mov"):
            x0 = imm(args)
        elif op == "str":
            if "#0x10" in args:
                ptr = x0
            elif "#0x18" in args:
                length = x0
        elif op == "ret":
            return ptr, length
        else:
            sys.exit(f"unhandled instruction {op} {args}: this method is not a plain switch")
        pc = nxt
    sys.exit("did not return")


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    binary, start, end, top = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16), int(sys.argv[4])
    data = open(binary, "rb").read()
    segs = segments(data)
    ins = disassemble(find_objdump(), binary, start, end)
    for v in range(top + 1):
        ptr, length = run(ins, start, v)
        print(f"{v} = {read_string(data, segs, ptr, length)}")


if __name__ == "__main__":
    main()
