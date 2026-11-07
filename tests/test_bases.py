"""Abstract bases: C++ inheritance mirrored on top of the pystreampu classes (Plan.md, rules R1/R2)."""

import json
import re
from pathlib import Path

import pytest
import streampu as spu

import aff3ct as af

# Stateful is not exported at the top level of streampu (only Stateful_core is)
Stateful = spu.Stateful

API = json.loads((Path(__file__).parent.parent / "docs" / "design" / "aff3ct_api.json").read_text())["classes"]


@pytest.mark.parametrize(
    "tpl",
    [af.crc.CRC, af.chn.Channel, af.cst.Coset, af.enc.Encoder, af.ext.Extractor, af.mdm.Modem, af.pct.Puncturer,
     af.qnt.Quantizer, af.dec.Decoder_HIHO, af.dec.Decoder_SIHO, af.dec.Decoder_SISO],
)
def test_every_instance_is_a_streampu_stateful(tpl):
    assert tpl.instances
    for cls in tpl.instances.values():
        assert issubclass(cls, Stateful), cls
        assert issubclass(cls, spu.Module), cls


def test_streampu_interfaces():
    assert issubclass(af.enc.Encoder[spu.int32], spu.Interface_set_seed)
    assert issubclass(af.chn.Channel[spu.float32], spu.Interface_set_seed)
    assert issubclass(af.dec.Decoder, spu.Interface_set_seed)
    assert issubclass(af.dec.Decoder, spu.Interface_reset)
    assert issubclass(af.mnt.Monitor, spu.Interface_is_done)
    assert issubclass(af.mnt.Monitor, spu.Interface_reset)


def test_decoder_hierarchy():
    siso = af.dec.Decoder_SISO[spu.int16, spu.int16]
    assert issubclass(siso, af.dec.Decoder_SIHO[spu.int16, spu.int16])
    assert issubclass(siso, af.dec.Decoder_HIHO[spu.int16])
    assert issubclass(siso, af.dec.Decoder)


def test_accessor_convention():
    # quantities are read-only properties, predicates and setters are methods (as in pystreampu)
    enc = af.enc.Encoder[spu.int32]
    assert isinstance(enc.K, property) and enc.K.fset is None
    assert callable(enc.is_sys) and callable(enc.set_memorizing)
    assert callable(af.dec.Decoder.set_auto_reset)
    mdm = af.mdm.Modem[spu.int32, spu.float32, spu.float32]
    assert callable(mdm.is_filter) and callable(mdm.is_demodulator)


def _tasks(key, seen=None):
    """Task names of an AFF3CT module class, inherited ones included (from the API fingerprint)."""
    seen = seen or set()
    entry = API.get(key, {})
    names = set(entry.get("tasks") or {})
    for b in entry.get("bases", []):
        bkey = "Module::" + re.sub(r"<.*", "", b).split("::")[-1]
        if bkey in API and bkey not in seen:
            seen.add(bkey)
            names |= _tasks(bkey, seen)
    return names


def _wrapped_module_classes():
    for name in dir(af._ext):
        sub = getattr(af._ext, name)
        if not hasattr(sub, "__name__") or name.startswith("_") or name in ("factory", "tools", "interfaces"):
            continue
        for cname in dir(sub):
            cls = getattr(sub, cname)
            if isinstance(cls, type) and issubclass(cls, spu.Module):
                base = re.sub(r"_(u?int(8|16|32|64)|float(32|64))(_.*)?$", "", cname)
                yield f"Module::{base}", cls


def test_no_attribute_hides_a_task():
    # pystreampu reaches the tasks through Module.__getattr__ (fallback): an attribute with the name of a task would
    # hide it (e.g. a `Modem.filter` property would hide the task `filter`)
    checked = 0
    for key, cls in _wrapped_module_classes():
        tasks = _tasks(key)
        own = {a for k in cls.__mro__ if k.__module__.startswith("aff3ct") for a in vars(k)}
        assert not (tasks & own), f"{cls.__name__}: attribute(s) {tasks & own} hide task(s)"
        checked += bool(tasks)
    assert checked > 10
