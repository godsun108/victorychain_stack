-- Victory Foundation for Restoration + Sacred Earth Restoration Alliance
-- Nonprofit impact-token MVP schema

CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  wallet_address TEXT,
  full_name TEXT,
  role TEXT NOT NULL DEFAULT 'donor',
  kyc_level TEXT NOT NULL DEFAULT 'none',
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE donors (
  id TEXT PRIMARY KEY,
  user_id TEXT UNIQUE NOT NULL,
  donor_reference TEXT UNIQUE NOT NULL,
  communication_opt_in BOOLEAN NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE donation_categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  treasury_wallet TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE treasury_accounts (
  id TEXT PRIMARY KEY,
  category_id INTEGER UNIQUE NOT NULL,
  steward_entity TEXT NOT NULL,
  account_reference TEXT NOT NULL,
  reserve_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL,
  FOREIGN KEY(category_id) REFERENCES donation_categories(id)
);

CREATE TABLE programs (
  id TEXT PRIMARY KEY,
  category_id INTEGER NOT NULL,
  project_id TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  operating_entity TEXT NOT NULL,
  public_summary TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(category_id) REFERENCES donation_categories(id)
);

CREATE TABLE donations (
  id TEXT PRIMARY KEY,
  donor_id TEXT NOT NULL,
  donor_user_id TEXT NOT NULL,
  category_id INTEGER NOT NULL,
  amount NUMERIC(18,2) NOT NULL,
  currency TEXT NOT NULL,
  payment_method TEXT NOT NULL,
  payment_reference TEXT,
  tx_hash TEXT,
  compliance_status TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(donor_id) REFERENCES donors(id),
  FOREIGN KEY(donor_user_id) REFERENCES users(id),
  FOREIGN KEY(category_id) REFERENCES donation_categories(id)
);

CREATE TABLE impact_tokens (
  id TEXT PRIMARY KEY,
  donation_id TEXT NOT NULL,
  owner_user_id TEXT NOT NULL,
  token_contract TEXT NOT NULL,
  token_standard TEXT NOT NULL,
  token_id_onchain TEXT NOT NULL,
  non_transferable BOOLEAN NOT NULL,
  metadata_uri TEXT,
  metadata_json JSON NOT NULL,
  minted_at TIMESTAMP NOT NULL,
  FOREIGN KEY(donation_id) REFERENCES donations(id),
  FOREIGN KEY(owner_user_id) REFERENCES users(id)
);

CREATE TABLE beneficiaries (
  id TEXT PRIMARY KEY,
  category_id INTEGER NOT NULL,
  reference_code TEXT UNIQUE NOT NULL,
  verification_status TEXT NOT NULL,
  needs_assessment TEXT NOT NULL,
  private_profile_json JSON NOT NULL,
  public_summary TEXT NOT NULL,
  operating_entity TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(category_id) REFERENCES donation_categories(id)
);

CREATE TABLE beneficiary_requests (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT NOT NULL,
  program_id TEXT,
  requested_aid_amount NUMERIC(18,2) NOT NULL,
  requested_currency TEXT NOT NULL,
  request_reason TEXT NOT NULL,
  status TEXT NOT NULL,
  approved_amount NUMERIC(18,2),
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(beneficiary_id) REFERENCES beneficiaries(id),
  FOREIGN KEY(program_id) REFERENCES programs(id)
);

CREATE TABLE disbursements (
  id TEXT PRIMARY KEY,
  beneficiary_request_id TEXT NOT NULL,
  program_id TEXT,
  category_id INTEGER NOT NULL,
  amount NUMERIC(18,2) NOT NULL,
  currency TEXT NOT NULL,
  treasury_wallet TEXT NOT NULL,
  destination_reference TEXT NOT NULL,
  disbursement_status TEXT NOT NULL,
  tx_hash TEXT,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(beneficiary_request_id) REFERENCES beneficiary_requests(id),
  FOREIGN KEY(program_id) REFERENCES programs(id),
  FOREIGN KEY(category_id) REFERENCES donation_categories(id)
);

CREATE TABLE receipts (
  id TEXT PRIMARY KEY,
  donation_id TEXT,
  disbursement_id TEXT,
  receipt_number TEXT UNIQUE NOT NULL,
  legal_text_version TEXT NOT NULL,
  tax_receipt_eligible BOOLEAN NOT NULL,
  issued_at TIMESTAMP NOT NULL,
  FOREIGN KEY(donation_id) REFERENCES donations(id),
  FOREIGN KEY(disbursement_id) REFERENCES disbursements(id)
);

CREATE TABLE donor_votes (
  id TEXT PRIMARY KEY,
  voter_user_id TEXT NOT NULL,
  donor_id TEXT,
  project_id TEXT NOT NULL,
  category_id INTEGER NOT NULL,
  token_weight REAL NOT NULL,
  signal TEXT NOT NULL,
  advisory_only BOOLEAN NOT NULL,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(voter_user_id) REFERENCES users(id),
  FOREIGN KEY(donor_id) REFERENCES donors(id),
  FOREIGN KEY(category_id) REFERENCES donation_categories(id)
);

CREATE TABLE compliance_reviews (
  id TEXT PRIMARY KEY,
  subject_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  review_type TEXT NOT NULL,
  status TEXT NOT NULL,
  findings TEXT NOT NULL,
  reviewed_by_user_id TEXT,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(reviewed_by_user_id) REFERENCES users(id)
);

CREATE TABLE audit_logs (
  id TEXT PRIMARY KEY,
  actor_user_id TEXT,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  metadata_json JSON NOT NULL,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(actor_user_id) REFERENCES users(id)
);

CREATE TABLE public_impact_updates (
  id TEXT PRIMARY KEY,
  category_id INTEGER NOT NULL,
  program_id TEXT,
  disbursement_id TEXT,
  title TEXT NOT NULL,
  anonymized_summary TEXT NOT NULL,
  media_links_json JSON NOT NULL,
  published_at TIMESTAMP NOT NULL,
  FOREIGN KEY(category_id) REFERENCES donation_categories(id),
  FOREIGN KEY(program_id) REFERENCES programs(id),
  FOREIGN KEY(disbursement_id) REFERENCES disbursements(id)
);

CREATE TABLE webhook_events (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  provider_event_id TEXT NOT NULL,
  event_type TEXT,
  payload_json JSON NOT NULL,
  delivery_count INTEGER NOT NULL DEFAULT 1,
  first_seen_at TIMESTAMP NOT NULL,
  last_seen_at TIMESTAMP NOT NULL,
  processed BOOLEAN NOT NULL DEFAULT 0,
  processing_status TEXT NOT NULL DEFAULT 'received',
  retry_count INTEGER NOT NULL DEFAULT 0,
  max_retries INTEGER NOT NULL DEFAULT 3,
  last_error TEXT,
  next_retry_at TIMESTAMP,
  processed_at TIMESTAMP,
  dead_lettered_at TIMESTAMP,
  remediation_owner_user_id TEXT,
  remediation_status TEXT NOT NULL DEFAULT 'none',
  remediation_notes TEXT,
  remediated_at TIMESTAMP,
  updated_at TIMESTAMP NOT NULL,
  UNIQUE(provider, provider_event_id),
  FOREIGN KEY(remediation_owner_user_id) REFERENCES users(id)
);
