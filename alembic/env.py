import asyncio
from logging.config import fileConfig
import os
import sys
# # Set up the path and configuration
# sys.path.append(os.path.join(sys.path[0], '../'))
# print(os.path.join(sys.path[0], './'))

from sqlalchemy import create_engine
from alembic import context

# for alembic
# from core import cfg, setup

# for main server
from core import cfg, setup

asyncio.run(setup())

# for alembic
# from database.connection import metadata
# from middleware.user.model import metadata

# for main server
from middleware.user.models import metadata


config = context.config

section = config.config_ini_section
config.set_section_option(section, "DB_HOST", str(cfg['DB_HOST']))
config.set_section_option(section, "DB_PORT", str(cfg['DB_PORT']))
config.set_section_option(section, "DB_USER", str(cfg['DB_USER']))
config.set_section_option(section, "DB_NAME", str(cfg['DB_NAME']))
config.set_section_option(section, "DB_PASS", str(cfg['DB_PASSWORD']))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata


# Конфигурация синхронного движка
url = config.get_main_option("sqlalchemy.url")
engine = create_engine(url)

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()