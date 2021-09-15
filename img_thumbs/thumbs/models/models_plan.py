from django.db import models


class ThumbRule(models.Model):
    height = models.IntegerField(unique=True)

    def __str__(self):
        return f'{self.height}px Thumb Rule'

class ThumbPlan(models.Model):
    name = models.CharField(max_length=50, unique=True)

    use_source_img = models.BooleanField(default=False)
    use_expiring_links = models.BooleanField(default=False)
    thumb_rules = models.ManyToManyField(
        ThumbRule
    )

    def __str__(self):
        return self.name