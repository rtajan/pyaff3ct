# -*- coding: utf-8 -*-
"""Monitors (bit/frame error rate, EXIT chart, mutual information).

Class templates are grouped by dtype combination (``isinstance(x, mnt.<Class>)`` whatever the dtypes,
``mnt.<Class>[streampu.int32]`` for one instance); see ``aff3ct._dispatch.Template``.
"""

from typing import Any

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions


def reduce(sequence: Any, monitor: Any) -> Any:
    """Measures of all the threads of a sequence, in one monitor.

    A ``streampu.Sequence`` runs a clone of the monitor in each thread, and each clone measures its own frames
    (``Monitor_BFER_AR`` excepted, whose clones share their counters). ``reduce`` returns a new monitor of the same
    type holding the sum of the measures of the clones (the role of ``Monitor_reduction`` in the AFF3CT simulator).

    Args:
        sequence (streampu.Sequence): the sequence, after its execution.
        monitor (aff3ct.mnt.Monitor_BFER | Monitor_MI | Monitor_EXIT): the monitor given to the sequence.

    Returns:
        out (aff3ct.mnt.Monitor): a new monitor (same type and parameters) with the measures of all the threads
        (a ``Monitor_BFER_AR`` is returned as is).

    Examples:
        >>> seq = spu.Sequence(mnt["get_mutual_info::status"], n_threads=4)
        >>> seq.exec()
        >>> af.mnt.reduce(seq, mnt).mi                       # mean over the frames of the 4 threads
    """
    if hasattr(monitor, "is_shared_with"):  # Monitor_BFER_AR: its counters are already the totals of the threads
        return monitor
    clones = sequence.get_cloned_modules(monitor)
    total = clones[0].clone()
    total.reset()
    for clone in clones:
        total.collect(clone, True)
    return total


__all__ = sorted(export(_ext.mnt, globals()) + export_functions(globals(), "mnt") + ["reduce"])
