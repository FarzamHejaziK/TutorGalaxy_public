from config import user_table

def update_schema_for_all_users():
    # Scan to retrieve all users from the user_table
    response = user_table.scan()
    all_users = response['Items']

    for user in all_users:
        # Update the fields for the user as per the new schema
        user['given_name'] = user.get('given_name', '')  # or some default value
        user['family_name'] = user.get('family_name', '') # or some default value
        user['photo'] = user.get('photo', '')  # or some default value
        
        # Check if 'conversations' and 'created_topics' are present in the existing user
        # If not, initialize them with empty lists
        user.setdefault('conversations', [])
        user.setdefault('created_topics', [])

        # Update the active checkout session
        user['active_checkout_session'] = {
            'session_id': None,
            'timestamp': None
        }

        # Set subscribed state to True
        user['subscribed'] = {
            'state': True,
            'id': None,
            'stripe_id': None
        }

        # Update the user in the user_table
        user_table.put_item(Item=user)

if __name__ == "__main__":
    update_schema_for_all_users()