#!/usr/bin/env python3
"""Send one bounded Deepskin gesture request to the IM Agent SSE endpoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deepskin_agent import post_agent_sse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--label", default="TAP")
    parser.add_argument("--timeout-s", type=float, default=20.0)
    args = parser.parse_args()
    result = post_agent_sse(
        url=args.url,
        user_id=args.user_id,
        session_id=args.session_id,
        label=args.label,
        status={"Mood": 0, "Favor": 0, "Egy": -1, "Stress": 0},
        timeout_s=args.timeout_s,
    )
    print(json.dumps({
        "label": result.label,
        "text": result.text,
        "value": result.value,
        "done": result.raw_done,
    }, ensure_ascii=False, indent=2))
