import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Optional


BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "login_mails")
DATABASE_PATH = os.path.join(DATABASE_DIR, "database.db")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")


def get_connection() -> sqlite3.Connection:
    os.makedirs(DATABASE_DIR, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def normalize_wallet(wallet_address: Optional[str]) -> str:
    return (wallet_address or "").strip().lower()


def ensure_schema() -> None:
    """Create and migrate local doctor/session tables."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS login(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT,
                Email TEXT,
                Password TEXT,
                Hospital TEXT,
                WalletAddress TEXT,
                BlockchainRegistered INTEGER DEFAULT 0
            )
            """
        )

        cursor.execute("PRAGMA table_info(login)")
        columns = {row["name"] for row in cursor.fetchall()}
        if "WalletAddress" not in columns:
            cursor.execute("ALTER TABLE login ADD COLUMN WalletAddress TEXT")
        if "BlockchainRegistered" not in columns:
            cursor.execute("ALTER TABLE login ADD COLUMN BlockchainRegistered INTEGER DEFAULT 0")
        if "Password" not in columns:
            cursor.execute("ALTER TABLE login ADD COLUMN Password TEXT")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS doctor_scans(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                WalletAddress TEXT NOT NULL,
                DoctorName TEXT,
                PatientName TEXT,
                PatientAge TEXT,
                ScanImagePath TEXT,
                PdfPath TEXT,
                MetadataPath TEXT,
                DocumentId TEXT,
                BlockchainReportId TEXT,
                PdfHash TEXT,
                EncryptedCid TEXT,
                EncryptionAlgorithm TEXT,
                BlockchainStatus TEXT,
                CreatedAt TEXT NOT NULL
            )
            """
        )

        connection.commit()


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    if not row:
        return None
    return dict(row)


def get_registered_wallets(exclude_wallet: Optional[str] = None) -> list[str]:
    ensure_schema()
    normalized_exclude = normalize_wallet(exclude_wallet)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT WalletAddress FROM login WHERE WalletAddress IS NOT NULL AND WalletAddress != ''")
        wallets = []
        for row in cursor.fetchall():
            wallet = row["WalletAddress"]
            if normalized_exclude and normalize_wallet(wallet) == normalized_exclude:
                continue
            wallets.append(wallet)
        return wallets


def get_doctor_by_wallet(wallet_address: str) -> Optional[dict[str, Any]]:
    ensure_schema()
    normalized_wallet = normalize_wallet(wallet_address)
    if not normalized_wallet:
        return None

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT * FROM login
            WHERE lower(WalletAddress) = ?
            ORDER BY BlockchainRegistered DESC, ID DESC
            LIMIT 1
            """,
            (normalized_wallet,),
        )
        return _row_to_dict(cursor.fetchone())


def upsert_doctor_profile(
    name: str,
    email: str,
    hospital: str,
    wallet_address: str,
    blockchain_registered: bool,
) -> dict[str, Any]:
    ensure_schema()
    existing = get_doctor_by_wallet(wallet_address)

    with get_connection() as connection:
        cursor = connection.cursor()
        if existing:
            cursor.execute(
                """
                UPDATE login
                SET Name = ?, Email = ?, Hospital = ?, WalletAddress = ?, BlockchainRegistered = ?
                WHERE ID = ?
                """,
                (name, email, hospital, wallet_address, int(blockchain_registered), existing["ID"]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO login (Name, Email, Password, Hospital, WalletAddress, BlockchainRegistered)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, email, "", hospital, wallet_address, int(blockchain_registered)),
            )
        connection.commit()

    return get_doctor_by_wallet(wallet_address) or {}


def write_current_user(profile: dict[str, Any]) -> None:
    user = {
        "name": profile.get("Name") or profile.get("name") or "Doctor",
        "email": profile.get("Email") or profile.get("email") or "",
        "hospital": profile.get("Hospital") or profile.get("hospital") or "",
        "wallet_address": profile.get("WalletAddress") or profile.get("wallet_address") or "",
        "blockchain_registered": bool(profile.get("BlockchainRegistered") or profile.get("blockchain_registered")),
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
        json.dump(user, config_file, indent=4)


def add_doctor_scan(scan: dict[str, Any]) -> int:
    ensure_schema()
    created_at = scan.get("created_at") or datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO doctor_scans (
                WalletAddress,
                DoctorName,
                PatientName,
                PatientAge,
                ScanImagePath,
                PdfPath,
                MetadataPath,
                DocumentId,
                BlockchainReportId,
                PdfHash,
                EncryptedCid,
                EncryptionAlgorithm,
                BlockchainStatus,
                CreatedAt
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan.get("wallet_address"),
                scan.get("doctor_name"),
                scan.get("patient_name"),
                scan.get("patient_age"),
                scan.get("scan_image_path"),
                scan.get("pdf_path"),
                scan.get("metadata_path"),
                scan.get("document_id"),
                scan.get("blockchain_report_id"),
                scan.get("pdf_hash"),
                scan.get("encrypted_cid"),
                scan.get("encryption_algorithm"),
                scan.get("blockchain_status"),
                created_at,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)


def get_scans_for_wallet(wallet_address: str, limit: int = 50) -> list[dict[str, Any]]:
    ensure_schema()
    normalized_wallet = normalize_wallet(wallet_address)
    if not normalized_wallet:
        return []

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT * FROM doctor_scans
            WHERE lower(WalletAddress) = ?
            ORDER BY datetime(CreatedAt) DESC, ID DESC
            LIMIT ?
            """,
            (normalized_wallet, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
