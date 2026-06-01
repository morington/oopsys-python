from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

OOPSYS_LOGGER_NAME = "OOPSYS"


class AgentModel(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=8080, ge=1, le=65535)
    path: str = Field(default="/reports")
    enabled: bool = Field(default=True)
    timeout: float = Field(default=3.0, gt=0)

    def url(self) -> str:
        return f"http://{self.host}:{self.port}{self.path}"


class Settings(BaseSettings):
    is_development: bool = Field(default=False)
    service_name: str = Field(default="app")
    logger_name: str = Field(default=OOPSYS_LOGGER_NAME)
    reraise: bool = Field(default=False)
    agent: AgentModel = AgentModel()

    model_config = SettingsConfigDict(
        env_prefix="OOPSYS_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @property
    def environment(self) -> str:
        return "development" if self.is_development else "production"
