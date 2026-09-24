import queue
import threading
import traceback


class BackgroundPublish:
    """Roda PublishService.publish numa thread e entrega eventos para a interface consultar (o Tk não aceita outra thread)."""

    def __init__(self, publish_service):
        self.publish_service = publish_service
        self.events = queue.Queue()
        self._cancel = threading.Event()
        self._thread = None

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running:
            return
        self._cancel.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self):
        self._cancel.set()

    def poll(self):
        events = []
        while True:
            try:
                events.append(self.events.get_nowait())
            except queue.Empty:
                return events

    def _run(self):
        try:
            result = self.publish_service.publish(
                progress=lambda done, total, message: self.events.put(("progress", done, total, message)),
                cancel=self._cancel.is_set,
            )
        except Exception as error:
            self.events.put(("error", f"{error}", traceback.format_exc()))
            return
        self.events.put(("done", result))
