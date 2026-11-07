#!/usr/bin/env python3
"""Measure how each AFF3CT encoder / decoder represents a 1 (needs the built aff3ct package).

Usage:
    python scripts/probe_bit_convention.py [-o docs/design/bit_convention.md]

In AFF3CT a bit is 0 or non-zero (the monitors compare booleans); some modules return another value than 1 for a 1.
Each (function, type, implem, dtypes) that can be built with the wrapped classes is run on a noiseless input: the
values of the outputs (``encode::X_N``, ``decode_siho::V_K``, ``decode_siho_cw::V_N``) are recorded, and the
decoded bits are checked (as booleans). The types and implementations come from the factory sources
(``cli::add_options`` / ``Example_set``), the dtype combinations from the compiled instantiations.
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import re
import traceback
from pathlib import Path

import numpy as np
import streampu as spu

import aff3ct as af
from aff3ct._generated.instantiations import INSTANTIATIONS

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "lib" / "aff3ct" / "src" / "Factory" / "Module"
DT = {d.name: d for d in (spu.int8, spu.int16, spu.int32, spu.int64, spu.float32, spu.float64)}


def options(path: Path, what: str) -> list[str]:
    """Values declared for `--<p>-<what>` in a factory source (add_options or Example_set)."""
    txt = path.read_text()
    vals = []
    for m in re.finditer(r'add_options\(args\.at\(\{\s*p \+ "-' + what + r'"[^)]*\),\s*0,(.*?)\);', txt, re.S):
        vals += re.findall(r'"([^"]+)"', m.group(1))
    for m in re.finditer(r'p \+ "-' + what + r'"[^;]*?Example_set\(([^;]*?)\)', txt, re.S):
        vals += re.findall(r'"([^"]+)"', m.group(1))
    return list(dict.fromkeys(vals))


def frozen(K: int, N: int) -> np.ndarray:
    fb = np.zeros(N, dtype=bool)
    fb[: N - K] = True
    return fb


def values(sock) -> str:
    v = np.unique(np.asarray(sock.numpy))
    return ", ".join(str(int(x)) for x in v[:6]) + (" …" if v.size > 6 else "")


def is01(sock) -> bool:
    return set(np.unique(np.asarray(sock.numpy)).tolist()) <= {0, 1}


def llr_of(x: np.ndarray, Q) -> object:
    scale = 2.0 if Q.name.startswith("float") else 8
    y = (1 - 2 * (x != 0).astype(np.int64)) * scale
    return spu.array(y.astype(np.float64 if Q.name.startswith("float") else np.int64).tolist(), dtype=Q)


FAMILIES = [
    # (function name, factory source, K, N, builder args (K, N) -> dict, encoder (K, N, B) -> module)
    ("polar", "Decoder/Polar/Decoder_polar.cpp", 32, 64, lambda K, N: {"frozen_bits": frozen(K, N)},
     lambda K, N, B: af.enc.polar(K, N, frozen(K, N), B=B)),
    ("repetition", "Decoder/Repetition/Decoder_repetition.cpp", 16, 48, lambda K, N: {},
     lambda K, N, B: af.enc.repetition(K, N, B=B)),
    ("no", "Decoder/NO/Decoder_NO.cpp", 32, 32, lambda K, N: {}, lambda K, N, B: af.enc.no(K, N, B=B)),
]
GENERIC_TYPES = ["ML", "CHASE"]  # factory::Decoder, built by every family with an encoder
GENERIC_SIZES = {"polar": (8, 16), "repetition": (8, 24), "no": (8, 8)}  # ML enumerates the 2^K codewords
NEEDS_CRC = {"ASCL", "ASCL_MEM", "SCF"}  # adaptive SCL and SC-Flip: CRC-aided


TIMEOUT = 20  # seconds per combination (a blocked decoder is reported, not waited for)


def run(rows: list, family, fname, typ, implem, combo, K, N, bargs, make_enc, with_encoder=False):
    """Run one combination in a child process (fork) with a timeout."""
    label = (fname, typ, implem, "(" + ", ".join(combo) + ")")
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    proc = ctx.Process(target=_run_child, args=(q, label, fname, typ, implem, combo, K, N, bargs, make_enc,
                                               with_encoder))
    proc.start()
    proc.join(TIMEOUT)
    if proc.is_alive():
        proc.kill()
        proc.join()
        rows.append(label + ("", "", "", f"délai dépassé (> {TIMEOUT} s, bloqué)"))
    elif not q.empty():
        rows.append(q.get())
    else:
        rows.append(label + ("", "", "", f"arrêt du processus (code {proc.exitcode})"))
    print(" ".join(map(str, rows[-1][:4])), "->", rows[-1][-1][:60], flush=True)


def _run_child(q, label, fname, typ, implem, combo, K, N, bargs, make_enc, with_encoder):
    rows: list = []
    _run(rows, label, fname, typ, implem, combo, K, N, bargs, make_enc, with_encoder)
    q.put(rows[0])


def _run(rows: list, label, fname, typ, implem, combo, K, N, bargs, make_enc, with_encoder=False):
    B, Q = DT[combo[0]], DT[combo[-1]]
    try:
        enc = make_enc(K, N, B)
        kw = dict(bargs)
        info = np.random.default_rng(1).integers(0, 2, K).tolist()
        if typ in NEEDS_CRC:
            crc = af.crc.crc(K - 8, type="8-DVB-S2", B=B)
            kw["crc"] = crc
            u = crc.build(spu.array(info[: K - 8], dtype=B))
            u = spu.array(np.asarray(u.numpy[0]).tolist(), dtype=B)
        else:
            u = spu.array(info, dtype=B)
        x = enc.encode(u)
        xv = np.asarray(x.numpy[0]).copy()
        if with_encoder:
            kw["encoder"] = enc
        dec = getattr(af.dec, fname)(K, N, **kw, type=typ, implem=implem, B=B, Q=Q)
        dec.decode_siho(llr_of(xv, Q))
        vk = dec["decode_siho::V_K"]
        ok = np.array_equal(np.asarray(vk.numpy) != 0, np.asarray(u.numpy) != 0)
        cw = ""
        try:
            dec.decode_siho_cw(llr_of(xv, Q))
            vn = dec["decode_siho_cw::V_N"]
            cw = values(vn) + ("" if is01(vn) else " ⚠")
        except Exception:
            cw = "—"
        rows.append(label + (values(x) + ("" if is01(x) else " ⚠"), values(vk) + ("" if is01(vk) else " ⚠"),
                             cw, "✓" if ok else "✗"))
    except Exception as e:
        msg = str(e).splitlines()[0]
        msg = re.sub(r"^In the '.*?' file at line \d+ \('(\w+)' function\): ", r"\1: ", msg)
        rows.append(label + ("", "", "", f"non construit ({type(e).__name__}: {msg[:90]})"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", type=Path, default=ROOT / "docs" / "design" / "bit_convention.md")
    a = ap.parse_args()
    rows: list = []
    for fname, src, K, N, bargs, make_enc in FAMILIES:
        fac = "Decoder_" + Path(src).stem.split("Decoder_")[1]
        combos = INSTANTIATIONS[f"Factory::{fac}"]["builders"]["build"]["combos"]
        types = options(SRC / src, "type")
        implems = options(SRC / src, "implem") or [None]
        for typ in types:
            for implem in implems:
                for combo in combos:
                    run(rows, fname, fname, typ, implem, combo, K, N, bargs(K, N), make_enc)
        Kg, Ng = GENERIC_SIZES[fname]
        for typ in GENERIC_TYPES:
            for combo in combos:
                run(rows, fname, fname, typ, "STD", combo, Kg, Ng, bargs(Kg, Ng), make_enc, with_encoder=True)

    bad = [r for r in rows if "⚠" in "".join(r[4:7])]
    lines = [
        "# Représentation des bits dans AFF3CT",
        "",
        "> Généré par `scripts/probe_bit_convention.py` (AFF3CT " + af.AFF3CT_VERSION + ") — ne pas éditer à la main.",
        "",
        "Dans AFF3CT, un bit vaut 0 ou **non nul** : les moniteurs comparent des booléens (`Boolean_diff`). Certains "
        "modules rendent donc autre chose que 1 pour un 1 ; `aff3ct.tools.hard(x)` donne la vue 0 / 1. Chaque ligne "
        "est mesurée sur une trame sans bruit : valeurs distinctes des sorties, ⚠ quand elles ne sont pas 0 / 1, et "
        "décodage correct (en booléens).",
        "",
        f"**{len(bad)} combinaison(s) sur {len(rows)} rendent autre chose que 0 / 1 :**",
        "",
    ]
    lines += [f"- `af.dec.{r[0]}` type `{r[1]}`, implem `{r[2]}`, {r[3]}" for r in bad] or ["- aucune"]
    lines += [
        "",
        "Non couverts pour l'instant (outils ou classes concrètes pas encore wrappés) : LDPC (`Sparse_matrix`), "
        "BCH / RS (générateur `GF`), RSC / conv. (`trellis` de l'encodeur concret), RA / turbo / turbo produit "
        "(`Interleaver_core`), polaire MK / PAC / PT (`Polar_code`, pré-transformation).",
        "",
        "| Fonction | Type | Implem | (B, Q) | `encode::X_N` | `decode_siho::V_K` | `decode_siho_cw::V_N` | Décodage |",
        "|---|---|---|---|---|---|---|---|",
    ]
    lines += ["| `" + "` | `".join(r[:3]) + "` | " + " | ".join(r[3:]) + " |" for r in rows]
    a.output.write_text("\n".join(lines) + "\n")
    print(f"{len(rows)} combinations, {len(bad)} not 0/1 -> {a.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
