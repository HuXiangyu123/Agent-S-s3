import unittest
from unittest.mock import patch

from gui_agents.s3.agents.worker import Worker


class _FakeAgent:
    def __init__(self) -> None:
        self.messages = []
        self.system_prompt = ""
        self.add_system_prompt("base")

    def add_system_prompt(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt
        message = {
            "role": "system",
            "content": [{"type": "text", "text": system_prompt}],
        }
        if self.messages:
            self.messages[0] = message
        else:
            self.messages.append(message)

    def add_message(
        self,
        text_content,
        image_content=None,
        role=None,
        image_detail="high",
        put_text_last=False,
    ) -> None:
        content = [{"type": "text", "text": text_content}]
        if image_content is not None:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,AA=="},
                }
            )
        self.messages.append({"role": role or "user", "content": content})


class _FakeGroundingAgent:
    def __init__(self) -> None:
        self.notes = []
        self.last_code_agent_result = None
        self.assigned_obs = None
        self.task_instruction = None

    def assign_screenshot(self, obs):
        self.assigned_obs = obs

    def set_task_instruction(self, instruction: str) -> None:
        self.task_instruction = instruction

    def build_worker_system_prompt(self, instruction: str, platform: str) -> str:
        return (
            "SYSTEM\n"
            "First reason from the screenshot before choosing a tool.\n"
            "Use agent.feishu_type_message(...) when the composer is visible.\n"
            f"TASK={instruction}\nPLATFORM={platform}"
        )

    def build_dynamic_guidance(self, instruction: str, obs: dict) -> str:
        return "DYNAMIC TOOL GUIDANCE SHOULD NOT BE IN USER TURN"

    def wait(self, seconds: float) -> str:
        return f"WAIT({seconds})"


class TestWorkerRuntimePrompt(unittest.TestCase):
    def test_worker_does_not_inject_dynamic_guidance_into_user_turn(self) -> None:
        grounding_agent = _FakeGroundingAgent()

        with patch.object(
            Worker, "_create_agent", side_effect=lambda *args, **kwargs: _FakeAgent()
        ):
            worker = Worker(
                {"engine_type": "openai", "model": "gpt-4o"},
                grounding_agent,
                platform="windows",
                enable_reflection=False,
            )

        response = """(Observe)\nScreen ready.\n(State Verification)\nFirst step - no expected state.\n(Next Action)\nWait briefly.\n(Expected Next State)\nUI settles.\n```python\nagent.wait(1.0)\n```"""
        obs = {"screenshot": b"fake-image"}

        with patch(
            "gui_agents.s3.agents.worker.call_llm_formatted", return_value=response
        ):
            worker.generate_next_action("打开消息中的bot功能测试群聊并发送hello", obs)

        self.assertGreaterEqual(len(worker.generator_agent.messages), 3)
        user_turn = worker.generator_agent.messages[1]["content"][0]["text"]
        self.assertNotIn("DYNAMIC TOOL GUIDANCE", user_turn)
        self.assertNotIn(
            "DYNAMIC TOOL GUIDANCE SHOULD NOT BE IN USER TURN",
            user_turn,
        )
        self.assertIn("Current Text Buffer", user_turn)
        self.assertIn(
            "First reason from the screenshot before choosing a tool.",
            worker.generator_agent.messages[0]["content"][0]["text"],
        )


if __name__ == "__main__":
    unittest.main()
