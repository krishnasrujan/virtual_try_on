import os
import json

from constants import DirectoryPath


os.makedirs(DirectoryPath.CHAT_HISTORY_DIR.value, exist_ok=True)

class ChatHistoryManager:
    def __init__(self):
        pass

    @staticmethod
    def update_chat_history(user_id, entry):
        """Add an entry to the user's chat history JSON."""
        history_file = os.path.join(DirectoryPath.CHAT_HISTORY_DIR.value, f"{user_id}.json")

        if os.path.exists(history_file):
            with open(history_file, "r") as file:
                history = json.load(file)
        else:
            history = []

        history.append(entry)
        with open(history_file, "w") as file:
            json.dump(history, file, indent=4)


