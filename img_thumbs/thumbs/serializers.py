from rest_framework import serializers
from thumbs.models import UserImage

class UserImageCreateSerializer(serializers.ModelSerializer):
    class Meta():
        model = UserImage
        fields = ('file',)

    def create(self, validated_data):
        ### ADD VALIDATION
        user = self.context['user']
        file = validated_data['file']
        
        image = UserImage.objects.create(
            user = user,
            file = file
        )
        return image