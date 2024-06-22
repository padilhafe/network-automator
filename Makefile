shell:
	@python -m pipenv shell

up:
	@python manage.py runserver

migrations:
	@python manage.py makemigrations

migrate:
	@python manage.py migrate

superuser:
	@python manage.py createsuperuser