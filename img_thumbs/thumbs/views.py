from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework import permissions
from thumbs.serializers import UserImageCreateSerializer
from thumbs.models import UserImage
from thumbs.permissions import IsImageOwner

# Create your views here.
class ImageUploadView(CreateAPIView):
    serializer_class = UserImageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            #self.perform_create(serializer)
            img = serializer.save()
            return Response({
                'message':'OK',
                'urls': img.get_all_urls()
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ImageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        images = UserImage.objects.prefetch_related('thumbs').filter(user=request.user)

        img_list = []
        for img in images:
            img_list.append({
                'id': img.pk,
                'urls': img.get_all_urls()
            })

        return Response(img_list, status=status.HTTP_200_OK)

class GetImageTempLink(APIView):
    permission_classes = [IsImageOwner]

class ParseImageTempLink(APIView):
    pass
