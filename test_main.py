import unittest
import os

# Set test database URL before importing main
# Use a file-based SQLite database for testing to ensure proper connection sharing
test_db_path = os.path.join(os.path.dirname(__file__), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

# Import the app and models after setting up test database
from main import (
    is_phone_number_valid,
)


# ==================== Validation Function Tests ====================

class TestPhoneNumberValidation(unittest.TestCase):
    def test_valid_phone_number(self):
        assert is_phone_number_valid("1234567890") == True
        assert is_phone_number_valid("9876543210") == True
    
    def test_invalid_phone_number(self):
        assert is_phone_number_valid("123456789") == False  # Too short
        assert is_phone_number_valid("12345678901") == False  # Too long
        assert is_phone_number_valid("123-456-7890") == False  # Contains dashes
        assert is_phone_number_valid("(123)456-7890") == False  # Contains parentheses
        assert is_phone_number_valid("abc1234567") == False  # Contains letters
        assert is_phone_number_valid("") == False
        assert is_phone_number_valid("12345") == False

if __name__ == "__main__":
    unittest.main()

