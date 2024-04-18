import os
from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_DATABASE: str
    DB_SCHEMA: str

    def __init__(self):

        load_dotenv(find_dotenv())

        super().__init__() # load all env variables into Config object
        
Config = AppConfig()


