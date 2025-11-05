from django.core.management.base import BaseCommand
from django.core.management import call_command
import sys


class Command(BaseCommand):
    help = "Setup complet de l'environnement de développement"

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-fake-data',
            action='store_true',
            help='Ne pas générer de fausses données'
        )
        parser.add_argument(
            '--fake-data-count',
            type=int,
            default=5000,
            help='Nombre de transactions fake à générer (défaut: 5000)'
        )

    def handle(self, *args, **options):
        skip_fake_data = options.get('skip_fake_data')
        fake_data_count = options.get('fake_data_count')

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("🚀 SETUP ENVIRONNEMENT DE DÉVELOPPEMENT"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        # 0. Reset complet
        self.stdout.write(self.style.WARNING("🔄 Étape 0/5 : Reset de l'environnement..."))
        try:
            # Supprimer les crons existants
            try:
                call_command('crontab', 'remove')
                self.stdout.write("   ✓ Cron jobs supprimés")
            except Exception:
                self.stdout.write("   ✓ Aucun cron à supprimer")
            
            # Supprimer la base de données SQLite (dev uniquement)
            import os
            from django.conf import settings
            if settings.DEBUG and 'sqlite3' in settings.DATABASES['default']['ENGINE']:
                db_path = settings.DATABASES['default']['NAME']
                if os.path.exists(db_path):
                    os.remove(db_path)
                    self.stdout.write(f"   ✓ Base de données supprimée ({db_path})")
                else:
                    self.stdout.write("   ✓ Aucune base de données à supprimer")
            else:
                self.stdout.write("   ⚠️  Reset base de données ignoré (PostgreSQL ou production)")
            
            self.stdout.write(self.style.SUCCESS("✅ Reset terminé\n"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur reset: {e}\n"))
            return

        # 1. Migrations
        self.stdout.write(self.style.WARNING("📦 Étape 1/5 : Application des migrations..."))
        try:
            call_command('migrate', '--noinput')
            self.stdout.write(self.style.SUCCESS("✅ Migrations appliquées\n"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur migrations: {e}\n"))
            return

        # 2. Init entity (configurations de base)
        self.stdout.write(self.style.WARNING("🏢 Étape 2/5 : Initialisation des entités..."))
        try:
            call_command('init_entity')
            self.stdout.write(self.style.SUCCESS("✅ Entités initialisées\n"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur init_entity: {e}\n"))
            # Continue quand même

        # 3. Créer admin user
        self.stdout.write(self.style.WARNING("👤 Étape 3/5 : Création de l'utilisateur admin..."))
        try:
            call_command('create_dev_admin')
            self.stdout.write(self.style.SUCCESS("✅ Admin créé (admin@example.com / admin)\n"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur create_dev_admin: {e}\n"))
            # Continue quand même

        # 4. Installer les cron jobs
        self.stdout.write(self.style.WARNING("⏰ Étape 4/5 : Configuration des tâches planifiées..."))
        try:
            call_command('crontab', 'add')
            self.stdout.write(self.style.SUCCESS("✅ Cron jobs installés (sync toutes les 10 min)\n"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Cron non installé: {e}"))
            self.stdout.write(self.style.WARNING("   (Normal si django-crontab n'est pas configuré)\n"))

        # 5. Fake data
        if not skip_fake_data:
            self.stdout.write(self.style.WARNING(f"📊 Étape 5/5 : Génération de {fake_data_count} transactions fake..."))
            
            # Demander confirmation en mode interactif
            if sys.stdin.isatty():
                response = input(f"   Voulez-vous générer {fake_data_count} transactions de test ? (o/N): ").strip().lower()
                if response not in ['o', 'oui', 'y', 'yes']:
                    self.stdout.write(self.style.WARNING("   ⏭️  Génération de fake data ignorée\n"))
                    self._print_summary()
                    return
            
            try:
                call_command('generate_fake_data', '--count', fake_data_count, '--clear')
                self.stdout.write(self.style.SUCCESS(f"✅ {fake_data_count} transactions générées\n"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur generate_fake_data: {e}\n"))
        else:
            self.stdout.write(self.style.WARNING("📊 Étape 5/5 : Génération de fake data (ignorée avec --skip-fake-data)\n"))

        self._print_summary()

    def _print_summary(self):
        """Affiche le résumé final"""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("✅ SETUP TERMINÉ !"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("🎯 Prochaines étapes :"))
        self.stdout.write("")
        self.stdout.write("   1. Lancer le serveur :")
        self.stdout.write(self.style.WARNING("      python manage.py runserver"))
        self.stdout.write("")
        self.stdout.write("   2. Se connecter à l'admin :")
        self.stdout.write(self.style.WARNING("      http://127.0.0.1:8000/admin/"))
        self.stdout.write(self.style.WARNING("      Email    : admin@example.com"))
        self.stdout.write(self.style.WARNING("      Password : admin"))
        self.stdout.write("")
        self.stdout.write("   3. Voir la doc API (Swagger) :")
        self.stdout.write(self.style.WARNING("      http://127.0.0.1:8000/swagger/"))
        self.stdout.write("")
        self.stdout.write("   4. Tester la sync manuelle :")
        self.stdout.write(self.style.WARNING("      python manage.py sync_transaction_status"))
        self.stdout.write("")
        self.stdout.write("   5. Voir les crons installés :")
        self.stdout.write(self.style.WARNING("      python manage.py crontab show"))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
