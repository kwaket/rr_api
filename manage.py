#!/var/www/html/rr_applications_api/env/bin/python
import click


@click.command()
@click.option('--deploy',
              is_flag=True,
              help='Deploy database, model state',)
@click.option('--tasker',
              is_flag=True,
              help='Кадастровый номер объекта',)
def manage(deploy, tasker):
    if tasker:
        print('run tasker')

    if deploy:
        from db import SessionLocal
        from services import insert_application_states

        db = SessionLocal()
        insert_application_states(db)
        db.close()


if __name__ == '__main__':
    manage()
