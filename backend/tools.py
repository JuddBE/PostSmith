from PIL import Image
from io import BytesIO
import base64
import mimetypes
import tempfile



def image_to_file(user, index):
    if index < 0 or index >= len(user.images or []):
        return (1, "Internal error, image index specified outside of valid range")
    uri = user.images[index]

    try:
        # Extract format info
        header, encoded = uri.split(",", 1)
        ext = mimetypes.guess_extension(header.split(";")[0].split(":")[1])

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

        # Save to a temp file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp:
            image.save(temp, format=(image.format or "PNG"), optimize=True)
            path = temp.name

        return (0, path)
    except Exception as e:
        print(e)
        return (1, "Internal error, failed to process image.")
