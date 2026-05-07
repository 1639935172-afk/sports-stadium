import os


if os.getenv('DB_ENGINE', 'sqlite').lower() == 'mysql':
    try:
        import pymysql
    except ImportError:
        pass
    else:
        pymysql.install_as_MySQLdb()
