import logging
import os
import json
import shutil

from datetime import datetime
from gradio_client import Client
from PIL import Image

from image_handler import ImageManager
from constants import DirectoryPath, TokensAndURLs
from utils import Utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MergeImages:
    def __init__(self, user_id):
        self.client_1 = Client(
            TokensAndURLs.MODEL_NAME.value,
            hf_token=TokensAndURLs.HUGGING_FACE_API_TOKEN.value
        )
        self.client_2 = Client(
            "Nymbo/Virtual-Try-On",
            hf_token=TokensAndURLs.HUGGING_FACE_API_TOKEN.value
        )
        # self.client = Client("Nymbo/Virtual-Try-On")
        self.output_dir = DirectoryPath.OUTPUT_DIR.value
        self.output_metadata_dir = DirectoryPath.OUTPUT_METADATA_DIR.value
        self.user_id = user_id
        self.image_manager_obj = ImageManager(user_id)
        os.makedirs(self.output_dir, exist_ok=True)
        pass

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

    def merge_images(self):
        try:
            # Fetch input images
            person_media_path = self.image_manager_obj.fetch_latest_unused_image(
                "person", get_url=False
            )
            garment_media_path = self.image_manager_obj.fetch_latest_unused_image(
                "garment", get_url=False
            )

            person_image = Image.open(person_media_path)
            garment_image = Image.open(garment_media_path)

            combined_width = person_image.width + garment_image.width
            combined_height = max(person_image.height, garment_image.height)
            combined_image = Image.new('RGB', (combined_width, combined_height))
            # Paste the images
            combined_image.paste(person_image, (0, 0))
            combined_image.paste(garment_image, (person_image.width, 0))

            output_path = self.get_output_path()
            with open(output_path, "wb") as output_file:
                output_file.write(combined_image.content)

            # Save metadata
            metadata = {
                "person_image": person_media_path,
                "garment_image": garment_media_path,
                "output_image": output_path
            }
            self.save_metadata(metadata)
            return output_path
        except Exception as e:
            logger.log(
                level=logging.ERROR,
                msg=f"Got an error while generating the output image. "
                f"User: {self.user_id} Error: [{e}]"
            )
            raise e