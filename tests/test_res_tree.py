"""Regression tests for the ResTree widget."""

import os
import tempfile
import unittest
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication
except ImportError as exc:  # pragma: no cover - platform-specific dependency
    QApplication = None
    _QT_IMPORT_ERROR = exc
    cyno_exporter = None
else:
    _QT_IMPORT_ERROR = None
    import cyno_exporter

    _APP = QApplication.instance() or QApplication([])


class _DummyLogger:
    def __init__(self):
        self.messages = []

    def add(self, message):
        self.messages.append(message)


class _DummyAction:
    def __init__(self):
        self.enabled_states = []

    def setEnabled(self, state):
        self.enabled_states.append(state)


if cyno_exporter is None:

    class ResTreeRemoteResindexFailureTest(unittest.TestCase):
        @unittest.skip(f"PyQt6 is unavailable: {_QT_IMPORT_ERROR}")
        def test_fetch_resindex_none_is_handled(self):
            pass

else:

    class ResTreeRemoteResindexFailureTest(unittest.TestCase):
        def setUp(self):
            self.tempdir = tempfile.TemporaryDirectory()
            self.addCleanup(self.tempdir.cleanup)

            self.config_patch = patch(
                "cyno_exporter.CONFIG_FILE",
                os.path.join(self.tempdir.name, "config.json"),
            )
            self.config_patch.start()
            self.addCleanup(self.config_patch.stop)

            self.logger = _DummyLogger()
            self.shared_action = _DummyAction()
            self.tree = cyno_exporter.ResTree(
                client="dummy_client",
                event_logger=self.logger,
                shared_cache=self.shared_action,
            )

        def test_fetch_resindex_none_is_handled(self):
            with patch.object(
                cyno_exporter.ResFileIndex, "fetch_client", return_value=12345
            ), patch.object(
                cyno_exporter.ResFileIndex, "fetch_resindexfile", return_value=None
            ), patch.object(
                cyno_exporter.QMessageBox, "warning"
            ) as mock_warning:
                self.tree.load_resfiles(self.tree, self.tree.client)

            self.assertEqual(self.tree.topLevelItemCount(), 1)
            self.assertFalse(self.tree.topLevelItem(0).isHidden())
            self.assertIn(False, self.shared_action.enabled_states)
            self.assertIn(True, self.shared_action.enabled_states)
            self.assertTrue(
                any(
                    "Could not download the remote resfile index" in msg
                    for msg in self.logger.messages
                )
            )
            mock_warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()

