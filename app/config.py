import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT',3306))
    DATABASE_NAME = os.getenv('DATABASE_NAME')

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return (
            f'mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}'
            f'@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.DATABASE_NAME}'
        )