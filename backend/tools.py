from PIL import Image
from io import BytesIO
import base64
import mimetypes
import tempfile

from db import chats


def image_to_file(user, index):
    if index < 0 or index >= user.images or 0:
        return (1, "Internal error, image index specified outside of valid range")

    message = chats.find_one(
            { "user_id": user.id, "image_id": index },
            { "imageuri": 1 }
        )

    if not message or not message.get("imageuri"):
        return (1, "Internal error, failed to find specified image")
    uri = message["imageuri"]

    try:
        # Extract format info
        header, encoded = uri.split(",", 1)
        ext = mimetypes.guess_extension(header.split(";")[0].split(":")[1])

        # Load image data
        data = base64.b64decode(encoded)
        image = Image.open(BytesIO(data))
        image.load()

        # Save to a temp file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp:
            image.save(temp, format=(image.format or "PNG"), optimize=True)
            path = temp.name

        return (0, path)
    except Exception as e:
        print(e)
        return (1, "Internal error, failed to process image.")

def resize_image(uri):
    # Extract format info
    header, encoded = uri.split(",", 1)
    mime = header.split(";")[0].split(":")[1]
    ext = mimetypes.guess_extension(mime)

    # Load image data
    data = base64.b64decode(encoded)
    image = Image.open(BytesIO(data))
    image.load()

    # Downscale if too large
    largest = max(image.width, image.height)
    if largest > 1024:
        factor = 1024 / largest
        image = image.resize(
                (int(factor * image.width), int(factor * image.height)),
                Image.LANCZOS)

    # Save to uri
    buffer = BytesIO()
    format = image.format or "PNG"
    image.save(buffer, format=format, optimize=True)
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:{mime};base64,{data}"
