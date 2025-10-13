import json

# --- Fraud detection logic (copied directly instead of importing) ---
def is_fraudulent(transaction):
    amount = transaction.get('amount', 0)
    location = transaction.get('location', '')
    user_id = transaction.get('user_id', '')

    if amount > 1000:
        return True, "High-value transaction flagged"
    if location.lower() in ['russia', 'north korea', 'unknown']:
        return True, "Suspicious location detected"
    if user_id.startswith('test') or user_id == '':
        return True, "Invalid or test user ID"

    return False, "Transaction appears normal"

# --- Load sample transactions from ../data/transactions.json ---
with open('../data/transactions.json', 'r') as f:
    transactions = json.load(f)

# --- Evaluate each transaction ---
for tx in transactions:
    fraud, message = is_fraudulent(tx)
    print(f"User: {tx['user_id']}, Amount: {tx['amount']}, Location: {tx['location']}")
    print(f"→ Fraud: {fraud}, Reason: {message}\n")