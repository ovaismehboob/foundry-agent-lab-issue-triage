"""Send a message to the agent server running locally (python main.py or the Docker container).

Uses only the Python standard library. The request follows the Responses protocol that the
Agent Framework hosting adapter serves on port 8088.

Usage (from the repository root):
    python scripts/invoke_local_agent.py "Triage ISS-1001"
    python scripts/invoke_local_agent.py --port 18088 "Triage ISS-1014"
    python scripts/invoke_local_agent.py --previous-response-id <id> "Why that priority?"
    python scripts/invoke_local_agent.py --ready        # only check GET /readiness
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def output_text(body: dict) -> str:
    parts = []
    for item in body.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in ("output_text", "text") and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("message", nargs="?")
    parser.add_argument("--port", type=int, default=8088)
    parser.add_argument("--previous-response-id")
    parser.add_argument("--ready", action="store_true")
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    base = f"http://localhost:{args.port}"

    if args.ready:
        try:
            with urllib.request.urlopen(f"{base}/readiness", timeout=10) as response:
                print(f"readiness: HTTP {response.status}")
                return 0
        except (urllib.error.URLError, OSError) as error:
            print(f"Agent server is not reachable on port {args.port}: {error}")
            return 1

    if not args.message:
        parser.error("provide a message, or use --ready")
    payload = {"input": args.message, "stream": False}
    if args.previous_response_id:
        payload["previous_response_id"] = args.previous_response_id
    request = urllib.request.Request(
        f"{base}/responses", data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode('utf-8', errors='replace')[:1000]}")
        return 1
    except (urllib.error.URLError, OSError) as error:
        print(f"Agent server is not reachable on port {args.port}: {error}")
        return 1

    print(f"status: {body.get('status')}   response id: {body.get('id')}")
    if body.get("error"):
        print(f"error: {body['error'].get('code')}: {body['error'].get('message')}")
        return 1
    print(output_text(body) or json.dumps(body, indent=2)[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
