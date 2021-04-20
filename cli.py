from exts import db
from app import create_app
import click
from models.admin import user_datastore
from flask_security.utils import hash_password
from models.loyalty import Levels


@click.command()
@click.option('--init-db', is_flag=True)
@click.option('--create-superuser', is_flag=True)
def create_roles(init_db, create_superuser):
    app = create_app()

    if init_db:
        try:
            with app.app_context():
                db.drop_all()
            click.secho('Data base dropped.', fg='green')
        except Exception:
            click.secho('Data base drop error', err=True)

        try:
            with app.app_context():
                db.create_all()
            click.secho('Data base created.', fg='green')
        except Exception:
            click.secho('Data base creation error', err=True)

    try:
        with app.app_context():
            user_datastore.create_role(name='superuser')
            user_datastore.create_role(name='manager')
            user_datastore.create_role(name='cashier')
            db.session.commit()
        click.secho('Roles created', fg='green')
    except Exception:
        click.secho('Error while creating roles', err=True)

    try:
        with app.app_context():
            base_level = Levels(name='Base', discount=0, min_balance=0)
            db.session.add(base_level)
            db.session.commit()
        click.secho('Base discount created.', fg='green')
    except Exception:
        click.secho('Error creating base discount', err=True)

    if create_superuser:
        try:
            with app.app_context():
                user = user_datastore.create_user(email='super@test.com',
                                                  password=hash_password('01234567890'))
                user_datastore.add_role_to_user(user, 'superuser')
                db.session.commit()
            click.secho('Superuser created', fg='green')
            click.echo('email: super@test.com, password: 01234567890')
        except Exception:
            click.secho('Error creating superuser', err=True)


if __name__ == '__main__':
    create_roles()