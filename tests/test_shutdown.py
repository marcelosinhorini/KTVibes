"""Shutdown watchdog and Uvicorn configuration regression checks."""
import importlib.util
import signal
import unittest
from unittest.mock import Mock, patch


@unittest.skipUnless(importlib.util.find_spec("uvicorn"), "Run uv sync to install dependencies")
class ShutdownTests(unittest.TestCase):
    def test_force_exit_does_not_return(self):
        from ktvibes import server
        with patch.object(server.os, "_exit") as exit_process:
            server.force_exit()
        exit_process.assert_called_once_with(1)

    def test_server_configures_graceful_timeout(self):
        from ktvibes import server
        app = object()
        with patch.object(server, "Server") as cls:
            server.run(app, 8765)
        config = cls.call_args.args[0]
        self.assertIs(config.app, app)
        self.assertEqual(config.timeout_graceful_shutdown, server.GRACEFUL_TIMEOUT)
        cls.return_value.run.assert_called_once_with()

    def test_first_interrupt_arms_watchdog_second_forces_exit(self):
        from ktvibes import server
        instance = server.Server(server.uvicorn.Config(lambda *args: None))
        with patch.object(server.threading, "Timer") as timer, patch.object(server, "force_exit") as force:
            instance.handle_exit(signal.SIGINT, None)
            timer.assert_called_once_with(server.SHUTDOWN_DEADLINE, server.force_exit)
            self.assertTrue(timer.return_value.daemon)
            timer.return_value.start.assert_called_once_with()
            self.assertTrue(instance.should_exit)
            instance.handle_exit(signal.SIGINT, None)
            force.assert_called_once_with()

    def test_watchdog_cancelled_after_server_returns_or_raises(self):
        from ktvibes import server
        for error in (None, RuntimeError("failed")):
            instance = server.Server(server.uvicorn.Config(lambda *args: None))
            timer = instance._shutdown_timer = Mock()
            with patch.object(server.uvicorn.Server, "run", side_effect=error):
                if error:
                    with self.assertRaises(RuntimeError):
                        instance.run()
                else:
                    instance.run()
            timer.cancel.assert_called_once_with()

    def test_keyboard_interrupt_exits_without_traceback(self):
        from ktvibes import server
        instance = server.Server(server.uvicorn.Config(lambda *args: None))
        timer = instance._shutdown_timer = Mock()
        with patch.object(server.uvicorn.Server, "run", side_effect=KeyboardInterrupt):
            instance.run()
        timer.cancel.assert_called_once_with()
