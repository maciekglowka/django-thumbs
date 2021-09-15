from django.contrib.auth.models import User
from django.db import models

from thumbs.models import ThumbPlan


class ThumbUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='thumb_user')
    plan = models.ForeignKey(ThumbPlan, on_delete=models.PROTECT)
