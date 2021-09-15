import datetime
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.core.files import File
from django.test import TestCase
from django.utils import timezone
from PIL import Image

from thumbs.models import ImageTempLink, ThumbPlan, ThumbUser, UserImage

from .utils import TEST_IMAGES, create_test_rules, delete_test_files


class TestUserImageModel(TestCase):
    def setUp(self):
        self.rules = create_test_rules()

        self.user = User.objects.create_user(
            username='test_user',
            email='user@test.com'
        )

        self.image_ids_to_delete = []

    def tearDown(self):
        delete_test_files(self.image_ids_to_delete)

    def add_image_for_delete(self, img):
        self.image_ids_to_delete.append(img.pk)
        self.image_ids_to_delete.extend(
            [a.pk for a in img.thumbs.all()]
        )

    def test_image_create_multiple_thumbs(self):
        plan = ThumbPlan.objects.create(
            name = 'MULTI_PLAN',
            use_source_img=False
        )

        plan.thumb_rules.set(self.rules)

        ThumbUser.objects.create(
            user = self.user,
            plan = plan
        )

        for img_file in TEST_IMAGES:
            with open(img_file, 'rb') as f:
                img = UserImage.objects.create(
                    user=self.user,
                    file = File(f)
                )
                self.add_image_for_delete(img)

            img_db_obj = UserImage.objects.get(pk=img.id)
            self.assertEqual(len(self.rules), len(img_db_obj.thumbs.all()))
            self.assertEqual('', img_db_obj.file.name)

            ### CHECK THUMBS
            for thumb in img_db_obj.thumbs.all().select_related('thumb_rule'):
                self.assertEqual(thumb.parent, img_db_obj)

                image = Image.open(thumb.file.path)
                height = image.size[1]
                self.assertEqual(height, thumb.thumb_rule.height)

    def test_image_create_source_only(self):
        plan = ThumbPlan.objects.create(
            name = 'MULTI_PLAN',
            use_source_img=True
        )

        ThumbUser.objects.create(
            user = self.user,
            plan = plan
        )

        for img_file in TEST_IMAGES:
            with open(img_file, 'rb') as f:
                img = UserImage.objects.create(
                    user=self.user,
                    file = File(f)
                )
                self.add_image_for_delete(img)

            img_db_obj = UserImage.objects.get(pk=img.id)
            self.assertEqual(0, len(img_db_obj.thumbs.all()))

            self.assertNotEqual('',img_db_obj.file.name)

    def test_get_all_urls(self):
        plan = ThumbPlan.objects.create(
            name = 'MULTI_PLAN',
            use_source_img=True
        )

        plan.thumb_rules.set(self.rules)

        ThumbUser.objects.create(
            user = self.user,
            plan = plan
        )

        for img_file in TEST_IMAGES:
            with open(img_file, 'rb') as f:
                img = UserImage.objects.create(
                    user=self.user,
                    file = File(f)
                )
                self.add_image_for_delete(img)

            img_db_obj = UserImage.objects.get(pk=img.id)
            data = img_db_obj.get_all_urls()

            for thumb in img_db_obj.thumbs.all():
                self.assertIn(thumb.file.name, json.dumps(data))

            self.assertIn(img_db_obj.file.name, json.dumps(data))

    def test_get_all_urls_no_source(self):
        plan = ThumbPlan.objects.create(
            name = 'MULTI_PLAN',
            use_source_img=False
        )

        plan.thumb_rules.set(self.rules)

        ThumbUser.objects.create(
            user = self.user,
            plan = plan
        )

        for img_file in TEST_IMAGES:
            with open(img_file, 'rb') as f:
                img = UserImage.objects.create(
                    user=self.user,
                    file = File(f)
                )
                self.add_image_for_delete(img)

            img_db_obj = UserImage.objects.get(pk=img.id)
            data = img_db_obj.get_all_urls()

            for thumb in img_db_obj.thumbs.all():
                self.assertIn(thumb.file.name, json.dumps(data))

    def test_get_all_urls_no_thumbs(self):
        plan = ThumbPlan.objects.create(
            name = 'NO_THUMBS_PLAN',
            use_source_img=True
        )

        ThumbUser.objects.create(
            user = self.user,
            plan = plan
        )

        for img_file in TEST_IMAGES:
            with open(img_file, 'rb') as f:
                img = UserImage.objects.create(
                    user=self.user,
                    file = File(f)
                )
                self.add_image_for_delete(img)

            img_db_obj = UserImage.objects.get(pk=img.id)
            data = img_db_obj.get_all_urls()

            self.assertIn(img_db_obj.file.name, json.dumps(data))


class TestImageTempLinkModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=f'link_user',
            email=f'link_@test.com'
        )

        plan = ThumbPlan.objects.create(
            name = 'NO_THUMBS_PLAN',
            use_source_img=True
        )

        ThumbUser.objects.create(
            user = self.user,
            plan = plan
        )

        self.image_ids_to_delete = []

        with open(TEST_IMAGES[0], 'rb') as f:
            self.img = UserImage.objects.create(
                user=self.user,
                file = File(f)
            )
        self.image_ids_to_delete.append(self.img.pk)

    def tearDown(self):
        delete_test_files(self.image_ids_to_delete)

    def test_generate_link(self):
        exp = timezone.now() + datetime.timedelta(seconds=settings.TEMP_LINK_MIN_SECONDS)
        link_obj = ImageTempLink.objects.create(
            image=self.img,
            expiration=exp
        )

        link = link_obj.generate_link()
        
        base = link.rsplit('/', 1)[0]
        self.assertEqual(base, '/thumbs/tmp')

        sign = link.split('/')[-1]

        signer = signing.Signer()
        pk = int(signer.unsign(sign))
        self.assertEqual(pk, link_obj.pk)