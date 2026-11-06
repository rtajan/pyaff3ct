"""The package imports on top of streampu and exposes the AFF3CT sub-modules."""

import streampu as spu

import aff3ct as af
from aff3ct._generated import instantiations


def test_submodules():
    for name in ("crc", "chn", "cst", "dec", "enc", "ext", "mdm", "mnt", "pct", "qnt", "interfaces", "tools", "factory"):
        assert hasattr(af, name), name


def test_wrapped_aff3ct_is_the_fingerprinted_one():
    # the dtype combinations are generated from the API of this exact AFF3CT revision
    assert af.AFF3CT_VERSION == instantiations.AFF3CT_VERSION
    assert instantiations.AFF3CT_COMMIT.startswith(af.AFF3CT_GIT_HASH[:7])


def test_streampu_is_imported_first():
    assert af._ext._streampu is spu
