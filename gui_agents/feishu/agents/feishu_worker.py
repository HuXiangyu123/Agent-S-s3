"""Minimal Feishu runtime worker for launcher/cli integration."""

from __future__ import annotations

import datetime as dt
import io
import time
from typing import Any

import pyautogui
from PIL import Image

from gui_agents.feishu.contracts import RuntimeContext, StepResult
from gui_agents.feishu.detectors.im_state_detector import detect_feishu_state
from gui_agents.feishu.planner.task_planner import plan_testcase
from gui_agents.feishu.testcases.nl_parser import parse_instruction
from gui_agents.feishu.verifiers.assertion_verifier import AssertionVerifier
from gui_agents.feishu.workflows.send_message_workflow import (
    build_send_message_workflow,
)


def _runtime_failure(
    reason: str,
    failure_type: str = "precondition",
) -> RuntimeContext:
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat()
    return RuntimeContext(
        run_id=now.replace(":", "").replace("+", "_"),
        status="failed",
        workflow=None,
        workflow_params={},
        page_id=None,
        precondition_results=[],
        action_logs=[],
        screenshots=[],
        step_results=[],
        failure_type=failure_type,
        failure_reason=reason,
        started_at=now,
    )


def _settle_delay(action: str) -> float:
    if action == "open_chat":
        return 2.0
    if action == "send_message":
        return 1.5
    return 1.0


class FeishuWorker:
    """Bridge Track A/B/C modules to a minimal executable Feishu runtime."""

    def __init__(
        self,
        grounding_agent: Any,
        scaled_width: int,
        scaled_height: int,
    ) -> None:
        self.grounding_agent = grounding_agent
        self.scaled_width = scaled_width
        self.scaled_height = scaled_height
        self.verifier = AssertionVerifier()

    def run_instruction(
        self,
        instruction: str,
        max_steps: int = 15,
    ) -> RuntimeContext:
        print(f"FEISHU_TRACE: instruction={instruction}")
        try:
            testcase = parse_instruction(instruction)
        except Exception as exc:
            print(f"❌ Feishu parser failed: {exc}")
            print(
                "FEISHU_TRACE: recommendation=use classic_s3 for unsupported free-form tasks"
            )
            return _runtime_failure(str(exc), failure_type="precondition")

        print(
            "FEISHU_TRACE: testcase="
            + repr(
                {
                    "product": testcase["product"],
                    "title": testcase["title"],
                    "steps": testcase["steps"],
                }
            )
        )
        plan = plan_testcase(testcase)
        if plan.get("workflow") != "send_message":
            reason = plan.get("failure_reason") or "unsupported Feishu workflow"
            print(f"❌ Feishu planner rejected instruction: {reason}")
            return _runtime_failure(
                reason, failure_type=plan.get("failure_type") or "precondition"
            )
        print(
            "FEISHU_TRACE: workflow_plan="
            + repr(
                {
                    "workflow": plan["workflow"],
                    "workflow_params": plan["workflow_params"],
                    "entry_assertions": plan["entry_assertions"],
                }
            )
        )

        workflow = build_send_message_workflow(plan)
        now = dt.datetime.now(dt.timezone.utc).astimezone()
        runtime = RuntimeContext(
            run_id=now.strftime("%Y%m%d_%H%M%S"),
            status="running",
            workflow=plan["workflow"],
            workflow_params=dict(plan.get("workflow_params", {})),
            page_id=None,
            precondition_results=[],
            action_logs=[],
            screenshots=[],
            step_results=[],
            failure_type=None,
            failure_reason=None,
            started_at=now.isoformat(),
        )

        steps = workflow.steps()
        if max_steps < len(steps):
            print(
                f"⚠️ Step budget {max_steps} 小于 workflow 需要的 {len(steps)} 步，任务可能提前停止"
            )

        for index, step in enumerate(steps[:max_steps], start=1):
            print(f"\n🔄 Step {index}/{len(steps)}: {step['stage']}")
            print(
                "FEISHU_TRACE: step="
                + repr(
                    {
                        "stage": step["stage"],
                        "action": step["action"],
                        "target": step["target"],
                        "params": step["params"],
                        "success_gate": step["success_gate"],
                    }
                )
            )
            step_result = self._run_step(step)
            runtime["page_id"] = step_result["locator_result"].get("page_id")
            runtime["step_results"].append(step_result)
            runtime["action_logs"].append(
                {
                    "timestamp": dt.datetime.now(dt.timezone.utc)
                    .astimezone()
                    .isoformat(),
                    "step_id": step["step_id"],
                    "stage": step["stage"],
                    "action": step["action"],
                    "target": step["target"],
                    "params": dict(step["params"]),
                    "status": step_result["status"],
                }
            )
            if step_result["status"] != "passed":
                runtime["status"] = "failed"
                runtime["failure_type"] = step_result["failure_type"]
                runtime["failure_reason"] = step_result["failure_reason"]
                print(
                    f"❌ Step failed: {step_result['failure_type']} / {step_result['failure_reason']}"
                )
                return runtime

        case_result = self.verifier.verify_case(testcase, runtime)
        if case_result["passed"]:
            runtime["status"] = "passed"
            print("✅ Feishu workflow passed")
            return runtime

        runtime["status"] = "failed"
        runtime["failure_type"] = case_result["failure_type"]
        runtime["failure_reason"] = case_result["failure_reason"]
        print(
            f"❌ Feishu case verification failed: {case_result['failure_type']} / {case_result['failure_reason']}"
        )
        return runtime

    def _capture_observation(self) -> dict[str, Any]:
        screenshot = pyautogui.screenshot()
        width, height = screenshot.size
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        observation = {
            "screenshot": buffered.getvalue(),
            "image_width": width,
            "image_height": height,
            "ocr_text": self._extract_ocr_text(screenshot),
        }
        return observation

    def _extract_ocr_text(self, screenshot: Image.Image) -> str:
        pytesseract = self._load_pytesseract()
        if pytesseract is None:
            return ""
        try:
            text = pytesseract.image_to_string(screenshot, lang="chi_sim+eng")
            if text.strip():
                return text
        except Exception:
            pass
        try:
            return pytesseract.image_to_string(screenshot)
        except Exception:
            return ""

    def _load_pytesseract(self):
        try:
            import pytesseract  # type: ignore

            return pytesseract
        except Exception:
            return None

    def _run_code(self, code: str) -> tuple[bool, dict[str, Any], str | None]:
        print("EXECUTING CODE:", code.strip())
        namespace: dict[str, Any] = {}
        try:
            exec(code, namespace)
        except Exception as exc:  # pragma: no cover - runtime side effect
            return False, namespace, repr(exc)
        return True, namespace, None

    def _run_step(self, step: dict[str, Any]) -> StepResult:
        if step["action"] == "open_chat":
            return self._run_open_chat_step(step)
        if step["action"] == "type_message":
            return self._run_type_message_step(step)
        if step["action"] == "send_message":
            return self._run_send_message_step(step)
        return StepResult(
            step_id=step["step_id"],
            stage=step["stage"],
            action=step["action"],
            target=step["target"],
            status="failed",
            locator_result={"matched": False, "page_id": None, "strategy": "runtime"},
            verification_result={
                "passed": False,
                "assertion": step.get("success_gate"),
                "evidence": [],
                "failure_type": "action",
                "failure_reason": f"unsupported runtime action: {step['action']}",
            },
            failure_type="action",
            failure_reason=f"unsupported runtime action: {step['action']}",
        )

    def _run_open_chat_step(self, step: dict[str, Any]) -> StepResult:
        chat_name = step["params"]["chat_name"]
        code = "\n".join(
            [
                self.grounding_agent.feishu_focus(),
                self.grounding_agent.feishu_click(chat_name),
            ]
        )
        ok, namespace, error = self._run_code(code)
        time.sleep(_settle_delay("open_chat"))

        observation = self._capture_observation()
        state = detect_feishu_state(observation)
        verification = self.verifier.verify_step(
            {
                "step_id": step["step_id"],
                "assertion": step["success_gate"],
                "chat_name": chat_name,
                "params": dict(step["params"]),
                "target": chat_name,
            },
            state,
            observation,
        )

        if not verification["passed"]:
            fallback_code = self.grounding_agent.feishu_type(
                chat_name,
                element_description="搜索",
                overwrite=True,
                enter=True,
            )
            print("↪ open_chat direct click 未验证通过，尝试搜索框 fallback")
            fallback_ok, fallback_ns, fallback_error = self._run_code(fallback_code)
            ok = ok and fallback_ok
            namespace = fallback_ns if fallback_ok else namespace
            error = fallback_error or error
            time.sleep(_settle_delay("open_chat"))
            observation = self._capture_observation()
            state = detect_feishu_state(observation)
            verification = self.verifier.verify_step(
                {
                    "step_id": step["step_id"],
                    "assertion": step["success_gate"],
                    "chat_name": chat_name,
                    "params": dict(step["params"]),
                    "target": chat_name,
                },
                state,
                observation,
            )

        return self._build_step_result(
            step,
            state=state,
            verification=verification,
            namespace=namespace,
            ok=ok,
            error=error,
        )

    def _run_type_message_step(self, step: dict[str, Any]) -> StepResult:
        chat_name = step["params"].get("chat_name", "")
        text = step["params"]["text"]
        input_hint = f"发送给 {chat_name}" if chat_name else "发送给"
        code = self.grounding_agent.feishu_type(
            text,
            element_description=input_hint,
            overwrite=True,
            enter=False,
        )
        ok, namespace, error = self._run_code(code)
        time.sleep(_settle_delay("type_message"))

        observation = self._capture_observation()
        state = detect_feishu_state(observation)
        verification = self.verifier.verify_step(
            {
                "step_id": step["step_id"],
                "assertion": step["success_gate"],
                "params": dict(step["params"]),
                "payload": {"text": text},
            },
            state,
            observation,
        )

        if not verification["passed"]:
            fallback_code = self.grounding_agent.feishu_type(
                text,
                element_description="发送给",
                overwrite=True,
                enter=False,
            )
            print(
                "↪ type_message placeholder 精确定位未验证通过，尝试通用输入框 fallback"
            )
            fallback_ok, fallback_ns, fallback_error = self._run_code(fallback_code)
            ok = ok and fallback_ok
            namespace = fallback_ns if fallback_ok else namespace
            error = fallback_error or error
            time.sleep(_settle_delay("type_message"))
            observation = self._capture_observation()
            state = detect_feishu_state(observation)
            verification = self.verifier.verify_step(
                {
                    "step_id": step["step_id"],
                    "assertion": step["success_gate"],
                    "params": dict(step["params"]),
                    "payload": {"text": text},
                },
                state,
                observation,
            )

        return self._build_step_result(
            step,
            state=state,
            verification=verification,
            namespace=namespace,
            ok=ok,
            error=error,
        )

    def _run_send_message_step(self, step: dict[str, Any]) -> StepResult:
        text = step["params"].get("text")
        code = "import pyautogui\npyautogui.press('enter')\n"
        ok, namespace, error = self._run_code(code)
        time.sleep(_settle_delay("send_message"))

        observation = self._capture_observation()
        state = detect_feishu_state(observation)
        verification = self.verifier.verify_step(
            {
                "step_id": step["step_id"],
                "assertion": step["success_gate"],
                "params": dict(step["params"]),
                "payload": {"text": text} if text else None,
            },
            state,
            observation,
        )

        if not verification["passed"]:
            fallback_code = self.grounding_agent.feishu_click("发送")
            print("↪ send_message Enter 未验证通过，尝试点击发送按钮 fallback")
            fallback_ok, fallback_ns, fallback_error = self._run_code(fallback_code)
            ok = ok and fallback_ok
            namespace = fallback_ns if fallback_ok else namespace
            error = fallback_error or error
            time.sleep(_settle_delay("send_message"))
            observation = self._capture_observation()
            state = detect_feishu_state(observation)
            verification = self.verifier.verify_step(
                {
                    "step_id": step["step_id"],
                    "assertion": step["success_gate"],
                    "params": dict(step["params"]),
                    "payload": {"text": text} if text else None,
                },
                state,
                observation,
            )

        return self._build_step_result(
            step,
            state=state,
            verification=verification,
            namespace=namespace,
            ok=ok,
            error=error,
        )

    def _build_step_result(
        self,
        step: dict[str, Any],
        state: dict[str, Any],
        verification: dict[str, Any],
        namespace: dict[str, Any],
        ok: bool,
        error: str | None,
    ) -> StepResult:
        locator_result = {
            "matched": bool(namespace.get("clicked", ok)),
            "page_id": state.get("page_type"),
            "strategy": "feishu_uia_runtime",
        }
        if verification["passed"]:
            return StepResult(
                step_id=step["step_id"],
                stage=step["stage"],
                action=step["action"],
                target=step["target"],
                status="passed",
                locator_result=locator_result,
                verification_result=verification,
                failure_type=None,
                failure_reason=None,
            )

        failure_reason = verification.get("failure_reason") or error or "step failed"
        return StepResult(
            step_id=step["step_id"],
            stage=step["stage"],
            action=step["action"],
            target=step["target"],
            status="failed",
            locator_result=locator_result,
            verification_result=verification,
            failure_type=verification.get("failure_type") or "verification",
            failure_reason=failure_reason,
        )
