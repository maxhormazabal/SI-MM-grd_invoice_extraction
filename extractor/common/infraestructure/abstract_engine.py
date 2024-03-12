from abc import ABC, abstractmethod
import pandas as pd


class AbstractEngine(ABC):
    @abstractmethod
    def read(sql: str) -> pd.DataFrame:
        """Returns data from the datasource

        Applies the SQL expression on the data source and expects it
        to return a single table with all the results. This funciont
        is good enough when the returned data fits all in memory

        Args:
            sql: SQL expression to apply on the data source

        Returns:
            Dataframe with the result table of aplying the SQL expression

        """
        pass

    @abstractmethod
    def execute(sql: str) -> int:
        """Applies a SQL expression on the Datasource

        Applies the SQL expression on the data source and does not expect
        it to return any value. This function should be used for CREATE,
        INSERT, UPDATE, DELETE,... type of operations which does not return
        a table as result

        Args:
            sql: SQL expression to apply on the data source

        Returns:
            Number of registries affected inside the database

        """
        pass

    @abstractmethod
    def test_connection() -> bool:
        """Tests if current engine has connection to datasource

        Returns:
            True if connected succesfully to the datasource and False otherwise
        """

    @abstractmethod
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
        """Writes a given pandas dataframe into a table database using
        pandas df.to_sql method

        Returns:
            None
        """
