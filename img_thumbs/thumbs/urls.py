from django.urls import path
from thumbs import views

app_name = 'thumbs'
urlpatterns = [
    path('upload_img/', views.ImageUploadView.as_view()),
    path('list_img/', views.ImageListView.as_view()),
    path('get_img_temp_link/', views.GetImageTempLink.as_view()),
    path('tmp/<str:slug>', views.ParseImageTempLink.as_view(), name='tmpLink')
]