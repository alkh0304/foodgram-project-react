import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework.serializers import ImageField, ValidationError

IMAGE_UUID4_NAME = '{}.{}'
IMAGE64ERROR = 'неверный файл картинки'
BASE64 = ";base64,"


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        try:
            format, imgstr = data.split(BASE64)
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=IMAGE_UUID4_NAME.format(
                    str(uuid.uuid4()), ext))
        except ValueError:
            raise ValidationError(IMAGE64ERROR)
        return data
