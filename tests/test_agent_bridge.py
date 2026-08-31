import sys
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deepskin_agent.client import (
    AgentDispatcher, AgentResult, extract_agent_text, gesture_prompt, im_frontend_url,
    parse_sse_lines,
)


class AgentBridgeTests(unittest.TestCase):
    def test_parses_multiline_done_event(self):
        done = parse_sse_lines([
            b"event: chunk\n", b'data: {"delta":"ok"}\n', b"\n",
            b"event: done\n", b'data: {"text":"hello",\n',
            b'data: "data":{"value":{"Mood":1,"Favor":2,"Egy":-1}}}\n', b"\n",
        ])
        self.assertEqual(done["text"], "hello")
        self.assertEqual(done["data"]["value"]["Favor"], 2)

    def test_all_formal_labels_have_social_prompts(self):
        for label in ("STATIC_TOUCH", "STROKE", "RUB", "TAP", "POKE", "PAT", "IMPACT"):
            self.assertIn("用户", gesture_prompt(label))

    def test_builds_im_page_from_frontend_root_or_existing_route(self):
        expected = "http://192.168.100.110:5175/im/session-1"
        self.assertEqual(im_frontend_url("http://192.168.100.110:5175/", "session-1"), expected)
        self.assertEqual(im_frontend_url("http://192.168.100.110:5175/s/old", "session-1"), expected)

    def test_prefers_structured_message_text_over_serialized_done_text(self):
        done = {
            "text": '{"messages":[{"type":"text","text":"fallback"}]}',
            "data": {"messages": [{"type": "text", "text": "第一句"},
                                    {"type": "text", "text": "第二句"}]},
        }
        self.assertEqual(extract_agent_text(done), "第一句\n第二句")

    def test_dispatcher_coalesces_pending_actions_and_updates_status(self):
        sent = []
        first_started = threading.Event()
        release_first = threading.Event()
        done = threading.Event()

        def fake_send(**kwargs):
            sent.append((kwargs["label"], dict(kwargs["status"])))
            if len(sent) == 1:
                first_started.set()
                release_first.wait(1.0)
            return AgentResult(kwargs["label"], "ok", {"Mood": len(sent), "Favor": 0, "Egy": -1}, {})

        updates = []
        dispatcher = AgentDispatcher(
            url="http://example.test", user_id="test-user", session_id="session",
            min_interval_s=0.0, send=fake_send,
            on_update=lambda kind, payload: (updates.append((kind, payload)),
                                             done.set() if kind == "done" and len(sent) == 2 else None),
        )
        dispatcher.start()
        dispatcher.submit("TAP")
        self.assertTrue(first_started.wait(1.0))
        dispatcher.submit("POKE")
        dispatcher.submit("PAT")
        release_first.set()
        self.assertTrue(done.wait(1.0))
        dispatcher.close()
        self.assertEqual([item[0] for item in sent], ["TAP", "PAT"])
        self.assertEqual(sent[1][1]["Mood"], 1)

    def test_dispatcher_enforces_minimum_start_interval(self):
        starts = []
        completed = threading.Event()

        def fake_send(**kwargs):
            starts.append(time.monotonic())
            return AgentResult(kwargs["label"], "ok", kwargs["status"], {})

        dispatcher = AgentDispatcher(
            url="http://example.test", user_id="test-user", session_id="session",
            min_interval_s=0.05, send=fake_send,
            on_update=lambda kind, _payload: completed.set() if kind == "done" and len(starts) == 2 else None,
        )
        dispatcher.start()
        dispatcher.submit("TAP")
        while len(starts) < 1:
            time.sleep(0.001)
        dispatcher.submit("POKE")
        self.assertTrue(completed.wait(1.0))
        dispatcher.close()
        self.assertGreaterEqual(starts[1] - starts[0], 0.045)


if __name__ == "__main__":
    unittest.main()
