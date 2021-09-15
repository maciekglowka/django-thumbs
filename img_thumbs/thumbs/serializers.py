from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from thumbs.models import UserImage


class UserImageCreateSerializer(serializers.ModelSerializer):
    class Meta():
        model = UserImage
        fields = ('file',)

    def validate_file(self, value):
        if not value:
            raise serializers.ValidationError
        return value

    def create(self, validated_data):
        user = self.context['user']
        if not user or not hasattr(user, 'thumb_user'):
            raise serializers.ValidationError

        file = validated_data.get('file', None)
        if not file:
            raise serializers.ValidationError
        
        image = UserImage.objects.create(
            user = user,
            file = file
        )
        return image