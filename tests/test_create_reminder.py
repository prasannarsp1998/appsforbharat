import unittest
from unittest.mock import MagicMock, patch

from services.reminder import create_reminder


class TestCreateReminder(unittest.TestCase):
    @patch("services.startup.mysql.connector.connect")
    def test_create_reminder_success(self, mock_connect):
        event = {"reminder_data": "Schedule a meet with Guru on 2024-04-22"}
        user_email = "test@example.com"

        mock_cursor = MagicMock()
        mock_connect.return_value = MagicMock(
            cursor=MagicMock(return_value=mock_cursor)
        )

        response, status_code = create_reminder(event, user_email)

        mock_cursor.execute.assert_called_once()

        self.assertEqual(status_code, 201)
        self.assertEqual(response["response"], "success")

    @patch("services.startup.mysql.connector.connect")
    def test_create_reminder_success_different_format(self, mock_connect):
        event = {
            "reminder_data": "Complete WebCheck In for Hyderabad trip on 22-Apr-2024"
        }
        user_email = "test@example.com"

        mock_cursor = MagicMock()
        mock_connect.return_value = MagicMock(
            cursor=MagicMock(return_value=mock_cursor)
        )

        response, status_code = create_reminder(event, user_email)

        mock_cursor.execute.assert_called_once()

        self.assertEqual(status_code, 201)
        self.assertEqual(response["response"], "success")

    @patch("services.startup.mysql.connector.connect")
    def test_create_reminder_failure_invalid_date(self, mock_connect):
        event = {"reminder_data": "Complete WebCheck In for Delhi trip on 31-31-20241"}
        user_email = "test@example.com"

        mock_cursor = MagicMock()
        mock_connect.return_value = MagicMock(
            cursor=MagicMock(return_value=mock_cursor)
        )

        response, status_code = create_reminder(event, user_email)
        print(response, status_code)

        self.assertEqual(status_code, 400)
        self.assertEqual(response["message"], "Invalid Date")


if __name__ == "__main__":
    unittest.main()
