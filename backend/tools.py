from PIL import Image
from io import BytesIO
import base64
import mimetypes
import tempfile



def uri_to_file(uri):
    header, encoded = uri.split(",", 1)
    ext = mimetypes.guess_extension(header.split(";")[0].split(":")[1])
    print(header, ext)

    data = base64.b64decode(encoded)
    print(data)
    image = Image.open(BytesIO(data))
    image.load()

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp:
        image.save(temp, format=(image.format or "PNG"))
        path = temp.name
    print(path)

    return path
