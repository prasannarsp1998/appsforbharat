import unittest
from unittest.mock import MagicMock, patch
from services.reminder import fetch_reminders
import json


class TestCreateReminder(unittest.TestCase):
    @patch("services.startup.redis.StrictRedis")
    @patch("services.startup.mysql.connector.connect")
    def test_fetch_reminders_cache_hit(self, mock_mysql_connect, mock_redis):
        # Mocking redis connection and cache data
        mock_redis_conn = MagicMock()
        mock_redis_conn.get.return_value = json.dumps(
            [
                {
                    "date": "2024-04-21",
                    "datetime": {
                        "createdAt": "2024-04-21 16:08:36",
                        "deletedAt": None,
                        "emailedAt": "2024-04-21 16:11:47",
                        "triggeredAt": "2024-04-21 16:11:46",
                    },
                    "id": 1,
                    "message": "Buy groceries",
                    "status": "sent",
                    "user": "prasannascorpian@gmail.com",
                }
            ]
        ).encode("utf-8")
        mock_redis.return_value = mock_redis_conn

        # Mocking mysql connection and query execution
        mock_mycursor = MagicMock()
        mock_mycursor.fetchall.return_value = [{"id": 1, "title": "Reminder 1"}]
        mock_mysql_connect.return_value.cursor.return_value = mock_mycursor

        # Call the function
        result, status_code = fetch_reminders(1, 10, "active", "user@example.com")

        # Assertions
        self.assertEqual(status_code, 200)
        mock_redis_conn.get.assert_called_once_with("cached_data:user@example.com:1:10")
        mock_mysql_connect.assert_not_called()  # MySQL connection should not be called due to cache hit

    @patch("services.startup.redis.StrictRedis")
    @patch("services.startup.mysql.connector.connect")
    def test_fetch_reminders_failed(self, mock_mysql_connect, mock_redis):
        # Mocking redis connection and cache data
        mock_redis_conn = MagicMock()
        mock_redis_conn.get.return_value = json.dumps(
            [
                {
                    "date": "2024-04-21",
                    "datetime": {
                        "createdAt": "2024-04-21 16:08:36",
                        "deletedAt": None,
                        "emailedAt": "2024-04-21 16:11:47",
                        "triggeredAt": "2024-04-21 16:11:46",
                    },
                    "id": 1,
                    "message": "Buy groceries",
                    "status": "sent",
                    "user": "prasannascorpian@gmail.com",
                }
            ]
        ).encode("utf-8")
        mock_redis.side_affect = Exception("Redis connection failed")

        # Mocking mysql connection and query execution
        mock_mycursor = MagicMock()
        mock_mycursor.fetchall.return_value = [{"id": 1, "title": "Reminder 1"}]
        mock_mysql_connect.return_value.cursor.return_value = mock_mycursor

        # Call the function
        result, status_code = fetch_reminders(1, 10, "active", "user@example.com")

        # Assertions
        self.assertEqual(status_code, 500)

    @patch("services.startup.redis.StrictRedis")
    @patch("services.startup.mysql.connector.connect")
    def test_fetch_reminders_mysql_hit(self, mock_mysql_connect, mock_redis):
        # Mocking redis connection and cache data
        mock_redis_conn = MagicMock()
        mock_redis_conn.get.return_value = None
        mock_redis.return_value = mock_redis_conn

        # Mocking mysql connection and query execution
        mock_mycursor = MagicMock()
        mock_mycursor.fetchall.return_value = [
            {
                "date": "2024-04-21",
                "datetime": json.dumps(
                    {
                        "createdAt": "2024-04-21 16:08:36",
                        "deletedAt": None,
                        "emailedAt": "2024-04-21 16:11:47",
                        "triggeredAt": "2024-04-21 16:11:46",
                    }
                ),
                "id": 1,
                "message": "Buy groceries",
                "status": "sent",
                "user": "user@example.com",
            }
        ]

        mock_mysql_connect.return_value.cursor.return_value = mock_mycursor

        # Call the function
        result, status_code = fetch_reminders(1, 10, "active", "user@example.com")

        # Assertions
        self.assertEqual(status_code, 200)
        mock_redis_conn.get.assert_called_once_with("cached_data:user@example.com:1:10")
        mock_mysql_connect.assert_called_once()  # MySQL connection should not be called due to cache hit


if __name__ == "__main__":
    unittest.main()
