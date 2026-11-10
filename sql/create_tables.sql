CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    datetime_transaction TIMESTAMP NOT NULL,
    iban_origine VARCHAR(34) NOT NULL,
    pays_source TEXT NOT NULL,
    banque_source TEXT NOT NULL,
    iban_destinataire VARCHAR(34) NOT NULL,
    pays_destinataire TEXT NOT NULL,
    montant NUMERIC(18, 2) NOT NULL CHECK (montant > 0),
    flag_montant_eleve BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS processed_files (
    file_hash VARCHAR(64) PRIMARY KEY,
    nom_fichier TEXT NOT NULL,
    processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS totaux_iban_origine (
    file_hash VARCHAR(64) REFERENCES processed_files(file_hash),
    iban_origine VARCHAR(34) NOT NULL,
    montant_total NUMERIC(28, 2) NOT NULL CHECK (montant_total > 0),
    PRIMARY KEY (file_hash, iban_origine)
);

CREATE TABLE IF NOT EXISTS totaux_banque_source (
    file_hash VARCHAR(64) REFERENCES processed_files(file_hash),
    banque_source TEXT NOT NULL,
    montant_total NUMERIC(28, 2) NOT NULL CHECK (montant_total > 0),
    PRIMARY KEY (file_hash, banque_source)
);

CREATE TABLE IF NOT EXISTS totaux_iban_destinataire (
    file_hash VARCHAR(64) REFERENCES processed_files(file_hash),
    iban_destinataire VARCHAR(34) NOT NULL,
    montant_total NUMERIC(28, 2) NOT NULL CHECK (montant_total > 0),
    PRIMARY KEY (file_hash, iban_destinataire)
);