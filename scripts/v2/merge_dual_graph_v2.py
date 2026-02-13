#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge many per-paper dual_graph_v2 delta JSON files into:
  outputs/dual_graph_v2/causal_graph_v2.json
  outputs/dual_graph_v2/method_graph_v2.json

This does NOT modify any existing v1 graph files.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _pattern_key(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True)
class EdgeKey:
    source: str
    target: str
    effect_type: str


def merge_dual_graph_v2(deltas: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    # Aggregated containers
    variables_by_id: Dict[str, Dict[str, Any]] = {}
    methods_by_id: Dict[str, Dict[str, Any]] = {}
    pipelines_by_id: Dict[str, Dict[str, Any]] = {}

    edges_by_key: Dict[EdgeKey, Dict[str, Any]] = {}
    complex_by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}  # (type, pattern_json)

    papers: List[str] = []

    for delta in deltas:
        paper_meta = delta.get("paper_meta", {}) or {}
        paper_title = paper_meta.get("title") or "Unknown"
        if paper_title not in papers:
            papers.append(paper_title)

        ga = delta.get("graph_A_delta", {}) or {}
        gb = delta.get("graph_B_delta", {}) or {}

        # Variables: merge by id
        for v in ga.get("variables", []) or []:
            vid = v.get("id")
            if not vid:
                continue
            if vid not in variables_by_id:
                variables_by_id[vid] = v
            else:
                # merge source/tags conservatively
                cur = variables_by_id[vid]
                cur.setdefault("source", [])
                cur.setdefault("tags", [])
                if isinstance(cur.get("source"), list) and isinstance(v.get("source"), list):
                    cur["source"] = sorted(set(cur["source"]) | set(v["source"]))
                if isinstance(cur.get("tags"), list) and isinstance(v.get("tags"), list):
                    cur["tags"] = sorted(set(cur["tags"]) | set(v["tags"]))
                # if definition differs, keep first and record note
                if v.get("definition") and cur.get("definition") and v["definition"] != cur["definition"]:
                    cur.setdefault("notes", [])
                    cur["notes"].append({"type": "definition_conflict", "paper": paper_title, "definition": v["definition"]})

        # Causal edges: merge by (source,target,effect_type)
        for e in ga.get("causal_edges", []) or []:
            s = e.get("source")
            t = e.get("target")
            et = e.get("effect_type", "unknown")
            if not s or not t:
                continue
            key = EdgeKey(source=s, target=t, effect_type=et)
            if key not in edges_by_key:
                edges_by_key[key] = e
            else:
                cur = edges_by_key[key]
                # evidence aggregation
                cur_ev = cur.get("evidence", {}) or {}
                e_ev = e.get("evidence", {}) or {}
                cur_ev["validated"] = bool(cur_ev.get("validated")) or bool(e_ev.get("validated"))
                cur_ev["evidence_count"] = int(cur_ev.get("evidence_count", 0)) + int(e_ev.get("evidence_count", 0))
                cur_ev.setdefault("papers", [])
                cur_ev.setdefault("sample_quotes", [])
                cur_ev.setdefault("domains", [])
                cur_ev["papers"] = sorted(set(cur_ev["papers"]) | set(e_ev.get("papers", []) or []))
                cur_ev["sample_quotes"] = list(dict.fromkeys((cur_ev["sample_quotes"] or []) + (e_ev.get("sample_quotes", []) or [])))[:20]
                cur_ev["domains"] = sorted(set(cur_ev["domains"]) | set(e_ev.get("domains", []) or []))
                cur["evidence"] = cur_ev
                # detect effect_size conflicts
                if cur.get("effect_size") and e.get("effect_size") and cur["effect_size"] != e["effect_size"]:
                    cur.setdefault("notes", [])
                    cur["notes"].append({"type": "effect_size_conflict", "paper": paper_title, "effect_size": e["effect_size"]})

        # Complex relations: merge by (type, pattern)
        for cr in ga.get("complex_relations", []) or []:
            cr_type = cr.get("type")
            pattern = cr.get("pattern", {})
            if not cr_type:
                continue
            pkey = _pattern_key(pattern)
            key2 = (cr_type, pkey)
            if key2 not in complex_by_key:
                complex_by_key[key2] = cr
            else:
                cur = complex_by_key[key2]
                cur_ev = cur.get("evidence", {}) or {}
                ev = cr.get("evidence", {}) or {}
                cur_ev.setdefault("papers", [])
                cur_ev["papers"] = sorted(set(cur_ev["papers"]) | set(ev.get("papers", []) or []))
                if ev.get("description") and cur_ev.get("description") and ev["description"] != cur_ev["description"]:
                    cur_ev.setdefault("notes", [])
                    cur_ev["notes"].append({"paper": paper_title, "description": ev["description"]})
                cur["evidence"] = cur_ev

        # Methods: merge by id
        for m in gb.get("methods", []) or []:
            mid = m.get("id")
            if not mid:
                continue
            if mid not in methods_by_id:
                methods_by_id[mid] = m
            else:
                cur = methods_by_id[mid]
                cur.setdefault("synonyms", [])
                cur_syn = cur.get("synonyms") or []
                m_syn = m.get("synonyms") or []
                if isinstance(cur_syn, list) and isinstance(m_syn, list):
                    cur["synonyms"] = sorted(set(cur_syn) | set(m_syn))
                # evidence merge
                cur_ev = cur.get("evidence", {}) or {}
                ev = m.get("evidence", {}) or {}
                cur_ev.setdefault("papers", [])
                cur_ev.setdefault("domains", [])
                cur_ev["papers"] = sorted(set(cur_ev["papers"]) | set(ev.get("papers", []) or []))
                cur_ev["domains"] = sorted(set(cur_ev["domains"]) | set(ev.get("domains", []) or []))
                cur["evidence"] = cur_ev

        # Pipelines: merge by id (simple)
        for p in gb.get("pipelines", []) or []:
            pid = p.get("id")
            if not pid:
                continue
            if pid not in pipelines_by_id:
                pipelines_by_id[pid] = p
            else:
                cur = pipelines_by_id[pid]
                cur.setdefault("related_causal_edges", [])
                cur["related_causal_edges"] = sorted(set(cur["related_causal_edges"]) | set(p.get("related_causal_edges", []) or []))

    causal_graph = {
        "meta": {
            "name": "Patent Analysis Causal Graph v2",
            "version": "2.0",
            "description": "Merged causal graph v2 from per-paper deltas",
            "created_at": "",
            "papers": papers,
        },
        "variables": list(variables_by_id.values()),
        "causal_edges": list(edges_by_key.values()),
        "complex_relations": list(complex_by_key.values()),
    }

    method_graph = {
        "meta": {
            "name": "Patent Analysis Method Graph v2",
            "version": "2.0",
            "description": "Merged method graph v2 from per-paper deltas",
            "created_at": "",
        },
        "methods": list(methods_by_id.values()),
        "pipelines": list(pipelines_by_id.values()),
    }

    return causal_graph, method_graph


def main():
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", default="outputs/dual_graph_v2/per_paper", help="Directory with per-paper delta json")
    parser.add_argument("--out-dir", default="outputs/dual_graph_v2", help="Directory to write merged graphs")
    args = parser.parse_args()

    in_dir = Path(args.in_dir)
    files = sorted(in_dir.glob("*_dual_graph_v2.json"))
    if not files:
        raise SystemExit(f"No per-paper files found in {in_dir}")

    deltas = [_load_json(p) for p in files]
    cg, mg = merge_dual_graph_v2(deltas)

    now = datetime.utcnow().isoformat() + "Z"
    cg["meta"]["created_at"] = now
    mg["meta"]["created_at"] = now

    out_dir = Path(args.out_dir)
    _dump_json(out_dir / "causal_graph_v2.json", cg)
    _dump_json(out_dir / "method_graph_v2.json", mg)
    print(f"[OK] wrote merged graphs to {out_dir}")


if __name__ == "__main__":
    main()

