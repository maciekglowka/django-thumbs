from django.contrib import admin

from thumbs.models import ThumbRule, ThumbPlan, ThumbUser, UserImage

# Register your models here.
@admin.register(ThumbRule)
class ThumbRuleAdmin(admin.ModelAdmin):
    pass

@admin.register(ThumbPlan)
class ThumbRuleAdmin(admin.ModelAdmin):
    pass

@admin.register(ThumbUser)
class ThumbRuleAdmin(admin.ModelAdmin):
    pass

@admin.register(UserImage)
class ThumbRuleAdmin(admin.ModelAdmin):
    pass