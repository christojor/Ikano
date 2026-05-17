-- 3NF schema for adaptive onboarding flow (Sweden/Spain/Poland, private/business)
-- Target: PostgreSQL 16+

BEGIN;

-- Lookup tables
CREATE TABLE country (
    country_code CHAR(2) PRIMARY KEY,
    country_name VARCHAR(64) NOT NULL UNIQUE
);

CREATE TABLE party_type (
    party_type_code VARCHAR(16) PRIMARY KEY,
    description VARCHAR(64) NOT NULL UNIQUE
);

CREATE TABLE application_status (
    application_status_code VARCHAR(24) PRIMARY KEY,
    description VARCHAR(96) NOT NULL UNIQUE
);

CREATE TABLE step_status (
    step_status_code VARCHAR(24) PRIMARY KEY,
    description VARCHAR(96) NOT NULL UNIQUE
);

CREATE TABLE check_type (
    check_type_code VARCHAR(24) PRIMARY KEY,
    description VARCHAR(96) NOT NULL UNIQUE
);

CREATE TABLE check_business_result (
    check_business_result_code VARCHAR(24) PRIMARY KEY,
    description VARCHAR(96) NOT NULL UNIQUE
);

CREATE TABLE decision_outcome (
    decision_outcome_code VARCHAR(24) PRIMARY KEY,
    description VARCHAR(96) NOT NULL UNIQUE
);

-- Core flow definition
CREATE TABLE onboarding_flow (
    flow_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_code CHAR(2) NOT NULL REFERENCES country(country_code),
    party_type_code VARCHAR(16) NOT NULL REFERENCES party_type(party_type_code),
    flow_name VARCHAR(120) NOT NULL,
    flow_version INTEGER NOT NULL CHECK (flow_version > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (country_code, party_type_code, flow_version)
);

CREATE TABLE onboarding_step (
    step_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flow_id BIGINT NOT NULL REFERENCES onboarding_flow(flow_id),
    step_code VARCHAR(32) NOT NULL,
    step_title VARCHAR(120) NOT NULL,
    step_order INTEGER NOT NULL CHECK (step_order > 0),
    is_terminal BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (flow_id, step_code),
    UNIQUE (flow_id, step_order)
);

-- Application aggregate
CREATE TABLE application (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_reference VARCHAR(40) NOT NULL UNIQUE,
    country_code CHAR(2) NOT NULL REFERENCES country(country_code),
    party_type_code VARCHAR(16) NOT NULL REFERENCES party_type(party_type_code),
    flow_id BIGINT NOT NULL REFERENCES onboarding_flow(flow_id),
    application_status_code VARCHAR(24) NOT NULL REFERENCES application_status(application_status_code),
    current_step_id BIGINT NULL REFERENCES onboarding_step(step_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMPTZ NULL
);

CREATE TABLE applicant_party (
    party_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL REFERENCES application(application_id),
    party_role VARCHAR(24) NOT NULL,
    email VARCHAR(320) NULL,
    phone_e164 VARCHAR(32) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (application_id, party_role)
);

CREATE TABLE person_profile (
    person_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    party_id BIGINT NOT NULL UNIQUE REFERENCES applicant_party(party_id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    national_id_value VARCHAR(80) NULL,
    nationality_country_code CHAR(2) NULL REFERENCES country(country_code)
);

CREATE TABLE business_profile (
    business_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    party_id BIGINT NOT NULL UNIQUE REFERENCES applicant_party(party_id),
    legal_name VARCHAR(180) NOT NULL,
    registration_number VARCHAR(80) NOT NULL,
    tax_number VARCHAR(80) NULL,
    incorporation_country_code CHAR(2) NOT NULL REFERENCES country(country_code),
    UNIQUE (incorporation_country_code, registration_number)
);

CREATE TABLE address (
    address_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    line1 VARCHAR(180) NOT NULL,
    line2 VARCHAR(180) NULL,
    postal_code VARCHAR(24) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country_code CHAR(2) NOT NULL REFERENCES country(country_code)
);

CREATE TABLE party_address (
    party_id BIGINT NOT NULL REFERENCES applicant_party(party_id),
    address_id BIGINT NOT NULL REFERENCES address(address_id),
    address_type VARCHAR(24) NOT NULL,
    PRIMARY KEY (party_id, address_id, address_type)
);

CREATE TABLE application_step_state (
    application_id BIGINT NOT NULL REFERENCES application(application_id),
    step_id BIGINT NOT NULL REFERENCES onboarding_step(step_id),
    step_status_code VARCHAR(24) NOT NULL REFERENCES step_status(step_status_code),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ NULL,
    payload_json JSONB NULL,
    error_code VARCHAR(64) NULL,
    PRIMARY KEY (application_id, step_id)
);

-- External checks (KYC, KYB, sanctions, credit, registry)
CREATE TABLE external_provider (
    provider_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    provider_code VARCHAR(32) NOT NULL UNIQUE,
    check_type_code VARCHAR(24) NOT NULL REFERENCES check_type(check_type_code),
    provider_name VARCHAR(120) NOT NULL
);

CREATE TABLE check_run (
    check_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL REFERENCES application(application_id),
    party_id BIGINT NULL REFERENCES applicant_party(party_id),
    check_type_code VARCHAR(24) NOT NULL REFERENCES check_type(check_type_code),
    provider_id BIGINT NOT NULL REFERENCES external_provider(provider_id),
    correlation_id VARCHAR(80) NOT NULL,
    input_fingerprint VARCHAR(128) NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ NULL,
    technical_status VARCHAR(24) NOT NULL,
    check_business_result_code VARCHAR(24) NOT NULL REFERENCES check_business_result(check_business_result_code),
    response_summary_json JSONB NULL
);

-- Decisioning and explainability
CREATE TABLE decision_rule_set (
    rule_set_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rule_set_name VARCHAR(80) NOT NULL,
    rule_set_version INTEGER NOT NULL CHECK (rule_set_version > 0),
    active_from TIMESTAMPTZ NOT NULL,
    active_to TIMESTAMPTZ NULL,
    UNIQUE (rule_set_name, rule_set_version)
);

CREATE TABLE decision_reason (
    reason_code VARCHAR(40) PRIMARY KEY,
    reason_description VARCHAR(180) NOT NULL,
    severity VARCHAR(16) NOT NULL
);

CREATE TABLE application_decision (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL UNIQUE REFERENCES application(application_id),
    rule_set_id BIGINT NOT NULL REFERENCES decision_rule_set(rule_set_id),
    decision_outcome_code VARCHAR(24) NOT NULL REFERENCES decision_outcome(decision_outcome_code),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decided_by VARCHAR(80) NOT NULL,
    rationale_json JSONB NULL
);

CREATE TABLE application_decision_reason (
    decision_id BIGINT NOT NULL REFERENCES application_decision(decision_id),
    reason_code VARCHAR(40) NOT NULL REFERENCES decision_reason(reason_code),
    rank_order INTEGER NOT NULL CHECK (rank_order > 0),
    reason_details VARCHAR(220) NULL,
    PRIMARY KEY (decision_id, reason_code)
);

CREATE TABLE manual_review_case (
    manual_review_case_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL UNIQUE REFERENCES application(application_id),
    review_status VARCHAR(24) NOT NULL,
    assigned_to VARCHAR(120) NULL,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ NULL,
    resolution_notes VARCHAR(1000) NULL
);

-- Immutable audit trail
CREATE TABLE audit_event (
    audit_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id BIGINT NOT NULL REFERENCES application(application_id),
    party_id BIGINT NULL REFERENCES applicant_party(party_id),
    actor_type VARCHAR(24) NOT NULL,
    actor_id VARCHAR(120) NOT NULL,
    event_type VARCHAR(48) NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id VARCHAR(80) NULL,
    metadata_json JSONB NULL,
    prev_event_hash VARCHAR(128) NULL,
    event_hash VARCHAR(128) NOT NULL
);

-- Helpful indexes for expected read paths
CREATE INDEX idx_application_status ON application(application_status_code);
CREATE INDEX idx_application_created_at ON application(created_at);
CREATE INDEX idx_step_state_status ON application_step_state(step_status_code);
CREATE INDEX idx_check_run_app_type ON check_run(application_id, check_type_code);
CREATE INDEX idx_check_run_party ON check_run(party_id);
CREATE INDEX idx_audit_event_app_ts ON audit_event(application_id, event_timestamp);
CREATE INDEX idx_audit_event_correlation ON audit_event(correlation_id);

-- Minimal seed data for required countries and parties
INSERT INTO country (country_code, country_name)
VALUES
    ('SE', 'Sweden'),
    ('ES', 'Spain'),
    ('PL', 'Poland');

INSERT INTO party_type (party_type_code, description)
VALUES
    ('PRIVATE', 'Private individual'),
    ('BUSINESS', 'Business customer');

INSERT INTO check_type (check_type_code, description)
VALUES
    ('KYC', 'Know Your Customer'),
    ('KYB', 'Know Your Business'),
    ('SANCTIONS', 'Sanctions screening'),
    ('CREDIT', 'Credit bureau check'),
    ('REGISTRY', 'Business registry check');

INSERT INTO check_business_result (check_business_result_code, description)
VALUES
    ('PASS', 'Automated pass'),
    ('MANUAL_REVIEW', 'Requires manual review'),
    ('FAIL', 'Automated fail');

INSERT INTO decision_outcome (decision_outcome_code, description)
VALUES
    ('APPROVED', 'Approved automatically'),
    ('MANUAL_REVIEW', 'Manual review required'),
    ('REJECTED', 'Rejected');

COMMIT;
