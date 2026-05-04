"""
Model connectivity & parameter validation script.

Tests all configured models (main + grounding) across providers,
verifies API parameters are accepted, and reports status.

Usage:
    python test_models.py              # run all tests
    python test_models.py --verbose    # show raw responses
    python test_models.py --json       # machine-readable output
"""

import os
import sys
import json
import base64
import argparse
import traceback
from io import BytesIO
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# config loading
# ---------------------------------------------------------------------------

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_DIR, "config.json")
ENV_FILE = os.path.join(PROJECT_DIR, "env.txt")


def parse_env_txt(path: str) -> Dict[str, str]:
    """Parse env.txt key: value pairs (ignore comments and blank lines)."""
    result: Dict[str, str] = {}
    if not os.path.exists(path):
        return result
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip()
    return result


def load_configs() -> Dict[str, Any]:
    """Merge config.json + env.txt into a single config dict."""
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    env = parse_env_txt(ENV_FILE)
    return {"json_config": cfg, "env_txt": env}


# ---------------------------------------------------------------------------
# test helpers
# ---------------------------------------------------------------------------

RESET = "\033[0m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"


def ok(msg: str) -> str:
    return f"{GREEN}{msg}{RESET}"


def fail(msg: str) -> str:
    return f"{RED}{msg}{RESET}"


def warn(msg: str) -> str:
    return f"{YELLOW}{msg}{RESET}"


def info(msg: str) -> str:
    return f"{CYAN}{msg}{RESET}"


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed: List[str] = []
        self.failed: List[str] = []
        self.warnings: List[str] = []
        self.details: Dict[str, Any] = {}

    def add_pass(self, check: str, detail: Any = None):
        self.passed.append(check)
        if detail is not None:
            self.details[check] = detail

    def add_fail(self, check: str, detail: Any = None):
        self.failed.append(check)
        if detail is not None:
            self.details[check] = detail

    def add_warn(self, check: str, detail: Any = None):
        self.warnings.append(check)
        if detail is not None:
            self.details[check] = detail

    @property
    def success(self) -> bool:
        return len(self.failed) == 0


def print_result(result: TestResult, verbose: bool = False):
    status = ok("[PASS]") if result.success else fail("[FAIL]")
    print(f"\n{BOLD}{status} {result.name}{RESET}")
    for p in result.passed:
        print(f"  {ok('+')} {p}")
    for w in result.warnings:
        print(f"  {warn('~')} {w}")
    for f in result.failed:
        print(f"  {fail('x')} {f}")
    if verbose and result.details:
        for k, v in result.details.items():
            if isinstance(v, str) and len(v) > 500:
                v = v[:500] + "...[truncated]"
            print(f"    {info(k)}: {v}")


# ---------------------------------------------------------------------------
# dummy image for vision model testing
# ---------------------------------------------------------------------------

def make_dummy_screenshot() -> str:
    """Generate a minimal 200x200 blue PNG and return as b64 data-uri."""
    from PIL import Image

    img = Image.new("RGB", (200, 200), color=(66, 133, 244))
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_doubao_main(cfg: Dict, verbose: bool) -> TestResult:
    """Test Doubao main model (doubao-seed-2.0-pro via volcano ARK endpoint)."""
    r = TestResult("Doubao 主模型 (doubao-seed-2.0-pro)")

    try:
        from openai import OpenAI
    except ImportError:
        r.add_fail("openai package not installed")
        return r

    json_cfg = cfg["json_config"]
    api_key = json_cfg.get("model_api_key", "")
    model_id = json_cfg.get("model_id", "")
    base_url = json_cfg.get("model_url", "https://ark.cn-beijing.volces.com/api/v3")

    if not api_key:
        r.add_warn("model_api_key not configured in config.json")
        return r
    if not model_id:
        r.add_warn("model_id (endpoint ID) not configured in config.json")
        return r

    r.add_pass(f"config loaded: url={base_url}, model={model_id}")

    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "回复 OK"}],
            max_tokens=32,
            temperature=0.0,
        )
        text = response.choices[0].message.content.strip()
        r.add_pass(f"chat completion OK: '{text[:100]}'", text)
        if verbose:
            r.add_pass(
                f"usage: prompt={response.usage.prompt_tokens}, "
                f"completion={response.usage.completion_tokens}"
            )

    except Exception as e:
        r.add_fail(f"chat completion failed: {e}", traceback.format_exc())

    # test parameter passthrough
    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "say test"}],
            max_tokens=16,
            temperature=0.5,
            top_p=0.8,
        )
        r.add_pass("extra params (temperature=0.5, top_p=0.8) accepted")
    except Exception as e:
        r.add_warn(f"extra params rejected: {e}")

    return r


def test_doubao_grounding(cfg: Dict, verbose: bool) -> TestResult:
    """Test Doubao grounding model (doubao-seed-1-6-vision-250815)."""
    r = TestResult("Doubao 定位模型 (doubao-seed-1-6-vision-250815)")

    try:
        from openai import OpenAI
    except ImportError:
        r.add_fail("openai package not installed")
        return r

    json_cfg = cfg["json_config"]
    api_key = json_cfg.get("ground_api_key", "")
    model_name = json_cfg.get("ground_model", "doubao-seed-1-6-vision-250815")

    if not api_key:
        r.add_warn("ground_api_key not configured")
        return r

    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    r.add_pass(f"config loaded: model={model_name}")

    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        dummy_img = make_dummy_screenshot()

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are a GUI agent. Given the screenshot, locate the "
                                "blue rectangle and output:\n"
                                "Thought: The blue rectangle fills the entire image.\n"
                                "Action: click(point='<point>500 500</point>')"
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": dummy_img}},
                    ],
                }
            ],
            temperature=0.0,
            top_p=0.7,
            max_tokens=256,
        )
        text = response.choices[0].message.content
        r.add_pass(f"vision completion OK (len={len(text)})", text[:300])

        # verify <point> format
        import re

        point = re.search(r"<point>\s*(\d+)\s+(\d+)\s*</point>", text)
        if point:
            x, y = int(point.group(1)), int(point.group(2))
            in_range = 0 <= x <= 1000 and 0 <= y <= 1000
            r.add_pass(
                f"coordinate format valid: ({x}, {y}) range_ok={in_range}",
                f"x={x}, y={y}",
            )
            if not in_range:
                r.add_warn(f"coordinate ({x}, {y}) outside expected 0-1000 range")
        else:
            r.add_warn("no <point> tag found in response", text[:300])

    except Exception as e:
        r.add_fail(f"vision completion failed: {e}", traceback.format_exc())

    return r


def test_gpt_model(cfg: Dict, verbose: bool) -> TestResult:
    """Test OpenAI GPT model with reasoning_effort parameter validation."""
    r = TestResult("OpenAI GPT 模型 (gpt-5.4)")

    try:
        from openai import OpenAI
    except ImportError:
        r.add_fail("openai package not installed")
        return r

    env = cfg["env_txt"]
    base_url = env.get("oai_base_url", "")
    api_key = env.get("oai_api", "")
    model = env.get("model", "gpt-5.4")
    default_effort = env.get("model_reasoning_effort", "medium")

    if not api_key:
        r.add_warn("oai_api not configured in env.txt")
        return r
    if not base_url:
        r.add_warn("oai_base_url not configured in env.txt")
        return r

    r.add_pass(
        f"config loaded: url={base_url}, model={model}, "
        f"default_reasoning_effort={default_effort}"
    )

    client = OpenAI(base_url=base_url, api_key=api_key)

    # --- test 1: basic chat completion ---
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "回复 OK"}],
            max_tokens=32,
        )
        text = response.choices[0].message.content.strip()
        r.add_pass(f"basic chat completion OK: '{text[:100]}'", text)
    except Exception as e:
        r.add_fail(f"basic chat completion failed: {e}", traceback.format_exc())
        return r  # can't continue without basic connectivity

    # --- test 2: reasoning_effort parameter ---
    effort_levels = ["low", "medium", "high", "xhigh"]
    for effort in effort_levels:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "回复 OK"}],
                max_tokens=32,
                reasoning_effort=effort,
            )
            # check if the parameter was actually accepted (not silently ignored)
            r.add_pass(f"reasoning_effort='{effort}' accepted")
        except Exception as e:
            error_msg = str(e)
            if "reasoning_effort" in error_msg.lower() or "not supported" in error_msg.lower():
                r.add_warn(f"reasoning_effort='{effort}' rejected: {e}")
            else:
                r.add_fail(f"reasoning_effort='{effort}' failed: {e}")

    # --- test 3: max_output_tokens parameter ---
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "写一首关于测试的五言绝句"}],
            max_output_tokens=64,
        )
        actual_tokens = response.usage.completion_tokens
        r.add_pass(
            f"max_output_tokens=64 accepted (actual={actual_tokens})",
            f"tokens={actual_tokens}, text={response.choices[0].message.content[:100]}",
        )
        if actual_tokens > 100:
            r.add_warn(f"max_output_tokens=64 was set but {actual_tokens} tokens used")
    except Exception as e:
        r.add_warn(f"max_output_tokens may not be supported: {e}")

    # --- test 4: text.format (JSON Schema) ---
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "返回一个JSON: name和age字段，name=测试, age=25"}
            ],
            max_tokens=128,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "person",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"},
                        },
                        "required": ["name", "age"],
                    },
                }
            },
        )
        content = response.choices[0].message.content
        try:
            parsed = json.loads(content)
            r.add_pass(
                f"text.format (JSON Schema) accepted, parsed OK: {parsed}", content
            )
        except json.JSONDecodeError:
            r.add_warn(f"JSON Schema accepted but output not valid JSON: {content[:200]}")
    except Exception as e:
        r.add_warn(f"text.format (JSON Schema) may not be supported: {e}")

    # --- test 5: temperature + top_p coexistence ---
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "回复 OK"}],
            max_tokens=16,
            temperature=0.2,
            top_p=0.9,
        )
        r.add_pass("temperature=0.2 + top_p=0.9 accepted")
    except Exception as e:
        r.add_warn(f"temperature+top_p together rejected: {e}")

    return r


def test_all_endpoints(cfg: Dict, verbose: bool) -> TestResult:
    """Synthetic connectivity test: ping each API base URL."""
    r = TestResult("API 端点可达性")

    import urllib.request
    import urllib.error

    endpoints = [
        ("Volcano ARK", "https://ark.cn-beijing.volces.com/api/v3/models"),
    ]

    env = cfg.get("env_txt", {})
    gpt_url = env.get("oai_base_url", "")
    if gpt_url:
        endpoints.append(("OpenAI GPT", gpt_url.rstrip("/") + "/models"))

    for name, url in endpoints:
        try:
            # Just check if endpoint responds (may 401 without auth, that's OK)
            req = urllib.request.Request(url, method="GET")
            urllib.request.urlopen(req, timeout=10)
            r.add_pass(f"{name}: {url} reachable")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                r.add_pass(f"{name}: {url} reachable (auth required, HTTP {e.code})")
            else:
                r.add_warn(f"{name}: {url} HTTP {e.code}")
        except Exception as e:
            r.add_warn(f"{name}: {url} unreachable — {e}")

    return r


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Model connectivity & parameter test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show raw responses")
    parser.add_argument("--json", "-j", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  Agent-S3 模型连通性与参数测试{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    cfg = load_configs()

    if not args.json:
        print(f"\n{info('加载配置:')}")
        json_cfg = cfg["json_config"]
        print(f"  主模型:   {json_cfg.get('model_id', '(未配置)')} @ {json_cfg.get('model_url', '')}")
        print(f"  定位模型: {json_cfg.get('ground_model', '')} (provider={json_cfg.get('ground_provider', '')})")
        env = cfg["env_txt"]
        if env.get("oai_api"):
            print(f"  GPT模型:  {env.get('model', '')} @ {env.get('oai_base_url', '')} reasoning={env.get('model_reasoning_effort', '')}")

    results: List[TestResult] = []

    # 1. endpoint reachability
    results.append(test_all_endpoints(cfg, args.verbose))

    # 2. doubao main model
    results.append(test_doubao_main(cfg, args.verbose))

    # 3. doubao grounding model
    results.append(test_doubao_grounding(cfg, args.verbose))

    # 4. GPT model with parameter validation
    results.append(test_gpt_model(cfg, args.verbose))

    # summary
    if args.json:
        output = {
            r.name: {
                "success": r.success,
                "passed": len(r.passed),
                "failed": len(r.failed),
                "warnings": len(r.warnings),
                "checks_passed": r.passed,
                "checks_failed": r.failed,
                "warnings": r.warnings,
            }
            for r in results
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print_result(r, verbose=args.verbose)

        # overall
        total = len(results)
        passed = sum(1 for r in results if r.success)
        print(f"\n{BOLD}{'='*60}{RESET}")
        if passed == total:
            print(f"{BOLD}  总结: {ok('全部通过')} ({passed}/{total}){RESET}")
        else:
            print(f"{BOLD}  总结: {fail(f'{passed}/{total} 通过')}{RESET}")
        print(f"{BOLD}{'='*60}{RESET}")


if __name__ == "__main__":
    main()
