class User:
    def __init__(self, user_dict):
        self.email = user_dict['email']
        self.userId = user_dict['userId']
        self.conversations = user_dict['conversations']
        self.created_topics = user_dict['created_topics']

    @property
    def is_active(self):
        # All users are considered active in this example
        return True

    @property
    def is_authenticated(self):
        # All users are considered authenticated in this example
        return True

    @property
    def is_anonymous(self):
        # We don't have anonymous users in this example
        return False

    def get_id(self):
        return self.userId
