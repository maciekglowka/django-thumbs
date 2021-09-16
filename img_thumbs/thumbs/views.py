import datetime

from django.conf import settings
from django.core import signing
from django.db.models import Q
from django.http.response import HttpResponseRedirect
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import (NotFound, PermissionDenied,
                                       ValidationError)
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from thumbs.models import ImageTempLink, UserImage
from thumbs.serializers import UserImageCreateSerializer


# Create your views here.
class ImageUploadView(CreateAPIView):
    '''
    Allows to upload image by a registered user.
    Thumbnails are created according to users's plan.
    Image urls (incl. thumbs) are returned in a response.
    '''
    serializer_class = UserImageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            img = serializer.save()

            data = {
                'message':'OK',
                'id':img.pk,
                'urls': img.get_all_urls()
            }

            return Response(data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ImageListView(APIView):
    '''
    Lists all images owned by request user
    '''
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        images = UserImage.objects.filter(
            Q(user=request.user) &
            Q(parent__isnull=True)
        ).prefetch_related('thumbs__thumb_rule')

        img_list = []
        for img in images:
            img_list.append( {
                'id': img.pk,
                'urls': img.get_all_urls()
            })

        return Response(img_list, status=status.HTTP_200_OK)

class GetImageTempLink(APIView):
    '''
    Generates an ImageTempLink objects and returns an encoded url
    pointing to the object.
    Necessary query params: img (Image object id) and exp (expiration time in seconds)
    '''
    def get(self, request):       
        try:
            img_id = self.request.query_params.get('img', None)
            image = UserImage.objects.get(pk=img_id)
        except UserImage.DoesNotExist:
            raise NotFound

        try:
            expiration = int(self.request.query_params.get('exp', None))
            if expiration < settings.TEMP_LINK_MIN_SECONDS or expiration > settings.TEMP_LINK_MAX_SECONDS:
                raise ValidationError
        except TypeError:
            raise ValidationError

        if image.user != request.user or not request.user.thumb_user.plan.use_expiring_links:
            raise PermissionDenied

        if not image.file.name:
            raise NotFound

        expiration_datetime = timezone.now() + datetime.timedelta(seconds=expiration)

        link = ImageTempLink.objects.create(
            image=image,
            expiration=expiration_datetime
        )

        relative_url = link.generate_link()
        uri = request.build_absolute_uri(relative_url)

        return Response(uri, status=status.HTTP_201_CREATED)

class ParseImageTempLink(APIView):
    '''
    Decodes a slug value, pointing to ImageTempLink objects.
    If valid, returns a redirecto to image file url.
    '''
    def get(self, request, slug):

        try:
            signer = signing.Signer()
            pk = int(signer.unsign(slug))
        except (ValueError, TypeError, signing.BadSignature):
            raise ValidationError

        try:
            link_obj = ImageTempLink.objects.get(pk=pk)
        except ImageTempLink.DoesNotExist:
            raise NotFound

        if not link_obj.image or not link_obj.image.file.name:
            raise NotFound

        if link_obj.expiration < timezone.now():
            raise NotFound

        url = link_obj.image.file.url

        return HttpResponseRedirect(url)
