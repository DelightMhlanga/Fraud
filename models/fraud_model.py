def is_fraudulent(transaction):
    amount = transaction.get('amount', 0)
    location = transaction.get('location', '')
    user_id = transaction.get('user_id', '')

    # Basic rule-based logic
    if amount > 1000:
        return True, "High-value transaction flagged"
    if location.lower() in ['russia', 'north korea', 'unknown']:
        return True, "Suspicious location detected"
    if user_id.startswith('test') or user_id == '':
        return True, "Invalid or test user ID"

    return False, "Transaction appears normal"