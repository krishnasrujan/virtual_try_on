# import base64
# import cv2
import logging
import os
import json
import requests
import shutil

from datetime import datetime
from gradio_client import Client, file

from image_handler import ImageManager
from constants import DirectoryPath, TokensAndURLs
from utils import Utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HUGGING_FACE_API_TOKEN = os.getenv("HF_API_TOKEN")

class VirtualTryOn:
    def __init__(self, user_id):
        self.client_1 = Client(
            TokensAndURLs.MODEL_NAME.value,
            hf_token=HUGGING_FACE_API_TOKEN
        )
        self.client_2 = Client(
            "Nymbo/Virtual-Try-On",
            hf_token=HUGGING_FACE_API_TOKEN
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

    def process_try_on_1(self):
        try:
            # Fetch input images
            person_media_path = self.image_manager_obj.fetch_latest_unused_image(
                "person", get_url=False
            )
            garment_media_path = self.image_manager_obj.fetch_latest_unused_image(
                "garment", get_url=False
            )

            # Predict try-on result
            media_url, seed, response = self.client_1.predict(
                person_img=person_media_path,
                garment_img=garment_media_path,
                seed=1,
                randomize_seed=True
            )

            # Check if API response is successful
            if response.status_code == 200:
                output_path = self.get_output_path()
                image = requests.get(media_url)
                with open(output_path, "wb") as output_file:
                    output_file.write(image.content)

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

    def process_try_on_2(self):
        try:
            # Fetch input images
            person_media_path = self.image_manager_obj.fetch_latest_unused_image(
                "person", get_url=False
            )
            garment_media_path = self.image_manager_obj.fetch_latest_unused_image(
                "garment", get_url=False
            )

            # Predict try-on result
            media_url, seed, response = self.client_2.predict(
                dict={"background": file(person_media_path), "layers": [], "composite": None},
                garm_img=file(garment_media_path),
                garment_des="Sample garment description",
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

    # def process_try_on_by_hf(self):
    #     try:
    #         # Fetch input images
    #         person_media_url = self.image_manager_obj.fetch_latest_unused_image(
    #             "person", get_url=False
    #         )
    #         garment_media_url = self.image_manager_obj.fetch_latest_unused_image(
    #             "garment", get_url=False
    #         )
    #         person_img = cv2.imread(person_media_url)
    #         garment_img = cv2.imread(garment_media_url)
    #         encoded_person_img = cv2.imencode('.png', cv2.cvtColor(person_img, cv2.COLOR_RGB2BGR))[1].tobytes()
    #         encoded_person_img = base64.b64encode(encoded_person_img).decode('utf-8')
    #         encoded_garment_img = cv2.imencode('.png', cv2.cvtColor(garment_img, cv2.COLOR_RGB2BGR))[1].tobytes()
    #         encoded_garment_img = base64.b64encode(encoded_garment_img).decode('utf-8')
    #
    #         data = {
    #             "humanImage": encoded_person_img,
    #             "clothImage": encoded_garment_img,
    #             "seed": 0
    #         }
    #         headers = {
    #             "Authorization": f"Bearer {TokensAndURLs.HUGGING_FACE_API_TOKEN.value}"
    #         }
    #
    #         response = requests.post(
    #             url=f"https://api-inference.huggingface.co/models/{TokensAndURLs.MODEL_NAME.value}/tryon/" + "Submit",
    #             headers=headers,
    #             data=json.dumps(data),
    #             timeout=50
    #         )
    #         if response.status_code == 200:
    #             result = response.json()['result']
    #             media_url = response.json().get("media_url")
    #             seed = response.json().get("seed")
    #             print(result)
    #             print("Media URL:", media_url)
    #             print("Seed:", seed)
    #             output_path = self.get_output_path()
    #             image = requests.get(media_url)
    #             with open(output_path, "wb") as output_file:
    #                 output_file.write(image.content)
    #             return output_path
    #
    #     except Exception as e:
    #         logger.log(
    #             level=logging.ERROR,
    #             msg=f"Got an error while generating the output image. "
    #                 f"User: {self.user_id} Error: [{e}]"
    #         )
    #         raise e