"""User interface for IPC-Hermes 9852 test system."""

import logging
from threading import Thread

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.treeview import TreeViewLabel

from mgr.hermes_test_manager import hermes_test_api # pylint: disable=import-error

class Hitmanager(Widget):
    """Main widget for HitManager. So far just one window
       and MVC pattern is not used.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._log = logging.getLogger('hitmanager')

        tree = self.ids.testlist_tv
        root = tree.root
        for test_name in hermes_test_api.available_tests():
            child_node = TreeViewLabel(text=test_name, is_leaf=True)
            tree.add_node(child_node, root)
        self._reset_ui()

    def treeview_touch_down(self):
        """Treeview touch down event handler
           resets ui and highlight selection but don't run test.
        """
        self._reset_ui()

    def run_selected_tests(self) -> None:
        """Button press event handler to run selected tests."""
        self._log.debug('button: run selected tests')
        selected_test = self.ids.testlist_tv.selected_node.text
        self._running_ui()
        thread = Thread(target=self._run_selected_test, args=(selected_test,))
        thread.start()

    def user_confirm(self, val: bool):
        """Button press event handler for user confirmation."""
        self.ids.instruction_label.text = 'Pressed: ' + str(val)

    def test_callback(self, *args, **kwargs):
        """Hermes test API callback function."""
        # at the moment the callback is called with 3 arguments (will change!)
        # arg0 : test name
        # arg1 : instruction
        # msg : waiting for Hermes message tag
        instruction = args[1]
        self.ids.instruction_label.text = instruction

    def _run_selected_test(self, selected_test):
        self._update_current_test_label(selected_test)
        result = hermes_test_api.run_test(selected_test, self.test_callback)
        if result:
            self.ids.current_test_label.background_color = (0, 1, 0, 1)
        else:
            self.ids.current_test_label.background_color = (1, 0, 0, 1)

    def _update_current_test_label(self, test_name):
        self.ids.current_test_label.text = test_name
        self.ids.current_test_label.background_color = (0.5, 0.5, 0.5, 1)

    def _reset_ui(self):
        """Reset user interface between tests."""
        self._update_current_test_label('')
        self.ids.instruction_label.text = ''

    def _running_ui(self):
        """Reset user interface between tests."""


class HitmanagerApp(App):
    """Main application class for HitManager."""

    title = 'IPC-9852 Hermes interface tester'

    def build(self):
        return Hitmanager()


if __name__ == '__main__':
    HitmanagerApp().run()