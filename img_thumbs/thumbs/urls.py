from django.urls import path
from thumbs import views

urlpatterns = [
    path('upload_img/', views.ImageUploadView.as_view()),
    path('list_img/', views.ImageListView.as_view()),
    path('get_img_temp_link/<int:pk>', views.GetImageTempLink.as_view()),
    path('tmp/<uuid:slug>', views.ParseImageTempLink.as_view())
]