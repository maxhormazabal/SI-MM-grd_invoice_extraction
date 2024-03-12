from .abstract_engine import AbstractEngine

import logging
import pandas as pd
from sqlalchemy import create_engine

logger = logging.getLogger("infra.timescale")


class TimescaleDBEngine(AbstractEngine):
    def __init__(self, config) -> None:
        super().__init__()
        base_con_str = "postgresql+psycopg2://{}:{}@{}:{}/{}"
        self._connection_string = base_con_str.format(
            config["TIMESCALEDB_USER"],
            config["TIMESCALEDB_PASS"],
            config["TIMESCALESDB_HOST"],
            config["TIMESCALEDB_PORT"],
            config["TIMESCALEDB_DATABASE"],
        )
        logger.info(
            "Connecting to db {} on host {}".format(
                config["TIMESCALEDB_DATABASE"], config["TIMESCALESDB_HOST"]
            )
        )

        self._engine = create_engine(self._connection_string)

    def read(self, sql: str) -> pd.DataFrame:
        logger.info("Running sql: {}".format(sql))
        connection = self._engine.connect()
        result = pd.read_sql_query(sql, connection)
        connection.close()
        return result

    def execute(self, sql: str) -> int:
        logger.info("Running sql: {}".format(sql))
        with self._engine.connect() as connection:
            connection.execute(sql)

    def test_connection(self) -> bool:
        result = self.read("SELECT 1")
        return result.shape[0] == 1

    def write_pd_dataframe(
        self,
        df: pd.DataFrame,
        name: str,
        schema=None,
        if_exists: str = "fail",
        index: bool = True,
        index_label=None,
        chunksize=None,
        dtype=None,
        method=None,
    ) -> None:
        with self._engine.connect() as connection:
            df.to_sql(
                name,
                connection,
                schema,
                if_exists,
                index,
                index_label,
                chunksize,
                dtype,
                method,
            )
