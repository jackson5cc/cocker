from django.db.models.fields.files import ImageFieldFile
from rest_framework.decorators import api_view
from rest_framework.response import Response

from store.models import ProductImage


@api_view()
def say_hello(request):
    image = ProductImage.objects.get(pk=19)
    photo: ImageFieldFile = image.photo 

    # methods inherited from File 
    photo.open()
    photo.save()
    photo.delete()

    return Response({
      'name': photo.name,
      # 'path': photo.path,
      'url': photo.url,
      'size': photo.size,
      'height': photo.height,
      'width': photo.width
    })
