class SessionManager:
    def __init__(self):
        self.mode = None        # "user" o "admin"
        self.username = None

    def set_user_mode(self, username="guest"):
        self.mode = "user"
        self.username = username

    def set_admin_mode(self, username="admin"):
        self.mode = "admin"
        self.username = username

    def is_user(self):
        return self.mode == "user"

    def is_admin(self):
        return self.mode == "admin"
