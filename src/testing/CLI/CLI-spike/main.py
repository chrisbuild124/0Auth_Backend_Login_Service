"""
Docstring for textual.main

Defines the main program implementation (Sprint 1)

Classes are screens which are popped and pushed off the view stack
"""

from dataclasses import dataclass

from time import sleep

from textual.app import App, ComposeResult
from textual.widgets import Header, Input, RichLog
from textual.screen import Screen
from textual.reactive import reactive

from auth_and_preferences import User, validate_credentials, VALID_USERS
import preference_options


class AuthState:

    def __init__(self):
        self.username = ""
        self.user = User()


class BaseCLIScreen(Screen):
    """
    Base screen which is the parent of every other screen.
    Includes widgets:
      Header, unnamed
      RichLog, "log"
      Input, "cmd"
      
    CLI-style
    """

    def compose(self) -> ComposeResult:
        # Initializes widgets for the basic screen
        yield Header()
        yield RichLog(id="log")
        yield Input(id="cmd")

    def on_mount(self) -> None:
        # Focuses on the input box and makes header invisible when the screen is initialized
        self.query_one("#cmd", Input).focus()
        self.query_one("HeaderIcon").visible = False

    def _log(self, text: str) -> None:
        # Writes a text string to the RichLog widget on the screen
        self.query_one("#log", RichLog).write(text)

    def clear_input(self) -> None:
        # Clears the text in the Input widget
        self.query_one("#cmd", Input).value = ""

    def get_app(self) -> "GameRecommenderApp":
       # Grabs the application so the screen can interface with it
       return self.app # type: ignore[return-value]


class LoginScreen(BaseCLIScreen):
    """Login screen with username and password prompt."""

    # Username step and password step to facilitate collecting each from the user
    step: reactive[str] = reactive("username") # username -> password

    def on_mount(self) -> None:
        super().on_mount()
        app = self.get_app()
        self._log(f"Welcome to {app.TITLE}!")
        self._log("Recommends games based on user preferences.\n")
        self._log("Log in with your credentials to begin.")
        self._log("Submit with Enter.\n")
        self._switch_to_username_mode()

    # What user interacts with to enter their username
    def _switch_to_username_mode(self) -> None:
        self.step = "username"
        inp = self.query_one("#cmd", Input)
        inp.password = False
        inp.placeholder = "Enter Username: "
        self.clear_input()

    # What user interacts with to enter their password
    def _switch_to_password_mode(self) -> None:
        self.step = "password"
        inp = self.query_one("#cmd", Input)
        inp.password = True
        inp.placeholder = "Enter Password: "
        self.clear_input()

    # Called when user presses enter with textbox highlighted
    def on_input_submitted(self, event: Input.Submitted) -> None:
        app = self.get_app()
        inp = event.input # What the user inputted
        raw = inp.value.strip()

        if self.step == "username":
            if not raw: # If there's no input, do nothing
                inp.focus()
                return
            app.auth.username = raw # Saves attempted username
            self._log(f"Attempting to login as {app.auth.username}...")
            self._switch_to_password_mode()

        elif self.step == "password":
            if not raw: # If there's no input, do nothing
                inp.focus()
                return
            
            validated_user = validate_credentials(app.auth.username, raw)

            if validated_user:
                app.auth.user = validated_user
                app.pop_screen()
                app.push_screen(HomeScreen())
            else:
                self._log("Authentication failed, try again.")
                app.auth = AuthState()
                self._switch_to_username_mode()
            

class HomeScreen(BaseCLIScreen):
    """Home screen with command implementation, traverse to different views"""
    def on_mount(self) -> None:
        super().on_mount()
        app = self.get_app()
        self._log(f"{app.auth.username} welcome to Game Recommender!")
        self._log("Here you can generate your recommendations or view/edit preferences.")
        self._log("Type 'help' to see commands.\n")
        self._log("Your changes are associated with your user if you quit the app.\n")
        self._log("If you're a new user, type the 'quick start' command to have\ninstructions you can follow for preference setup and a generation\nprinted on the screen!")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        self.clear_input()
        if not raw:
            return
        
        cmd, *args = raw.split()
        await self._handle_commands(cmd, args)
        
    async def _handle_commands(self, cmd: str, args: list[str]) -> None:
        """Handles commands associated with the screen"""
        app = self.get_app()

        match cmd.lower():
            case "help":
                self.print_help_message()
            case "logout":
                app.auth = AuthState()
                app.pop_screen()
                app.push_screen(LoginScreen())
            case "exit":
                await app.action_quit()
            case "view":
                if args[0] == "preferences":
                    app.push_screen(ViewPreferences())
                else:
                    self._log("Second word in input is invalid.")
            case "edit":
                if args[0] == "preferences":
                    app.push_screen(EditPreferences())
                else:
                    self._log("Second word in input is invalid.")
            case "quick":
                if len(args) != 1:
                    self._log("Too many arguments.")
                if args[0] == "start":
                    self.print_quick_start_message()
                else:
                    self._log("Second word in input is invalid.")
            case _:
                self._log("Unrecognized input.")

    def print_help_message(self) -> None:
        # Print help message associated with each command associated with screen
        self._log("\nhelp - Shows a list of commands with usage information")
        self._log("logout - Log out of current user (returns to login screen)")
        self._log("exit - Quits the application")
        self._log("view preferences - Shows a screen with a list of current user's preferences")
        self._log("edit preferences - Shows a screen with a list of current user's preferences and shows how to edit them")
        self._log("quick start - Shows a basic guide for how to use this application")

    def print_quick_start_message(self) -> None:
        self._log("\nSince you're logged in, head to edit preferences!")
        self._log("From there, edit whichever preference you want the recommender to consider.")
        self._log("Once the preferences are to your liking, return home and run 'recommend games'\nto receive your recommendations!")


class ViewPreferences(BaseCLIScreen):
    """Screen where user views the preferences associated with their account"""
    def on_mount(self) -> None:
        app = self.get_app()
        self._log(f"Viewing preferences of {app.auth.username}")
        self._log(f"Preferences determine how the recommender decides what to recommend.")
        self._log("Type 'exit' to return to the home screen or 'edit preferences'\nto jump to that screen immediately.\n")
        
        self.print_user_preferences()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        self.clear_input()
        if not raw:
            return
        
        cmd, *args = raw.split()
        self._handle_commands(cmd, args)
    
    def _handle_commands(self, cmd: str, args: list[str]) -> None:
        # return await super()._handle_commands(cmd, args)
        app = self.get_app()

        match cmd.lower():
            case "exit":
                app.pop_screen()
            case "edit":
                if len(args) != 1:
                    self._log("Too many arguments.")
                elif args[0] == "preferences":
                    app.pop_screen()
                    app.push_screen(EditPreferences())
                else:
                    self._log("Second word in input is invalid.")
            case _:
                self._log("Unrecognized input.")

    def print_user_preferences(self) -> None:
        # Prints preference dictionary associated with user
        prefs = self.get_app().auth.user.preferences
        for preference in prefs.items():
            self._log(preference[0] + ": " + str(preference[1]))


class EditPreferences(BaseCLIScreen):
    """Screen where user edits the preferences associated with their account"""
    def on_mount(self) -> None:
        app = self.get_app()
        self._log(f"Editing preferences of {app.auth.username}")
        self._log("Preferences determine how the recommender decides what to recommend.\n")
        self._log("Type 'edit <preference>' or (e <preference>) followed by the name of the\npreference (e.g. genre) to go to a screen with\noptions to add or remove preferences.")
        self._log("Type 'exit' to return to the home screen.\n")

        self.print_user_preferences()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        self.clear_input()
        if not raw:
            return
        
        cmd, *args = raw.split()
        self._handle_commands(cmd, args)
    
    def _handle_commands(self, cmd: str, args: list[str]) -> None:
        # return await super()._handle_commands(cmd, args)
        app = self.get_app()

        match cmd.lower():
            case "exit":
                app.pop_screen()
            case "edit" | "e":
                if len(args) != 1:
                    self._log("Too many arguments.")
                elif args[0] in ("genre", "genres"):
                    app.pop_screen()
                    app.push_screen(EditPreference("genre"))
                else:
                    self._log("Second word in input is invalid.")
            case _:
                self._log("Unrecognized input.")

    def print_user_preferences(self) -> None:
        # Prints preference dictionary associated with user
        prefs = self.get_app().auth.user.preferences
        for preference in prefs.items():
            self._log(preference[0] + ": " + str(preference[1]))


class EditPreference(BaseCLIScreen):
    """Screen where user edits the genres associated with their account"""
    def __init__(self, preference: str):
        super().__init__()
        self.preference = preference
        self.valid_options = preference_options.get_options(self.preference)

    def on_mount(self) -> None:
        app = self.get_app()
        self._log(f"Editing {self.preference} of {app.auth.username}")
        self._log("Type 'exit' to return to the edit screen or\nadd/delete (a/d) followed by the name of the genre\nto add or remove a particular genre from your preferences.\n")
        self._log("Preferences determine how the recommender\ndecides what to recommend.\n")
        self._log(f"{self.preference.capitalize()} Options: \n")
        self.print_preference_options(self.preference)
        self._log("")
        self.print_user_preference(self.preference)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        self.clear_input()
        if not raw:
            return
        
        cmd, *args = raw.split()
        self._handle_commands(cmd, args)
    
    def _handle_commands(self, cmd: str, args: list[str]) -> None:
        # return await super()._handle_commands(cmd, args)
        app = self.get_app()

        match cmd.lower():
            case "exit":
                app.pop_screen()
                app.push_screen(EditPreferences())
            case "add" | "a":
                if len(args) != 1:
                    self._log("Too many arguments.")
                elif args[0] in self.valid_options:
                    app.auth.user.add_preference(self.preference, args[0])
                    self.print_user_preference(self.preference)
                else:
                    self._log("Invalid genre option.")
            case "delete" | "d":
                if len(args) != 1:
                    self._log("Too many arguments.")
                elif args[0] in self.valid_options:
                    app.auth.user.delete_preference(self.preference, args[0])
                    self.print_user_preference(self.preference)
                else:
                    self._log("Invalid genre option.")
            case _:
                self._log("Unrecognized input.")

    def print_preference_options(self, preference: str):
        # Logs all unique options the preference can be assigned
        for option in preference_options.get_options(preference):
            self._log(option)

    def print_user_preference(self, preference: str):
        preference_value = self.get_app().auth.user.preferences[preference]
        self._log(preference + ": " + str(preference_value))


class GameRecommenderApp(App):
    """Textual app which recommends games and interfaces with microservices"""

    ENABLE_COMMAND_PALETTE = False # Off so user is constricted
    TITLE = "Game Recommender"
    SUB_TITLE = "Get recommendations for games based on your preferences!"

    def __init__(self):
        super().__init__() # Initializes the app
        self.auth = AuthState() # Sets the base authentication state for the app, changes after user login

    def on_mount(self) -> None:
        """Runs when the app is started."""
        self.push_screen(LoginScreen())


if __name__ == "__main__":
    GameRecommenderApp().run()