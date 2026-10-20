import datetime as dt
import os
import platform
import subprocess
from pathlib import Path


class PersonalAssistant:
    def __init__(self, name="Assistant"):
        self.name = name

    # --------------------------------------------------
    # TIME
    # --------------------------------------------------

    def get_time(self):
        current_time = dt.datetime.now().strftime("%I:%M:%S %p")
        return f"The current time is {current_time}."

    # --------------------------------------------------
    # DATE
    # --------------------------------------------------

    def get_date(self):
        current_date = dt.datetime.now().strftime("%A, %d %B %Y")
        return f"Today's date is {current_date}."

    # --------------------------------------------------
    # OPEN FOLDER
    # --------------------------------------------------

    def open_folder(self, folder_name):
        folder_name = folder_name.lower().strip()

        folders = {
            "home": Path.home(),
            "downloads": Path.home() / "Downloads",
            "documents": Path.home() / "Documents",
            "pictures": Path.home() / "Pictures",
        }

        if folder_name not in folders:
            return f"I don't know how to open the {folder_name} folder."

        folder_path = folders[folder_name]

        if not folder_path.exists():
            return f"The {folder_name} folder was not found."

        try:
            system = platform.system()

            if system == "Windows":
                os.startfile(str(folder_path))

            elif system == "Darwin":
                subprocess.Popen(["open", str(folder_path)])

            elif system == "Linux":
                subprocess.Popen(["xdg-open", str(folder_path)])

            else:
                return f"Opening folders is not supported on {system}."

            return f"Opening your {folder_name} folder."

        except Exception as error:
            return f"I couldn't open the {folder_name} folder: {error}"

    # --------------------------------------------------
    # OPEN TERMINAL
    # --------------------------------------------------

    def open_terminal(self):
        try:
            system = platform.system()

            if system == "Windows":
                subprocess.Popen(
                    ["cmd.exe"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )

            elif system == "Darwin":
                subprocess.Popen(
                    ["open", "-a", "Terminal"]
                )

            elif system == "Linux":
                terminals = [
                    ["gnome-terminal"],
                    ["konsole"],
                    ["xfce4-terminal"],
                    ["x-terminal-emulator"],
                ]

                for terminal in terminals:
                    try:
                        subprocess.Popen(terminal)
                        break
                    except FileNotFoundError:
                        continue
                else:
                    return "I couldn't find a terminal application."

            else:
                return f"Opening the terminal is not supported on {system}."

            return "Opening the terminal."

        except Exception as error:
            return f"I couldn't open the terminal: {error}"

    # --------------------------------------------------
    # COMMAND ROUTER
    #
    # Returns:
    #   string -> command handled here
    #   None   -> app.py should handle it
    # --------------------------------------------------

    def process_command(self, command):
        if not command:
            return "Please enter a command."

        command = command.strip()
        print(f"Processing command: {command}")
        command_lower = command.lower()

        # -----------------------------
        # TIME
        # -----------------------------

        if command_lower in {
            "time",
            "what time is it",
            "what is the time",
            "tell me the time",
            "current time",
        }:
            return self.get_time()

        # -----------------------------
        # DATE
        # -----------------------------

        if command_lower in {
            "date",
            "today",
            "today's date",
            "what is today's date",
            "what is the date",
            "tell me the date",
            "current date",
        }:
            return self.get_date()

        # -----------------------------
        # HOME
        # -----------------------------

        if any(
            phrase in command_lower
            for phrase in [
                "open home",
                "open home folder",
                "open my home folder",
            ]
        ):
            return self.open_folder("home")

        # -----------------------------
        # DOWNLOADS
        # -----------------------------

        if any(
            phrase in command_lower
            for phrase in [
                "open downloads",
                "open downloads folder",
                "open my downloads",
            ]
        ):
            return self.open_folder("downloads")

        # -----------------------------
        # DOCUMENTS
        # -----------------------------

        if any(
            phrase in command_lower
            for phrase in [
                "open documents",
                "open documents folder",
                "open my documents",
            ]
        ):
            return self.open_folder("documents")

        # -----------------------------
        # PICTURES
        # -----------------------------

        if any(
            phrase in command_lower
            for phrase in [
                "open pictures",
                "open pictures folder",
                "open my pictures",
            ]
        ):
            return self.open_folder("pictures")

        # -----------------------------
        # TERMINAL
        # -----------------------------

        if any(
            phrase in command_lower
            for phrase in [
                "open terminal",
                "open command prompt",
                "open cmd",
                "open console",
            ]
        ):
            return self.open_terminal()

        # -----------------------------
        # UNKNOWN COMMAND
        # -----------------------------

        return None

