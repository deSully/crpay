# 🎓 Plateforme de Gestion Éducation Nationale

Plateforme web centralisée pour la gestion du système éducatif : écoles, enseignants, élèves, et tableaux de bord statistiques pour le ministère.

## 🚀 Fonctionnalités

- Gestion des **établissements scolaires**
- Enregistrement des **enseignants**, multi-affectations par école et matières
- Gestion complète des **élèves**, avec responsables à prévenir
- **Filtres intelligents** par commune, ville, préfecture
- Interface **réactive et moderne** avec Tailwind CSS
- **Graphiques** interactifs : Highcharts, Chart.js
- Interface **sécurisée** avec rôles : ministère, directeur, etc.

## 🛠️ Stack technique

- **Backend** : Django, Django REST Framework
- **Frontend** : Tailwind CSS, Chart.js, Choices.js
- **Base de données** : PostgreSQL (ou SQLite en local)
- **Authentification** : Django User Model étendu

## 🧑‍💻 Installation locale

```bash
git clone <repo-url>
cd <nom-du-dossier>
docker-compose up --build
```