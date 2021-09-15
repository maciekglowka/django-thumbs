from django.core.management import call_command
from django.core.management.base import BaseCommand

from thumbs.models import ThumbPlan, ThumbRule


class Command(BaseCommand):
    def handle(self, *args, **options):
        call_command('makemigrations')
        call_command('migrate')

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
        