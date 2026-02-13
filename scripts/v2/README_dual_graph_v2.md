# Dual Graph v2 (Graph A causal + Graph B methods)

This v2 workflow is **fully independent** from the current v1 graphs used by the system.
All outputs are written under `outputs/dual_graph_v2/`.

## 1) Extract per-paper delta from a PDF

```bash
python scripts/v2/extract_dual_graph_v2_from_pdf.py path/to/paper.pdf
```

Output:
- `outputs/dual_graph_v2/per_paper/<paper>_dual_graph_v2.json`

Prompt template:
- `prompts/dual_graph_v2_extraction_prompt.md`

## 2) Merge many deltas into merged v2 graphs

```bash
python scripts/v2/merge_dual_graph_v2.py --in-dir outputs/dual_graph_v2/per_paper --out-dir outputs/dual_graph_v2
```

Outputs:
- `outputs/dual_graph_v2/causal_graph_v2.json`
- `outputs/dual_graph_v2/method_graph_v2.json`

## 3) Schemas (optional validation)

- `schemas/causal_graph_v2.schema.json`
- `schemas/method_graph_v2.schema.json`
- `schemas/dual_graph_v2_delta.schema.json`

