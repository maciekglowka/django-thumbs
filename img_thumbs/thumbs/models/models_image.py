from io import BytesIO
import os
import uuid
from pathlib import Path
from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
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

    def save(self, *args, **kwargs):
        first_save = True if self.pk == None else False

        plan = self.user.thumb_user.plan
        rules = plan.thumb_rules.all()

        super().save(*args, **kwargs)

        if not first_save:
            return

        for rule in rules:
            ImageThumb.objects.create(
                image = self,
                rule=rule
            )

    def get_all_urls(self):
        urls = {
            'main':None,
            'thumbs':{}
        }

        if self.user.thumb_user.plan.use_source_img:
            urls['main'] = self.file.url

        #add fetch all
        thumbs = self.thumbs.all()
        for thumb in thumbs:
            urls['thumbs'][thumb.rule.height] = thumb.file.url

        return urls


class ImageThumb(models.Model):
    image = models.ForeignKey(UserImage, on_delete=models.CASCADE, related_name='thumbs')
    rule = models.ForeignKey(ThumbRule, on_delete=models.PROTECT)
    file = models.ImageField()

    def save(self, *args, **kwargs):
        if self.pk != None:
            super().save(*args, **kwargs)
            return

        source_path = self.image.file.path
        source_image = Image.open(source_path)
        width = int(source_image.size[0] * self.rule.height /  source_image.size[1])

        thumb_image = source_image.resize((width,self.rule.height), Image.ANTIALIAS)
        thumb_io = BytesIO()

        thumb_image.save(thumb_io, format=source_image.format)
        
        path_obj = Path(self.image.file.name)
        filename = get_unique_name(path_obj.name)
        thumb_path = os.path.join(path_obj.parent, filename)

        self.file.save(
            thumb_path,
            content=ContentFile(thumb_io.getvalue()),
            save=False
        )

        super().save(*args, **kwargs)

class ImageTempLink(models.Model):
    target_url = models.CharField(max_length=255)
    expiration = models.DateTimeField()