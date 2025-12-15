import pandas as pd
from sqlalchemy import create_engine

conn_str = (
    "mssql+pyodbc://sa:StrongPassword123!@localhost:1433/sdud"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&TrustServerCertificate=yes"
)

engine = create_engine(conn_str)

query = """
SELECT TOP 10000 *
FROM dbo.sdud_silver
"""

df = pd.read_sql(query, engine)
print(df.head())
print(df.info())