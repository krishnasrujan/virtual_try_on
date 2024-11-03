import os
import json
import requests

from datetime import datetime
from dotenv import load_dotenv
from constants import DirectoryPath, TokensAndURLs
from virtual_try_on import logger

# Load environment variables from .env file
load_dotenv()
twilio_account_id = os.getenv("TWILIO_ACCOUNT_ID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")

os.makedirs(DirectoryPath.INPUT_DIR.value, exist_ok=True)
os.makedirs(DirectoryPath.INPUT_METADATA_DIR.value, exist_ok=True)


class UserMetadataManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.metadata_file = os.path.join(
            DirectoryPath.INPUT_METADATA_DIR.value, f"{self.user_id}_metadata.json"
        )
        self.input_metadata = self.load_input_metadata()

    def load_input_metadata(self):
        """Load or initialize metadata for the user."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as file:
                return json.load(file)
        return []

    def save_metadata(self):
        """Save metadata to a JSON file."""
        print('saving the metadata:', self.input_metadata)
        with open(self.metadata_file, "w") as file:
            json.dump(self.input_metadata, file, indent=4)

    def add_image_metadata(self, media_url, image_location, image_type="None"):
        metadata = self.load_input_metadata()
        """Add new image metadata entry."""
        metadata.append({
            "media_url": media_url,
            "image_location": image_location,
            "image_type": image_type,
            "already_used": False
        })
        self.input_metadata = metadata
        self.save_metadata()

    def find_latest_unused_image(self, image_type):
        metadata = self.load_input_metadata()
        """Find and return the latest unused image metadata of a specific type."""
        for entry in reversed(metadata):
            if entry["image_type"] == image_type and not entry["already_used"]:
                return entry
        return None

    def mark_image_as_used(self, index):
        """Mark a specific image as used."""
        metadata = self.load_input_metadata()
        metadata[index]["already_used"] = True
        self.input_metadata = metadata
        self.save_metadata()


class ImageManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.metadata_manager = UserMetadataManager(user_id)

    def download_image(self, media_url, image_type=None):
        try:
            """Download image from a URL and save it locally, returning the file path."""
            retry_count = 0
            response = None

            while retry_count < 3:
                try:
                    response = requests.get(
                        media_url,
                        auth=(twilio_account_id, twilio_auth_token),
                        timeout=30
                    )
                    if response.status_code == 200:
                        break
                except requests.RequestException as e:
                    print(f"Attempt {retry_count + 1} failed with error: {e}")
                retry_count += 1

            if response and response.status_code == 200:
                filename = f"{self.user_id}_{image_type}_{datetime.now().isoformat()}.png"
                filepath = os.path.join(DirectoryPath.INPUT_DIR.value, filename)
                with open(filepath, "wb") as file:
                    file.write(response.content)
                self.metadata_manager.add_image_metadata(
                    media_url, filepath, image_type
                )
                print("Image downloaded at:", filepath)
                return filepath
            else:
                raise f"Failed to download the image for the user: {self.user_id}"
        except Exception as e:
            logger.log(f"Got an error while downloading the image. Media URL: "
                  f"[{media_url}] Image Type: [{image_type}] Error: [{e}]")
            raise e


    def rename_image(self, old_image_type=None, new_image_type="garment"):
        try:
            """Rename the latest unused image of old_image_type to new_image_type."""
            metadata = self.metadata_manager.load_input_metadata()
            latest_image = None

            # Find the latest unused image with the specified type
            for i in range(len(metadata) - 1, -1, -1):
                if metadata[i]["image_type"] == old_image_type and not metadata[i]["already_used"]:
                    latest_image = metadata[i]
                    index = i
                    break

            if latest_image:
                directory, original_filename = os.path.split(latest_image["image_location"])
                new_filename = f"{self.user_id}_{new_image_type}_{datetime.now().isoformat()}.png"
                new_filepath = os.path.join(directory, new_filename)
                print("inside renaming the image:", latest_image["image_location"], new_filepath)

                # Rename file and update metadata
                os.rename(latest_image["image_location"], new_filepath)
                latest_image["image_location"] = new_filepath
                latest_image["image_type"] = new_image_type
                metadata[index] = latest_image
                self.metadata_manager.input_metadata = metadata
                self.metadata_manager.save_metadata()
                return new_filepath
            else:
                raise "No unused image found with the specified type."
        except Exception as e:
            logger.log(f"Got an error while renaming the image. Media URL: "
                  f"[{media_url}] Error: [{e}]")
            raise e


    def fetch_latest_unused_image(self, image_type="garment", get_url=True):
        """Fetch the latest unused image of a specific type, returning its location or URL."""
        metadata = self.metadata_manager.load_input_metadata()
        for i in range(len(metadata) - 1, -1, -1):
            entry = metadata[i]
            if entry["image_type"] == image_type and not entry["already_used"]:
                self.metadata_manager.mark_image_as_used(i)
                return entry["media_url"] if get_url else entry["image_location"]
        raise f"No unused {image_type} image found for user {self.user_id}."

    def has_unused_image(self, image_type="garment"):
        """Check if there is an unused image of a specific type."""
        for entry in reversed(self.metadata_manager.input_metadata):
            if entry["image_type"] == image_type and not entry["already_used"]:
                return True
        return False


# Example usage
if __name__ == "__main__":
    user_id = "12345"
    media_url = "https://example.com/image.jpg"  # Replace with actual media URL

    # Initialize ImageManager and handle image operations
    image_manager = ImageManager(user_id)

    # Download and store the image
    saved_image_path = image_manager.download_image(media_url, image_type="None")
    print(f"Saved image path: {saved_image_path}")

    # Rename the latest 'None' type image to 'garment'
    renamed_image_path = image_manager.rename_image(old_image_type="None", new_image_type="garment")
    print(f"Renamed image path: {renamed_image_path}")

    # Fetch latest unused 'garment' type image
    garment_image = image_manager.fetch_latest_unused_image(image_type="garment")
    print(f"Latest unused garment image URL: {garment_image}")
