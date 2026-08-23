def get_user_balance(account_id):
    query = "SELECT balance FROM accounts WHERE id = %s"
    return db.execute(query, (account_id,))