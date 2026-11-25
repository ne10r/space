"""Translate three domain configurations through the real stdin/stdout CLI."""

import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "web": {
        "HTTP/HOST": "api.example.test", "HTTP/PORT": "8080.0",
        "DATABASE/POOL/MAX": "10.0",
    },
    "laboratory": {
        "SENSOR/MODEL": "T & H <logger>",
        "SENSOR/CALIBRATION/OFFSET": "-0.25", "LIMITS/REFERENCE": "21.50",
    },
    "game": {
        "DISPLAY/WIDTH": "1280.0", "PLAYER/MOVEMENT/SPEED": "100.0",
        "SCORE/MULTIPLIER": "1.5",
    },
}


def run_example(name: str, expected: dict) -> dict:
    """Check actual emitted XML and save it under the ignored build folder."""
    source = ROOT / "examples" / (name + ".conf")
    result = subprocess.run(
        [sys.executable, "-m", "src.main"], cwd=ROOT,
        input=source.read_text(encoding="utf-8"), capture_output=True,
        text=True, encoding="utf-8", timeout=10, check=True,
    )
    if result.stderr:
        raise AssertionError(result.stderr)
    root = ElementTree.fromstring(result.stdout)
    actual = {path: root.find(path).text for path in expected}
    if actual != expected:
        raise AssertionError(f"{name}: {actual} != {expected}")
    output = ROOT / "build/examples" / (name + ".xml")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.stdout, encoding="utf-8")
    return {
        "source": "examples/" + source.name,
        "output": "build/examples/" + output.name,
        "root_type": root.get("type"), "checked_values": actual,
        "matched": True,
    }


def main() -> None:
    """Record the CLI output checks for all three subject domains."""
    results = [run_example(name, expected) for name, expected in CASES.items()]
    report = ROOT / "reports/examples.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for result in results:
        print(f"{result['source']} -> {result['output']}: OK")
    print("Saved report: reports/examples.json")


if __name__ == "__main__":
    main()
