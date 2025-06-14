# pylimer-predictor-website
Website showcasing predictive power of pylimer-tools and other results from my PhD

Some useful commands:

```bash
python manage.py runserver # run the dev server

python manage.py makemigrations
python manage.py migrate

```

To create a user:

```bash

python manage.py createsuperuser --email admin@example.com --username admin

```

To add the relevant permissions:

```bash
python manage.py shell -c "from pylimerpredictor.models.user import User; user = User.objects.get(username='admin'); user.role = 'admin'; user.save(); print(f'User {user.username} role updated to: {user.role}')"
```
