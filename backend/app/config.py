# from pydantic_settings import BaseSettings
# from pydantic import Field

# class Settings(BaseSettings):
#     """Application settings with environment variable support."""

#     # Application
#     app_name: str = Field(default="FastAPI Backend", env="APP_NAME")
#     debug: bool = Field(default=False, env="DEBUG")
#     version: str = Field(default="1.0.0", env="VERSION")
#     api_port: int = Field(default=8000, env="API_PORT")

#     # Database
#     mysql_host: str = Field(default="localhost", env="MYSQL_HOST")
#     mysql_port: int = Field(default=3306, env="MYSQL_PORT")
#     mysql_user: str = Field(default="root", env="MYSQL_USER")
#     mysql_password: str = Field(default="password", env="MYSQL_PASSWORD")
#     mysql_database: str = Field(default="fastapi_backend", env="MYSQL_DATABASE")

#     # JWT Configuration
#     jwt_secret_key: str = Field(default="your-super-secret-jwt-key-change-in-production", env="JWT_SECRET_KEY")
#     jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
#     access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
#     refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

#     # Security
#     bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")

#     # -------------------------------------------------------
#     # 🌐 Azure AD Integration
#     # -------------------------------------------------------
#     azure_ad_tenant_id: str = Field(..., env="AZURE_AD_TENANT_ID")
#     azure_ad_client_id: str = Field(..., env="AZURE_AD_CLIENT_ID")
#     azure_ad_client_secret: str = Field(..., env="AZURE_AD_CLIENT_SECRET")
#     azure_ad_redirect_uri: str = Field(..., env="AZURE_AD_REDIRECT_URI")
#     azure_ad_authority: str = Field(default="", env="AZURE_AD_AUTHORITY")
#     azure_ad_token_url: str = Field(default="", env="AZURE_AD_TOKEN_URL")
#     azure_ad_jwks_url: str = Field(default="", env="AZURE_AD_JWKS_URL")
#     azure_ad_scope: str = Field(default="openid profile email offline_access", env="AZURE_AD_SCOPE")

#     # -------------------------------------------------------
#     # API Configuration
#     # -------------------------------------------------------
#     api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
#     cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")

#     # Rate Limiting
#     rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
#     rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")

#     # Pagination
#     default_page_size: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
#     max_page_size: int = Field(default=100, env="MAX_PAGE_SIZE")

#     @property
#     def database_url(self) -> str:
#         """Construct database URL for aiomysql."""
#         return f"mysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"

#     class Config:
#         env_file = ".env"
#         case_sensitive = False


# settings = Settings()


# app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="FastAPI Backend", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    version: str = Field(default="1.0.0", env="VERSION")
    api_port: int = Field(default=8000, env="API_PORT")

    # Database
    mysql_host: str = Field(default="localhost", env="MYSQL_HOST")
    mysql_port: int = Field(default=3306, env="MYSQL_PORT")
    mysql_user: str = Field(default="root", env="MYSQL_USER")
    mysql_password: str = Field(default="password", env="MYSQL_PASSWORD")
    mysql_database: str = Field(default="fastapi_backend", env="MYSQL_DATABASE")

    # JWT
    jwt_secret_key: str = Field(default="super-secret-jwt-key", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_days: int = Field(default=1, env="ACCESS_TOKEN_EXPIRE_DAYS")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # Azure AD (core fields)
    azure_ad_tenant_id: str = Field(default="", env="AZURE_AD_TENANT_ID")
    azure_ad_client_id: str = Field(default="", env="AZURE_AD_CLIENT_ID")
    azure_ad_client_secret: Optional[str] = Field(default=None, env="AZURE_AD_CLIENT_SECRET")
    azure_ad_redirect_uri: str = Field(default="http://localhost:8001/api/v1/auth/azure/callback/", env="AZURE_AD_REDIRECT_URI")
    azure_ad_scope: str = Field(default="openid profile email offline_access", env="AZURE_AD_SCOPE")

    # API config
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")

    # Pagination / rate limiting
    default_page_size: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, env="MAX_PAGE_SIZE")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")

    # computed / derived props (no field names collide)
    @property
    def database_url(self) -> str:
        return f"mysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    # @property
    # def database_url_timesheet(self) -> str:
    #     return f"mysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/timesheet_db"

    @property
    def azure_ad_authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.azure_ad_tenant_id}"

    @property
    def azure_ad_token_url(self) -> str:
        return f"{self.azure_ad_authority}/oauth2/v2.0/token"

    @property
    def azure_ad_jwks_url(self) -> str:
        return f"{self.azure_ad_authority}/discovery/v2.0/keys"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
