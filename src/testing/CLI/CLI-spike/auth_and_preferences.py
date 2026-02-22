from typing import Any

class User:
    """
    Docstring for user
    
    Initialize:
        username
        password

    Set a dictionary of:
        preferences: predefined key value pairs, no adding more but we can update the values of the keys
    """
    def __init__(self, username=None, password=None, preferences=None):
        self.username = username or ""
        self.password = password or ""
        self.preferences = preferences or {}

    # Can update preferences
    def update_preference(self, preference: str, value: Any) -> None:
        self.preferences.update(preference=value)

    def add_preference(self, preference: str, value: Any) -> None:
        if type(self.preferences[preference]) is set:
            # E.g. genres
            # Update preference with 
            self.preferences[preference].add(value)
        else:
            self.preferences.update(preference=value)

    def delete_preference(self, preference: str, value: Any) -> None:
        if type(self.preferences[preference]) is set:
            # E.g. genres
            # Update preference with 
            if value not in self.preferences[preference]:
                return
            self.preferences[preference].remove(value)
        else:
            self.preferences.update(preference=value)


def validate_credentials(username: str, password: str) -> User | None:
    for user in VALID_USERS:
        if user.username == username and user.password == password:
            return user
    return None


VALID_USERS = [
    User("test", "1234", {
        "genre": set(),
        "release_range": (),
        "number_of_players": None,
        "length": None,
    })
]