import os
import uuid
from io import BytesIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core import signing
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from PIL import Image

from thumbs.models import ThumbRule


def get_unique_name(filename):
    ext = filename.split('.')[-1]
    return f"{uuid.uuid4()}.{ext}"

def user_dir_path(instance, filename):
    return 'photos/{}/{}'.format(instance.user.id, get_unique_name(filename))


class UserImage(models.Model):
    user = models.ForeignKey(User, related_name='images', on_delete=models.CASCADE)
    file = models.ImageField(upload_to=user_dir_path, null=True)

    parent = models.ForeignKey('UserImage', related_name='thumbs', on_delete=models.CASCADE, default=None, null=True)
    thumb_rule = models.ForeignKey(ThumbRule, null=True, default=None, on_delete=models.PROTECT)

    def __str__(self):
        return f'Image {self.pk}'

    def save(self, *args, **kwargs):
        if self.pk != None or not hasattr(self.user, 'thumb_user'):
            super().save(*args, **kwargs)
            return
        
        if self.parent == None:
            super().save(*args, **kwargs)
            self.create_thumbs()
            if not self.user.thumb_user.plan.use_source_img:
                self.file.delete()
        else:
            self.create_thumb_file()
            super().save(*args, **kwargs)


    def create_thumbs(self):
        plan = self.user.thumb_user.plan
        rules = plan.thumb_rules.all()

        for rule in rules:
            UserImage.objects.create(
                user=self.user,
                parent=self,
                thumb_rule=rule
            )

    def create_thumb_file(self):
        if self.file.name:
            return

        source_path = self.parent.file.path
        source_image = Image.open(source_path)
        width = int(source_image.size[0] * self.thumb_rule.height /  source_image.size[1])

        thumb_image = source_image.resize((width,self.thumb_rule.height), Image.ANTIALIAS)
        thumb_io = BytesIO()

        thumb_image.save(thumb_io, format=source_image.format)
        
        path_obj = Path(self.parent.file.name)
        filename = get_unique_name(path_obj.name)
        thumb_path = os.path.join(path_obj.parent, filename)

        self.file.save(
            thumb_path,
            content=ContentFile(thumb_io.getvalue()),
            save=False
        )

    def get_all_urls(self):
        urls = {}

        for thumb in self.thumbs.all().prefetch_related('thumb_rule'):
            urls[thumb.thumb_rule.height] = {
                'id':thumb.pk,
                'url':thumb.file.url
            }

        if self.file.name:
            urls['original'] = {
                'id':self.pk,
                'url':self.file.url
            }

        return urls
        

class ImageTempLink(models.Model):
    image = models.ForeignKey(UserImage, on_delete=models.CASCADE)
    expiration = models.DateTimeField()

    def __str__(self):
        return f'Link for image {self.image.pk}'

    def generate_link(self):
        signer = signing.Signer()
        sign = signer.sign(self.pk)

        url = reverse('thumbs:tmpLink', args=[sign])
        return url