from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    db_name: str
    db_user: str
    db_password: SecretStr
    db_host: str
    db_port: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_host}:{self.db_port}/{self.db_name}"


class JWTSettings(BaseSettings):
    jwt_secret_key: SecretStr
    jwt_algorithm: str
    access_token_expire_min: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")


class RedisSettings(BaseSettings):
    redis_pass: SecretStr
    redis_host: str
    redis_port: int
    redis_db: int
    celery_db: int
    celery_back_db: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")

    @property
    def redis_url(self):
        return f"redis://:{self.redis_pass.get_secret_value()}@{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def celery_url(self):
        return f"redis://:{self.redis_pass.get_secret_value()}@{self.redis_host}:{self.redis_port}/{self.celery_db}"

    @property
    def celery_back_url(self):
        return f"redis://:{self.redis_pass.get_secret_value()}@{self.redis_host}:{self.redis_port}/{self.celery_back_db}"


class S3Settings(BaseSettings):
    access_key: str
    secret_key: SecretStr
    endpoint_url: str
    bucket1: str
    bucket2: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")


class EmailSettings(BaseSettings):
    email_host: str
    email_port: int
    email_username: str
    email_password: SecretStr

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")


class Settings(BaseSettings):
    db_settings: DBSettings = DBSettings()
    jwt_settings: JWTSettings = JWTSettings()
    redis_settings: RedisSettings = RedisSettings()
    s3_settings: S3Settings = S3Settings()
    email_settings: EmailSettings = EmailSettings()

    default_avatar_url: str
    frontend_url: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")


settings = Settings()
