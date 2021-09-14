import pathlib
import json
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.files import File
from rest_framework import status
from rest_framework.test import APITestCase
from thumbs.models import UserImage, ThumbUser, ThumbPlan, ThumbRule
from .utils import delete_test_files, create_test_rules, TEST_IMAGES, NON_IMAGE_FILE

class TestImageUploadView(APITestCase):
    def setUp(self):
        self.rules = create_test_rules()

        self.user = User.objects.create_user(
            username='test_user',
            email='user@test.com'
        )

        self.image_ids_to_delete = []

    def tearDown(self):
        delete_test_files(self.image_ids_to_delete)

    def test_image_upload_single_thumb(self):
        plan = ThumbPlan.objects.create(
            name = 'SINGLE_PLAN',
            use_source_img=False
        )

        plan.thumb_rules.set([self.rules[0]])

        ThumbUser.objects.create(
            user = self.user,
            plan = plan
        )

        self.client.force_authenticate(self.user)

        for img_file in TEST_IMAGES:
            with open(img_file, 'rb') as f:
                response = self.client.post(
                    '/thumbs/upload_img/',
                    {'file':f}, format='multipart'
                )

            for img in response.data['urls'].values():
                self.image_ids_to_delete.append(img['id'])

            self.assertEqual(status.HTTP_201_CREATED, response.status_code)
            rule_height = plan.thumb_rules.first().height

            self.assertIn(rule_height, response.data['urls'])
            thumb_id = response.data['urls'][rule_height]['id']

            thumb = UserImage.objects.get(pk=thumb_id)
            self.assertIsNotNone(thumb.file.name)

            path_obj = pathlib.Path(thumb.file.path)
            self.assertTrue(path_obj.exists())

    def test_image_upload_multiple_thumbs(self):
        plan = ThumbPlan.objects.create(
            name = 'MULTIPLE_PLAN',
            use_source_img=False
        )

        plan.thumb_rules.set(self.rules)

        ThumbUser.objects.create(
            user = self.user,
            plan = plan
        )

        self.client.force_authenticate(self.user)
        for img_file in TEST_IMAGES:
            with open(img_file, 'rb') as f:
                response = self.client.post(
                    '/thumbs/upload_img/',
                    {'file':f}, format='multipart'
                )

            for img in response.data['urls'].values():
                self.image_ids_to_delete.append(img['id'])

            self.assertEqual(status.HTTP_201_CREATED, response.status_code)

            for rule in plan.thumb_rules.all():
                self.assertIn(rule.height, response.data['urls'])
                thumb_id = response.data['urls'][rule.height]['id']

                thumb = UserImage.objects.get(pk=thumb_id)
                self.assertIsNotNone(thumb.file.name)

                path_obj = pathlib.Path(thumb.file.path)
                self.assertTrue(path_obj.exists())

    def test_image_upload_include_original(self):
        plan = ThumbPlan.objects.create(
            name = 'SINGLE_PLAN',
            use_source_img=True
        )

        plan.thumb_rules.set([self.rules[0]])

        ThumbUser.objects.create(
            user = self.user,
            plan = plan
        )

        self.client.force_authenticate(self.user)

        for img_file in TEST_IMAGES:
            with open(img_file, 'rb') as f:
                response = self.client.post(
                    '/thumbs/upload_img/',
                    {'file':f}, format='multipart'
                )

            for img in response.data['urls'].values():
                self.image_ids_to_delete.append(img['id'])

            self.assertEqual(status.HTTP_201_CREATED, response.status_code)
            self.assertIn('original', response.data['urls'])
            img_id = response.data['urls']['original']['id']

            img = UserImage.objects.get(pk=img_id)
            self.assertIsNotNone(img.file.name)

            path_obj = pathlib.Path(img.file.path)
            self.assertTrue(path_obj.exists())

    def test_image_upload_nologin(self):
        with open(TEST_IMAGES[0], 'rb') as f:
            response = self.client.post(
                '/thumbs/upload_img/',
                {'file':f}, format='multipart'
            )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_image_upload_non_image(self):
        plan = ThumbPlan.objects.create(
            name = 'SINGLE_PLAN',
            use_source_img=False
        )

        plan.thumb_rules.set([self.rules[0]])

        ThumbUser.objects.create(
            user = self.user,
            plan = plan
        )

        self.client.force_authenticate(self.user)

        with open(NON_IMAGE_FILE, 'rb') as f:
            response = self.client.post(
                '/thumbs/upload_img/',
                {'file':f}, format='multipart'
            )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

class TestImageListView(APITestCase):
    def setUp(self):
        self.rules = create_test_rules()
        plan = ThumbPlan.objects.create(
            name = 'MULTIPLE_PLAN',
            use_source_img=True
        )

        plan.thumb_rules.set(self.rules)

        self.users = []
        
        for idx in range(2):
            user = User.objects.create_user(
                username=f'test_user_{idx}',
                email=f'user{idx}@test.com'
            )
            self.users.append(user)

            ThumbUser.objects.create(
                user = user,
                plan = plan
            )

        self.image_ids_to_delete = []

        for user in self.users:
            for img_file in TEST_IMAGES:
                with open(img_file, 'rb') as f:
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

    def test_image_upload_multiple_thumbs(self):
        for user in self.users:
            self.client.force_authenticate(user)

            response = self.client.get('/thumbs/list_img/')

            self.assertEqual(status.HTTP_200_OK, response.status_code)

            parent_images = UserImage.objects.filter(
                Q(user=user) &
                Q(parent__isnull=True)
            )

            self.assertEqual(len(response.data), len(parent_images))

            all_images = UserImage.objects.filter(user=user)

            for img in all_images:
                self.assertIn(img.file.name, json.dumps(response.data))
        