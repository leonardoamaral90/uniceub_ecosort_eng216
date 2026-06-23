from __future__ import annotations

import duckdb

from ecosort.config import get_settings


def inspect() -> None:
    settings = get_settings()
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        tables = con.execute("show tables").fetchall()
        print("Tabelas DuckDB:")
        for (table,) in tables:
            print(f"- {table}")
            print(con.execute(f"select * from {table} limit 5").fetchdf())
    finally:
        con.close()


if __name__ == "__main__":
    inspect()
