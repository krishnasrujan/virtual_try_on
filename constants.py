from enum import Enum


class TokensAndURLs(Enum):
    HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/Kwai-Kolors/Kolors-Virtual-Try-On"
    MODEL_NAME = "AhmedAlmaghz/Kolors-Virtual-Try-On"
    BASE_URL = "https://fc3e-2401-4900-1c0e-1d9d-b9ce-4a6c-ec16-58e2.ngrok-free.app"

class DirectoryPath(Enum):
    INPUT_DIR = "./input_images"
    INPUT_METADATA_DIR = "./input_metadata"
    OUTPUT_DIR = "./output_images"
    OUTPUT_METADATA_DIR = "./output_metadata"
    CHAT_HISTORY_DIR = "./chat_history"

