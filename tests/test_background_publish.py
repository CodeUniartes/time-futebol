import threading
import time

from src.services.background_publish import BackgroundPublish


class FakeService:
    def __init__(self, steps=3, fail=False, wait_for_cancel=False):
        self.steps = steps
        self.fail = fail
        self.wait_for_cancel = wait_for_cancel
        self.started = threading.Event()

    def publish(self, progress=None, cancel=None):
        self.started.set()
        if self.fail:
            raise RuntimeError("falhou")
        for step in range(1, self.steps + 1):
            if self.wait_for_cancel:
                while not cancel():
                    time.sleep(0.005)
                return "cancelado"
            progress(step, self.steps, f"arquivo {step}")
        return "resultado"


def wait_until_finished(runner, timeout=3):
    events = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        events += runner.poll()
        if any(event[0] in ("done", "error") for event in events):
            return events
        time.sleep(0.005)
    raise AssertionError("a publicação não terminou")


def test_reports_progress_then_done():
    runner = BackgroundPublish(FakeService())
    runner.start()
    events = wait_until_finished(runner)
    assert [event[:3] for event in events if event[0] == "progress"] == [
        ("progress", 1, 3),
        ("progress", 2, 3),
        ("progress", 3, 3),
    ]
    assert events[-1] == ("done", "resultado")


def test_error_becomes_an_event_instead_of_crashing_the_thread():
    runner = BackgroundPublish(FakeService(fail=True))
    runner.start()
    events = wait_until_finished(runner)
    assert events[-1][0] == "error"
    assert events[-1][1] == "falhou"


def test_cancel_reaches_the_service():
    service = FakeService(wait_for_cancel=True)
    runner = BackgroundPublish(service)
    runner.start()
    assert service.started.wait(2)
    assert runner.running
    runner.cancel()
    events = wait_until_finished(runner)
    assert events[-1] == ("done", "cancelado")


def test_start_while_running_does_not_start_twice():
    service = FakeService(wait_for_cancel=True)
    runner = BackgroundPublish(service)
    runner.start()
    assert service.started.wait(2)
    runner.start()
    runner.cancel()
    events = wait_until_finished(runner)
    assert [event[0] for event in events].count("done") == 1


def test_poll_without_events_returns_empty_list():
    assert BackgroundPublish(FakeService()).poll() == []
