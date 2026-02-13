#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Dual-Graph v2 delta (Graph A causal + Graph B method) from a single PDF paper.

Outputs one JSON file per paper under:
  outputs/dual_graph_v2/per_paper/<paper_stem>_dual_graph_v2.json

This script does NOT touch existing v1 graphs.
"""

import os
import json
import base64
import time
from pathlib import Path
from typing import Any, Dict, Optional

import anthropic
from dotenv import load_dotenv


load_dotenv()


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _encode_pdf_base64(pdf_path: Path) -> str:
    with open(pdf_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


class DualGraphV2ClaudeExtractor:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        prompt_file: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("JUHENEXT_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.getenv("JUHENEXT_BASE_URL") or "https://api.anthropic.com"
        if not self.api_key:
            raise ValueError("Missing API key: set JUHENEXT_API_KEY or ANTHROPIC_API_KEY")

        self.model = model or os.getenv("CLAUDE_MODEL") or "claude-sonnet-4-20250514"
        self.client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)

        prompt_path = Path(prompt_file) if prompt_file else Path("prompts/dual_graph_v2_extraction_prompt.md")
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        self.prompt = _read_text_file(prompt_path)

    def extract_from_pdf(self, pdf_path: str, max_tokens: int = 4096) -> Dict[str, Any]:
        pdf = Path(pdf_path)
        if not pdf.exists():
            return {"success": False, "error": f"PDF not found: {pdf}"}

        pdf_b64 = _encode_pdf_base64(pdf)
        start = time.time()

        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64},
                        },
                        {"type": "text", "text": self.prompt},
                    ],
                }
            ],
        )

        raw = msg.content[0].text if msg and msg.content else ""
        elapsed = time.time() - start
        parsed = self._parse_json(raw)
        parsed["success"] = parsed.get("success", True)
        parsed["meta"] = {
            "model": self.model,
            "elapsed_seconds": elapsed,
            "source_pdf": str(pdf),
        }
        return parsed

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        t = text.strip()
        # Remove accidental markdown fences if present
        if "```json" in t:
            start = t.find("```json") + 7
            end = t.rfind("```")
            t = t[start:end].strip() if end > start else t[start:].strip()
        elif t.startswith("```"):
            start = t.find("```") + 3
            end = t.rfind("```")
            t = t[start:end].strip() if end > start else t[start:].strip()

        try:
            return json.loads(t)
        except Exception as e:
            return {"success": False, "error": f"JSON parse failed: {e}", "raw_response_head": t[:2000]}


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", help="Path to a PDF paper")
    parser.add_argument("--out-dir", default="outputs/dual_graph_v2/per_paper", help="Output directory")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--model", default=None)
    parser.add_argument("--prompt-file", default=None)
    args = parser.parse_args()

    extractor = DualGraphV2ClaudeExtractor(model=args.model, prompt_file=args.prompt_file)
    result = extractor.extract_from_pdf(args.pdf, max_tokens=args.max_tokens)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{Path(args.pdf).stem}_dual_graph_v2.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote: {out_file}")


if __name__ == "__main__":
    main()

