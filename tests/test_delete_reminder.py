import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from services.reminder import delete_reminder


class TestCreateReminder(unittest.TestCase):
    @patch("services.startup.mysql.connector.connect")
    def test_delete_reminder_success(self, mock_connect):
        user_email = "test@example.com"

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "status": "created",
            "id": 1,
            "user": "test@example.com",
        }
        mock_connect.return_value = MagicMock(
            cursor=MagicMock(return_value=mock_cursor)
        )

        response, status_code = delete_reminder(user_email, reminder_id=1)

        self.assertEqual(mock_cursor.execute.call_count, 2)

        self.assertEqual(status_code, 204)

    @patch("services.startup.mysql.connector.connect")
    def test_delete_reminder_not_found(self, mock_connect):
        user_email = "test@example.com"

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connect.return_value = MagicMock(
            cursor=MagicMock(return_value=mock_cursor)
        )

        response, status_code = delete_reminder(user_email, reminder_id=10000)

        mock_cursor.execute.assert_called_once()

        self.assertEqual(status_code, 404)
        self.assertEqual(response["message"], "Reminder not found")

    @patch("services.startup.mysql.connector.connect")
    def test_delete_reminder_unauthorized(self, mock_connect):
        user_email = "test@example.com"

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "status": "created",
            "id": 1,
            "user": "test123@example.com",
        }
        mock_connect.return_value = MagicMock(
            cursor=MagicMock(return_value=mock_cursor)
        )

        response, status_code = delete_reminder(user_email, reminder_id=1)

        mock_cursor.execute.assert_called_once()

        self.assertEqual(status_code, 401)
        self.assertEqual(response["message"], "Unauthorized")

    @patch("services.startup.mysql.connector.connect")
    def test_delete_reminder_invalid_status(self, mock_connect):
        user_email = "test@example.com"

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "status": "emailed",
            "id": 1,
            "user": "test@example.com",
        }
        mock_connect.return_value = MagicMock(
            cursor=MagicMock(return_value=mock_cursor)
        )

        response, status_code = delete_reminder(user_email, reminder_id=1)

        mock_cursor.execute.assert_called_once()

        self.assertEqual(status_code, 400)
        self.assertEqual(
            response["message"], "Cannot delete already executed/deleted item"
        )


if __name__ == "__main__":
    unittest.main()
