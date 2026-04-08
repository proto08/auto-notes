from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MySQL
    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_database: str
    mysql_user: str
    mysql_password: str

    # RabbitMQ
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_default_user: str = "guest"
    rabbitmq_default_pass: str = "guest"
    rabbitmq_use_tls: bool = False

    # Celery
    celery_broker_url: str
    celery_result_backend: str

    # App
    tz: str = "Asia/Tokyo"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


settings = Settings()
