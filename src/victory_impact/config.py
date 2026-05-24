from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VictoryChain Impact Token API"
    app_env: str = "dev"
    sovereign_mode: bool = True
    inhouse_only_mode: bool = True
    enable_external_stripe_webhooks: bool = False
    enable_external_walletconnect: bool = False
    public_web_mode: bool = False
    enforce_internal_endpoints_in_sovereign_mode: bool = True
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
    evm_rpc_fallback_urls: str = ""
    evm_required_confirmations: int = 1
    vusd_token_decimals: int = 18
    inhouse_payment_gateway_base_url: str = "https://payments.local"
    inhouse_checkout_app_base_url: str = ""
    inhouse_payment_intent_ttl_seconds: int = 1800
    delivery_supported_providers: str = "instacart,doordash,uber_eats,grubhub,shipt,generic"
    delivery_webhook_token: str = ""
    delivery_auto_verify_settlement_tx: bool = True
    delivery_provider_api_timeout_seconds: int = 15
    delivery_instacart_base_url: str = ""
    delivery_instacart_api_key: str = ""
    delivery_doordash_base_url: str = ""
    delivery_doordash_api_key: str = ""
    delivery_uber_eats_base_url: str = ""
    delivery_uber_eats_api_key: str = ""
    delivery_grubhub_base_url: str = ""
    delivery_grubhub_api_key: str = ""
    delivery_shipt_base_url: str = ""
    delivery_shipt_api_key: str = ""
    webhook_max_retries: int = 3
    webhook_retry_interval_seconds: int = 300
    webhook_retry_max_delay_seconds: int = 21600
    webhook_retry_jitter_ratio: float = 0.2
    slo_window_hours: int = 24
    slo_vusd_failed_rejected_ratio_threshold: float = 0.05
    slo_vusd_pending_ratio_threshold: float = 0.10
    slo_webhook_retry_queue_depth_threshold: int = 25
    slo_webhook_dead_letter_threshold: int = 5
    slo_retry_success_rate_threshold: float = 0.70
    slo_control_retry_hours_back: int = 24
    slo_control_retry_batch_limit: int = 300
    audit_proof_secret: str = "set-me-audit-proof-secret"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    enable_demo_seed_data: bool = True
    public_auth_nonce_ttl_seconds: int = 300
    public_wallet_session_ttl_seconds: int = 3600
    public_wallet_max_active_sessions: int = 5
    public_auth_default_chain_id: int = 1
    public_auth_allowed_chain_ids: str = "1,8453,137,1337"
    public_auth_default_statement: str = "Sign in to VictoryChain to access wallet-linked public services."
    public_auth_domain: str = "localhost"
    public_auth_uri: str = "http://localhost"
    public_pull_phrase_min_len: int = 3
    public_pull_phrase_max_len: int = 64
    wallet_photo_max_bytes: int = 4 * 1024 * 1024
    wallet_photo_max_items_per_wallet: int = 200
    wallet_photo_library_limit: int = 100
    admin_session_ttl_seconds: int = 3600
    admin_session_rotate_before_expiry_seconds: int = 600
    admin_session_max_active_per_role: int = 5
    admin_bootstrap_enabled: bool = False
    admin_bootstrap_tokens: str = ""
    admin_bootstrap_allowed_roles: str = "admin,board,compliance"
    admin_allow_legacy_api_tokens: bool = False
    admin_legacy_api_tokens: str = ""
    public_rate_limit_window_seconds: int = 60
    public_rate_limit_max_requests: int = 120
    trust_proxy_headers: bool = False
    trusted_proxy_cidrs: str = "127.0.0.1/32,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    sanctions_screening_provider: str = "local_rules"
    sanctions_blocked_wallets: str = ""
    sanctions_blocked_terms: str = ""
    pegasus_enabled: bool = True
    pegasus_kill_switch: bool = False
    pegasus_require_trusted_signal: bool = True
    pegasus_enabled_event_keys: str = (
        "social.post_published,"
        "games.session_played,"
        "chat.friend_message_sent,"
        "stream.movie_watch_verified,"
        "wallet.vusd_p2p_transfer_verified,"
        "wallet.vcn_domain_setup,"
        "wallet.email_setup_verified"
    )
    pegasus_max_events_5min: int = 40
    pegasus_max_rejected_1h: int = 30
    pegasus_trusted_signal_ttl_hours: int = 168
    pegasus_cross_actor_source_ref_block: bool = True
    iso20022_schema_root: str = ""
    iso20022_require_schema: bool = True
    iso20022_enable_institutional_profile: bool = True
    iso20022_institutional_profile_path: str = ""
    iso20022_require_external_schema_pack: bool = False
    victorychain_iso20022_onchain_enabled: bool = True
    victorychain_require_iso20022_onchain: bool = False
    victorychain_iso20022_onchain_log_path: str = ""
    victorychain_iso20022_bizsvc: str = "victorychain.vusd.fednow.01"
    victorychain_iso20022_default_currency: str = "USD"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
