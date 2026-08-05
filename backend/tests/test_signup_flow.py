import unittest
from unittest import mock

from backend.registration import signup_flow


class SignupFlowTests(unittest.TestCase):
    class NativeInput:
        def __init__(self, current_value=""):
            self.current_value = current_value
            self.states = mock.Mock(is_alive=True, is_displayed=True, is_enabled=True)

        def click(self, **kwargs):
            return None

        def input(self, value, **kwargs):
            return None

        def property(self, name):
            return self.current_value

    def test_native_input_does_not_treat_empty_value_as_success(self):
        element = self.NativeInput(current_value="")
        self.assertFalse(signup_flow._native_type_element(element, "Neo"))

    def test_native_input_accepts_confirmed_value(self):
        element = self.NativeInput(current_value="Neo")
        self.assertTrue(signup_flow._native_type_element(element, "Neo"))

    def test_code_submission_accepts_native_button_label(self):
        logs = []
        page = mock.Mock()
        with mock.patch.dict(
            signup_flow._deps,
            {"get_oai_code": mock.Mock(return_value="123456")},
        ), mock.patch.object(
            signup_flow, "_native_fill_code", return_value="filled-aggregate"
        ), mock.patch.object(
            signup_flow, "_native_click_action", return_value="Continue"
        ), mock.patch.object(
            signup_flow, "sleep_with_cancel"
        ), mock.patch.object(signup_flow, "page", page):
            result = signup_flow.fill_code_and_submit(
                "fixture@example.com",
                "fixture-token",
                timeout=1,
                log_callback=logs.append,
            )

        self.assertEqual(result, "123456")
        self.assertFalse(page.run_js.called)
        self.assertTrue(any("Continue" in message for message in logs))


if __name__ == "__main__":
    unittest.main()
