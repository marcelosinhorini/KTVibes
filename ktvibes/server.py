"""Uvicorn shutdown with a last resort for stuck connections or worker threads."""
import os
import signal
import sys
import threading

import uvicorn


GRACEFUL_TIMEOUT = 5
SHUTDOWN_DEADLINE = 15


def force_exit():
    # The queue is saved as it changes, not at shutdown. Don't wait indefinitely for
    # a stuck socket, executor thread, or subprocess after the shutdown deadline.
    print("Forcing KTVibes to exit. Saved queue data is retained.", file=sys.stderr, flush=True)
    os._exit(1)


class Server(uvicorn.Server):
    def __init__(self, config):
        super().__init__(config)
        self._shutdown_timer = None

    def handle_exit(self, sig, frame):
        if self._shutdown_timer is None:
            self._shutdown_timer = threading.Timer(SHUTDOWN_DEADLINE, force_exit)
            self._shutdown_timer.daemon = True
            self._shutdown_timer.start()
            print("Stopping KTVibes; press Ctrl+C again to force exit.", file=sys.stderr, flush=True)
        elif sig == signal.SIGINT:
            force_exit()
            return
        super().handle_exit(sig, frame)

    def run(self, *args, **kwargs):
        try:
            return super().run(*args, **kwargs)
        except KeyboardInterrupt:
            # Uvicorn re-raises Ctrl+C after completing its shutdown.
            pass
        finally:
            if self._shutdown_timer is not None:
                self._shutdown_timer.cancel()


def run(app, port):
    config = uvicorn.Config(app, host="0.0.0.0", port=port, timeout_graceful_shutdown=GRACEFUL_TIMEOUT)
    Server(config).run()
