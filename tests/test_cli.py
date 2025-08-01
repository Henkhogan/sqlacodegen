from __future__ import annotations

import sqlite3
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest

future_imports = "from __future__ import annotations\n\n"


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    with sqlite3.connect(str(path)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE foo (id INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL)"
        )

    return path


def test_cli_tables(db_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "outfile"
    subprocess.run(
        [
            "sqlacodegen",
            f"sqlite:///{db_path}",
            "--generator",
            "tables",
            "--outfile",
            str(output_path),
        ],
        check=True,
    )

    assert (
        output_path.read_text()
        == """\
from sqlalchemy import Column, Integer, MetaData, Table, Text

metadata = MetaData()


t_foo = Table(
    'foo', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', Text, nullable=False)
)
"""
    )


def test_cli_declarative(db_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "outfile"
    subprocess.run(
        [
            "sqlacodegen",
            f"sqlite:///{db_path}",
            "--generator",
            "declarative",
            "--outfile",
            str(output_path),
        ],
        check=True,
    )

    assert (
        output_path.read_text()
        == """\
from sqlalchemy import Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class Foo(Base):
    __tablename__ = 'foo'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
"""
    )


def test_cli_dataclass(db_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "outfile"
    subprocess.run(
        [
            "sqlacodegen",
            f"sqlite:///{db_path}",
            "--generator",
            "dataclasses",
            "--outfile",
            str(output_path),
        ],
        check=True,
    )

    assert (
        output_path.read_text()
        == """\
from sqlalchemy import Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

class Base(MappedAsDataclass, DeclarativeBase):
    pass


class Foo(Base):
    __tablename__ = 'foo'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
"""
    )


def test_cli_sqlmodels(db_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "outfile"
    subprocess.run(
        [
            "sqlacodegen",
            f"sqlite:///{db_path}",
            "--generator",
            "sqlmodels",
            "--outfile",
            str(output_path),
        ],
        check=True,
    )

    assert (
        output_path.read_text()
        == """\
from sqlalchemy import Column, Integer, Text
from sqlmodel import Field, SQLModel

class Foo(SQLModel, table=True):
    id: int = Field(sa_column=Column('id', Integer, primary_key=True))
    name: str = Field(sa_column=Column('name', Text))
"""
    )


def test_cli_engine_arg(db_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "outfile"
    subprocess.run(
        [
            "sqlacodegen",
            f"sqlite:///{db_path}",
            "--generator",
            "tables",
            "--engine-arg",
            'connect_args={"timeout": 10}',
            "--outfile",
            str(output_path),
        ],
        check=True,
    )

    assert (
        output_path.read_text()
        == """\
from sqlalchemy import Column, Integer, MetaData, Table, Text

metadata = MetaData()


t_foo = Table(
    'foo', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', Text, nullable=False)
)
"""
    )


def test_cli_invalid_engine_arg(db_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "outfile"

    # Expect exception:
    # TypeError: 'this_arg_does_not_exist' is an invalid keyword argument for Connection()
    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        subprocess.run(
            [
                "sqlacodegen",
                f"sqlite:///{db_path}",
                "--generator",
                "tables",
                "--engine-arg",
                'connect_args={"this_arg_does_not_exist": 10}',
                "--outfile",
                str(output_path),
            ],
            check=True,
            capture_output=True,
        )

    if sys.version_info < (3, 13):
        assert (
            "'this_arg_does_not_exist' is an invalid keyword argument"
            in exc_info.value.stderr.decode()
        )
    else:
        assert (
            "got an unexpected keyword argument 'this_arg_does_not_exist'"
            in exc_info.value.stderr.decode()
        )


def test_main() -> None:
    expected_version = version("sqlacodegen")
    completed = subprocess.run(
        [sys.executable, "-m", "sqlacodegen", "--version"],
        stdout=subprocess.PIPE,
        check=True,
    )
    assert completed.stdout.decode().strip() == expected_version
