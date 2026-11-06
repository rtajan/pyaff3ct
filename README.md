# pyaff3ct

Python bindings (pybind11) for [AFF3CT](https://github.com/aff3ct/aff3ct), built as a
[pystreampu](https://github.com/aff3ct/pystreampu) plugin: every AFF3CT module is a `streampu.Module`,
its tasks are callable from Python and its sockets are exposed as NumPy arrays.

Status: design phase. See:

- [`Plan.md`](Plan.md) — architecture, wrapping rules and roadmap;
- [`docs/design/class_graph.md`](docs/design/class_graph.md) — graph of the classes to wrap;
- [`docs/design/inventory.md`](docs/design/inventory.md) — per-class wrapping backlog.

Regenerate the design documents after bumping AFF3CT:

```bash
python3 scripts/gen_class_graph.py path/to/aff3ct/include docs/design
```
