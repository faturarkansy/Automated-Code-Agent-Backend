from unittest.mock import MagicMock

def test_get_user_balance_parameterized():
    mock_db = MagicMock()
    account_id = 123
    query = "SELECT balance FROM accounts WHERE id = %s"
    mock_db.execute(query, (account_id,))
    mock_db.execute.assert_called_once_with(query, (account_id,))