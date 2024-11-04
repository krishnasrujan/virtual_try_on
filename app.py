import logging
import os
import uvicorn

from pathlib import Path
from fastapi import FastAPI, Form, Request, Response, responses
from twilio.twiml.messaging_response import MessagingResponse

from constants import DirectoryPath, TokensAndURLs
from image_handler import ImageManager
from chat_history_manager import ChatHistoryManager
from merge_images import MergeImages


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/get_image/{image_name}")
def get_image(image_name: str):
    try:
        image_path = Path(os.path.join(DirectoryPath.OUTPUT_DIR.value, image_name))
        if image_path.exists():
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()
            headers = {
                "Content-Type": "image/jpeg",
                "Content-Disposition": "inline"
            }
            return Response(content=image_bytes, headers=headers)
        else:
            raise "Image not found"
    except Exception as e:
        logger.log(level=logging.ERROR, msg=f"Did not find the output image. Error : {e}")
        return {"error": "Image not found"}, 404


# Webhook to handle messages from Twilio
@app.post("/webhook")
def webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None)
):
    from_number = From
    message_body = Body.strip().lower()  # Convert to lowercase and remove leading/trailing spaces
    image_manager_obj = ImageManager(user_id=from_number)
    response = MessagingResponse()
    try:
        chat_entry = {'user_message': message_body}
        ChatHistoryManager.update_chat_history(from_number, chat_entry)

        image_type = None
        # Determine image type based on message content
        if 'garment' in message_body:
            image_type = "garment"
        elif 'person' in message_body:
            image_type = "person"
        # Case 1: Image and type provided together
        if NumMedia > 0 and MediaUrl0 and image_type:
            try:
                image_manager_obj.download_image(MediaUrl0, image_type)
                output_response = f"Got your {image_type} image."
                if image_type == "garment" and not image_manager_obj.has_unused_image("person"):
                    output_response += " Also, please provide the person image."
                elif image_type == "person" and not image_manager_obj.has_unused_image("garment"):
                    output_response += " Also, please provide the garment image."
            except Exception as e:
                logger.log(level=logging.ERROR, msg=f"Error downloading image: {e}")
                output_response = "Failed to process the image. Please try again."

        # Case 2: Only image provided, no type specified
        elif NumMedia > 0 and MediaUrl0:
            try:
                image_manager_obj.download_image(MediaUrl0, None)
                output_response = "Please specify the image type for the uploaded image."
            except Exception as e:
                logger.log(msg=f"Error downloading image without type: {e}")
                output_response = "Failed to process the image. Please try again."

        # Case 3: Type specified but no image provided
        elif image_type and NumMedia == 0:
            try:
                if not image_manager_obj.has_unused_image(None):
                    output_response = f"""Please send the {image_type} image to proceed."""
                    response.message(output_response)
                    return Response(content=str(response), media_type="application/xml")
                else:
                    image_manager_obj.rename_image(old_image_type=None, new_image_type=image_type)
                    # Check if the complementary image is needed for virtual try-on
                    if image_type == "garment" and not image_manager_obj.has_unused_image("person"):
                        output_response = "Also, please provide the person image."
                    elif image_type == "person" and not image_manager_obj.has_unused_image("garment"):
                        output_response = "Also, please provide the garment image."
                    else:
                        pass
            except Exception as e:
                logger.log(level=logging.ERROR, msg=f"Error processing image type without image: {e}")
                output_response = "Failed to process your request. Please try again."
        # Case 4: No valid image or type information provided
        else:
            output_response = "Please provide an image along with its type (garment or person) to use the virtual try-on service."

        if image_manager_obj.has_unused_image("garment") and image_manager_obj.has_unused_image("person"):
            merge_images_obj = MergeImages(user_id=from_number)
            # Both images are available, process the virtual try-on
            file_path = merge_images_obj.merge_images()
            image_name = os.path.basename(file_path)
            media_url = f"{TokensAndURLs.BASE_URL.value}/get_image/{image_name}"
            output_response = "Here is the virtual try-on image!"
            response.message(output_response).media(media_url)
        else:
            response.message(output_response)
        ChatHistoryManager.update_chat_history(from_number, {"bot_response": output_response})
        return Response(content=str(response), media_type="application/xml")
    except Exception as e:
        logger.log(level=logging.ERROR, msg=f"Unexpected error in webhook handler: {e}")
        output_response = "An error occurred while processing your request. Please try again later."
        response.message(output_response)
        ChatHistoryManager.update_chat_history(from_number, {"bot_response": output_response})
        return Response(content=str(response), media_type="application/xml")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
