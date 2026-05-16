from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VictoryChain Impact Token API"
    app_env: str = "dev"
    database_url: str = Field(default="sqlite:///./victory_impact.db", alias="DATABASE_URL")
    treasury_widow_wallet: str = "WIDOW_TREASURY_PLACEHOLDER"
    treasury_elder_wallet: str = "ELDER_TREASURY_PLACEHOLDER"
    treasury_orphan_wallet: str = "ORPHAN_TREASURY_PLACEHOLDER"
    treasury_mercy_wallet: str = "MERCY_TREASURY_PLACEHOLDER"
    treasury_earth_wallet: str = "EARTH_TREASURY_PLACEHOLDER"
    legal_review_tax_receipts_enabled: bool = False
    donation_large_amount_usd_threshold: float = 10000.0
    stripe_webhook_secret: str = "set-me"
    vusd_contract_address: str = "0x0000000000000000000000000000000000000000"
    evm_rpc_url: str = "http://localhost:8545"
    evm_required_confirmations: int = 1
    webhook_max_retries: int = 3
    webhook_retry_interval_seconds: int = 300
    webhook_retry_max_delay_seconds: int = 21600
    webhook_retry_jitter_ratio: float = 0.2
    audit_proof_secret: str = "set-me-audit-proof-secret"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    enable_demo_seed_data: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
