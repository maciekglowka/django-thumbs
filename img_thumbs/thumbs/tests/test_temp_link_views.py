import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from thumbs.models import ImageTempLink, ThumbPlan, ThumbUser, UserImage

from .utils import NON_IMAGE_FILE, TEST_IMAGES, delete_test_files


class TestGetImageTempLinkView(APITestCase):
    def setUp(self):
        allow_links_plan = ThumbPlan.objects.create(
            name = 'Links_PLAN',
            use_expiring_links=True,
            use_source_img=True
        )

        disallow_links_plan = ThumbPlan.objects.create(
            name = 'No Links_PLAN',
            use_expiring_links=False,
            use_source_img=True
        )

        self.link_user = User.objects.create_user(
            username=f'link_user',
            email=f'link_@test.com'
        )
        ThumbUser.objects.create(
            user = self.link_user,
            plan = allow_links_plan
        )

        self.nolink_user = User.objects.create_user(
            username=f'no_link_user',
            email=f'no_link_@test.com'
        )
        ThumbUser.objects.create(
            user = self.nolink_user,
            plan = disallow_links_plan
        )

        self.image_ids_to_delete = []

        for user in [self.link_user, self.nolink_user]:
            with open(TEST_IMAGES[0], 'rb') as f:
                img = UserImage.objects.create(
                    user=user,
                    file = File(f)
                )
            self.image_ids_to_delete.append(img.pk)

            self.image_ids_to_delete.extend(
                [a.pk for a in img.thumbs.all()]
            )


    def tearDown(self):
        delete_test_files(self.image_ids_to_delete)

    def test_get_image_temp_link_view_create_link(self):
            self.client.force_authenticate(self.link_user)

            img = UserImage.objects.filter(user=self.link_user).first()
            exp = settings.TEMP_LINK_MIN_SECONDS

            timestamp_before = timezone.now()
            response = self.client.get(f'/thumbs/get_img_temp_link/?img={img.id}&exp={exp}')
            timestamp_after = timezone.now()
            self.assertEqual(status.HTTP_201_CREATED, response.status_code)
            
            link = response.data

            img_response = self.client.get(link)
            self.assertEqual(status.HTTP_302_FOUND, img_response.status_code)
            self.assertEqual(img_response.url, img.file.url)

            link_obj = ImageTempLink.objects.last()
            self.assertGreaterEqual(link_obj.expiration, timestamp_before + datetime.timedelta(seconds=exp))
            self.assertLessEqual(link_obj.expiration, timestamp_after + datetime.timedelta(seconds=exp))

    def test_get_image_temp_link_view_exp_to_soon(self):
            self.client.force_authenticate(self.link_user)

            img = UserImage.objects.filter(user=self.link_user).first()
            exp = settings.TEMP_LINK_MIN_SECONDS - 1

            response = self.client.get(f'/thumbs/get_img_temp_link/?img={img.id}&exp={exp}')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_get_image_temp_link_view_exp_to_late(self):
            self.client.force_authenticate(self.link_user)

            img = UserImage.objects.filter(user=self.link_user).first()
            exp = settings.TEMP_LINK_MAX_SECONDS + 1

            response = self.client.get(f'/thumbs/get_img_temp_link/?img={img.id}&exp={exp}')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_get_image_temp_link_view_wrong_user(self):
            self.client.force_authenticate(self.link_user)

            img = UserImage.objects.filter(user=self.nolink_user).first()
            exp = settings.TEMP_LINK_MIN_SECONDS

            response = self.client.get(f'/thumbs/get_img_temp_link/?img={img.id}&exp={exp}')
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_get_image_temp_link_view_wrong_plan(self):
            self.client.force_authenticate(self.nolink_user)

            img = UserImage.objects.filter(user=self.nolink_user).first()
            exp = settings.TEMP_LINK_MIN_SECONDS

            response = self.client.get(f'/thumbs/get_img_temp_link/?img={img.id}&exp={exp}')
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_get_image_temp_link_view_wrong_id(self):
            self.client.force_authenticate(self.link_user)

            exp = settings.TEMP_LINK_MIN_SECONDS

            response = self.client.get(f'/thumbs/get_img_temp_link/?img={-1}&exp={exp}')
            self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

class TestParseImageTempLinkView(APITestCase):
    def setUp(self):
        allow_links_plan = ThumbPlan.objects.create(
            name = 'Links_PLAN',
            use_expiring_links=True,
            use_source_img=True
        )

        self.user = User.objects.create_user(
            username=f'link_user',
            email=f'link_@test.com'
        )
        ThumbUser.objects.create(
            user = self.user,
            plan = allow_links_plan
        )

        self.image_ids_to_delete = []

        with open(TEST_IMAGES[0], 'rb') as f:
            img = UserImage.objects.create(
                user=self.user,
                file = File(f)
            )
        self.image_ids_to_delete.append(img.pk)

        self.image_ids_to_delete.extend(
            [a.pk for a in img.thumbs.all()]
        )


    def tearDown(self):
        delete_test_files(self.image_ids_to_delete)

    def test_parse_image_temp_link_view(self):
            self.client.force_authenticate(self.user)

            img = UserImage.objects.filter(user=self.user).first()
 
            exp = timezone.now() + datetime.timedelta(seconds=settings.TEMP_LINK_MIN_SECONDS)
            link_obj = ImageTempLink.objects.create(
                image = img,
                expiration = exp
            )

            temp_link = link_obj.generate_link()

            response = self.client.get(temp_link)
            self.assertEqual(status.HTTP_302_FOUND, response.status_code)
            self.assertEqual(response.url, img.file.url)

    def test_parse_image_temp_link_view_expired(self):
            self.client.force_authenticate(self.user)

            img = UserImage.objects.filter(user=self.user).first()
 
            exp = timezone.now() - datetime.timedelta(seconds=1)
            link_obj = ImageTempLink.objects.create(
                image = img,
                expiration = exp
            )

            temp_link = link_obj.generate_link()

            response = self.client.get(temp_link)
            self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_parse_image_temp_link_view_wrong_sign(self):
            self.client.force_authenticate(self.user)

            img = UserImage.objects.filter(user=self.user).first()
 
            exp = timezone.now() + datetime.timedelta(seconds=settings.TEMP_LINK_MIN_SECONDS)
            link_obj = ImageTempLink.objects.create(
                image = img,
                expiration = exp
            )

            temp_link = link_obj.generate_link()
            temp_link = temp_link[:-1]
            response = self.client.get(temp_link)
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
            