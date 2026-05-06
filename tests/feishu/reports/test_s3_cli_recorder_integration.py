import unittest


class _FakeGroundingAgent:
    def capture_observation(self, scaled_width, scaled_height):
        return {
            "screenshot": b"fake-png-bytes",
            "image_width": scaled_width,
            "image_height": scaled_height,
        }


class _FakeAgent:
    def __init__(self):
        self.grounding_agent = _FakeGroundingAgent()
        self.predictions = 0

    def predict(self, instruction, observation):
        self.predictions += 1
        return {"executor_plan": "done"}, ["agent.done()"]


class _FakeRecorder:
    def __init__(self):
        self.started_with = None
        self.observations = []
        self.actions = []
        self.finalized_with = None

    def start(self, instruction):
        self.started_with = instruction

    def record_observation(self, step_index, observation):
        self.observations.append((step_index, observation))

    def record_action(self, step_index, exec_code, status, failure_reason=None):
        self.actions.append((step_index, exec_code, status, failure_reason))

    def finalize(self, status=None, failure_reason=None):
        self.finalized_with = (status, failure_reason)
        return {"summary": "fake-summary.json"}


class TestS3CliRecorderIntegration(unittest.TestCase):
    def test_run_agent_records_s3_loop_facts_without_executing_workflow(self):
        from gui_agents.s3 import cli_app

        cli_app.paused = False
        agent = _FakeAgent()
        recorder = _FakeRecorder()

        cli_app.run_agent(
            agent,
            "打开消息并发送 hello",
            scaled_width=800,
            scaled_height=600,
            max_steps=3,
            recorder=recorder,
        )

        self.assertEqual(agent.predictions, 1)
        self.assertEqual(recorder.started_with, "打开消息并发送 hello")
        self.assertEqual(len(recorder.observations), 1)
        self.assertEqual(recorder.observations[0][0], 1)
        self.assertEqual(recorder.observations[0][1]["image_width"], 800)
        self.assertEqual(
            recorder.actions,
            [(1, "agent.done()", "done", None)],
        )
        self.assertEqual(recorder.finalized_with, ("completed", None))


if __name__ == "__main__":
    unittest.main()
