import os
import json
import requests
import shutil

from datetime import datetime
from gradio_client import Client, handle_file

from image_handler import ImageManager
from constants import DirectoryPath, TokensAndURLs
from utils import Utils


os.makedirs(DirectoryPath.OUTPUT_METADATA_DIR.value, exist_ok=True)

# Headers for the API request
headers = {
    "Authorization": f"Bearer {TokensAndURLs.HUGGING_FACE_API_TOKEN}"
}


class VirtualTryOn:
    def __init__(self, user_id):
        # self.client = Client(MODEL_NAME)
        self.output_dir = DirectoryPath.OUTPUT_DIR.value
        self.output_metadata_dir = DirectoryPath.OUTPUT_METADATA_DIR.value
        self.user_id = user_id
        self.image_manager_obj = ImageManager(user_id)
        os.makedirs(self.output_dir, exist_ok=True)

    def get_output_path(self):
        unique_id = Utils.generate_unique_id(
            f"{self.user_id}_output_{datetime.now().isoformat()}"
        )
        return os.path.join(self.output_dir, f"{unique_id}.jpeg")

    def save_metadata(self, metadata):
        # Save metadata per user in a JSON file
        metadata_path = os.path.join(
            self.output_metadata_dir, f"{self.user_id}_metadata.json"
        )

        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as file:
                user_metadata = json.load(file)
        else:
            user_metadata = []

        user_metadata.append(metadata)

        with open(metadata_path, "w") as file:
            json.dump(user_metadata, file, indent=4)

    def copy_image(self, src_path, dest_path):
        """Copy an image from src_path to dest_path."""
        shutil.copy2(src_path, dest_path)

    def process_try_on(self):
        # Fetch input images
        try:
            person_image_path = self.image_manager_obj.fetch_latest_unused_image(
                "person", get_url=False
            )
            garment_image_path = self.image_manager_obj.fetch_latest_unused_image(
                "garment", get_url=False
            )

            output_path = self.get_output_path()
            self.copy_image(person_image_path, output_path)

            # Save metadata
            metadata = {
                "person_image": person_image_path,
                "garment_image": garment_image_path,
                "output_image": output_path
            }
            self.save_metadata(metadata)
            print("Try-on result saved at:", output_path)
            return output_path
        except Exception as e:
            print(f"Failed to process the image.Message: {e}")
            return None

    def process_try_on_orig(self):
        # Fetch input images
        person_media_url = self.image_manager_obj.fetch_latest_unused_image(
            "person", get_url=True
        )
        garment_media_url = self.image_manager_obj.fetch_latest_unused_image(
            "garment", get_url=True
        )

        # Predict try-on result
        media_url, seed, response = self.client.predict(
            person_img=handle_file(person_media_url),
            garment_img=handle_file(garment_media_url),
            seed=0,
            randomize_seed=True,
            api_name="/tryon"
        )

        # Check if API response is successful
        if response.status_code == 200:
            output_path = self.get_output_path()
            image = requests.get(media_url)
            with open(output_path, "wb") as output_file:
                output_file.write(image.content)

            # Save metadata
            metadata = {
                "person_image": person_media_url,
                "garment_image": garment_media_url,
                "output_image": output_path
            }
            self.save_metadata(metadata)
            print("Try-on result saved at:", output_path)
        else:
            print(f"Failed to process the image. Status code: {response.status_code}, Message: {response.text}")


# Example usage
if __name__ == "__main__":
    try_on = VirtualTryOn(user_id="srujan")
    try_on.process_try_on()
