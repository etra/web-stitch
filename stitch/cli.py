import click
from flask.cli import with_appcontext
from stitch.database import db


def register_commands(app):
    """Register custom CLI commands with Flask app"""
    app.cli.add_command(db_commands)


@click.group()
def db_commands():
    """Database management commands"""
    pass


@db_commands.command('create')
@with_appcontext
def create_db():
    """Create all database tables (uses current models, not migrations)"""
    db.create_all()
    click.echo('✓ Database tables created successfully')


@db_commands.command('drop')
@with_appcontext
def drop_db():
    """Drop all database tables (WARNING: destroys all data)"""
    if click.confirm('Are you sure you want to drop all tables? This will delete all data.'):
        db.drop_all()
        click.echo('✓ Database tables dropped')
    else:
        click.echo('Aborted')


@db_commands.command('reset')
@with_appcontext
def reset_db():
    """Drop and recreate all database tables (WARNING: destroys all data)"""
    if click.confirm('Are you sure you want to reset the database? This will delete all data.'):
        db.drop_all()
        click.echo('✓ Dropped all tables')
        db.create_all()
        click.echo('✓ Created all tables')
        click.echo('✓ Database reset complete')
    else:
        click.echo('Aborted')
