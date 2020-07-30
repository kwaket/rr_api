#!/var/www/html/rr_applications_api/env/bin/python
import click


@click.group()
def cli():
    pass

@click.command()
def runserver():
    click.echo('Run server at 127.0.0.1:8000')
    import uvicorn
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, log_level="info")


@click.command()
def tasker():
    click.echo('Run tasker')


@click.command()
def deploy():
    from app.db import SessionLocal
    from services import insert_application_states

    db = SessionLocal()
    insert_application_states(db)
    db.close()


cli.add_command(runserver)
cli.add_command(tasker)
cli.add_command(deploy)


if __name__ == '__main__':
    cli()
