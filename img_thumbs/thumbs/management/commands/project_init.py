import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key

from thumbs.models import ThumbPlan, ThumbRule


class Command(BaseCommand):
    def handle(self, *args, **options):
        #start db
        call_command('makemigrations')
        call_command('migrate')
        call_command('collectstatic', '--noinput')

        #create secret key
        path = os.path.join(settings.BASE_DIR, '.env')

        with open(path, 'a+') as f:
            f.seek(0)
            if not [line for line in f if line.startswith('SECRET_KEY')]:
                f.write(f'\nSECRET_KEY={get_random_secret_key()}')
                print('created SECRET_KEY variable')


        #create rules for 200px and 400px
        rules = {}

        for h in [200,400]:
            q = ThumbRule.objects.filter(height=h)
            if q.exists():
                rules[h] = q.first()
                continue
            rule = ThumbRule.objects.create(
                height = h
            )
            rules[h] = rule
            print(f'created {h}px rule')

        #create plans
        if not ThumbPlan.objects.filter(name='Basic').exists():
            basic_plan = ThumbPlan.objects.create(
                name='Basic',
                use_source_img=False,
                use_expiring_links=False
            )
            basic_plan.thumb_rules.set([rules[200]])
            print('created Basic plan')

        if not ThumbPlan.objects.filter(name='Premium').exists():
            premium_plan = ThumbPlan.objects.create(
                name='Premium',
                use_source_img=True,
                use_expiring_links=False
            )
            premium_plan.thumb_rules.set([rules[200],rules[400]])
            print('created Premium plan')

        if not ThumbPlan.objects.filter(name='Enterprise').exists():
            enterprise_plan = ThumbPlan.objects.create(
                name='Enterprise',
                use_source_img=True,
                use_expiring_links=True
            )
            enterprise_plan.thumb_rules.set([rules[200],rules[400]])
            print('created Enterprise plan')
        