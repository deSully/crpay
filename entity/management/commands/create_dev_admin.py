from django.core.management.base import BaseCommand
from entity.models import Entity, AppUser


class Command(BaseCommand):
    help = 'Create default admin user and entity for development'

    def handle(self, *args, **options):
        # Créer une entité par défaut si elle n'existe pas
        entity, created = Entity.objects.get_or_create(
            code='ADMIN_ENTITY',
            defaults={
                'name': 'Administration',
                'entity_type': 'INTERNAL',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Entity "Administration" created successfully')
            )
        else:
            self.stdout.write('Entity "Administration" already exists')

        # Créer l'utilisateur admin s'il n'existe pas
        if not AppUser.objects.filter(username='admin').exists():
            AppUser.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin',
                entity=entity
            )
            self.stdout.write(
                self.style.SUCCESS('Admin user "admin/admin" created successfully')
            )
        else:
            self.stdout.write('Admin user already exists')