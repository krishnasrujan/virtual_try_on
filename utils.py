import hashlib

class Utils:

    @staticmethod
    def generate_unique_id(unique_string):
        # Create a hash of the combined string for a shorter unique ID
        unique_id = hashlib.md5(unique_string.encode()).hexdigest()
        return unique_id


class MyCustomError(Exception):  # Correct
    pass