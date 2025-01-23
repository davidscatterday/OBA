import sqlite3
import mysql.connector

sqlite_file = "nycprocurement.db"
sqlite_table = "newtable"
mysql_host = "sql.freedb.tech"
mysql_user = "freedb_davidscatterday"
mysql_password = "KC55*RM*F8ujyfn"
mysql_db_name = "freedb_NYCtest"
mysql_table_name = "newtable"

# 1. Connect to SQLite
sqlite_conn = sqlite3.connect(sqlite_file)
sqlite_cursor = sqlite_conn.cursor()

# 2. Get column names from SQLite
sqlite_cursor.execute(f"PRAGMA table_info({sqlite_table})")
columns_info = sqlite_cursor.fetchall()
column_names = [info[1] for info in columns_info]

# 3. Connect to MySQL
mysql_conn = mysql.connector.connect(
    host=mysql_host,
    user=mysql_user,
    password=mysql_password,
    database=mysql_db_name
)
mysql_cursor = mysql_conn.cursor()

# 4. Drop old table if it exists
drop_table_stmt = f"DROP TABLE IF EXISTS `{mysql_table_name}`"
mysql_cursor.execute(drop_table_stmt)

# 5. Create a new table with appropriate column types
create_cols = ", ".join(f"`{col}` TEXT" for col in column_names)
create_table_stmt = f"""
    CREATE TABLE IF NOT EXISTS `{mysql_table_name}` (
        {create_cols}
    )
"""
mysql_cursor.execute(create_table_stmt)

# 6. Fetch data from SQLite
sqlite_cursor.execute(f"SELECT * FROM {sqlite_table}")
rows = sqlite_cursor.fetchall()

# 7. Insert rows into MySQL
column_list = ", ".join(f"`{col}`" for col in column_names)
placeholders = ", ".join(["%s"] * len(column_names))
insert_stmt = f"INSERT INTO `{mysql_table_name}` ({column_list}) VALUES ({placeholders})"

for row in rows:
    mysql_cursor.execute(insert_stmt, row)

mysql_conn.commit()

# 8. Clean up
sqlite_conn.close()
mysql_cursor.close()
mysql_conn.close()
