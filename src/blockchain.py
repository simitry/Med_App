"""
Blockchain integration for the medical AI application.

This module supports:
- local Hardhat / Ethereum JSON-RPC connections
- Pinata uploads for generated PDF reports
- report publication through MedicalReportRegistry
- doctor integrity checks through DoctorRegistry
"""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "blockchain_config.json"
PACKAGE_JSON_PATH = PROJECT_ROOT / "package.json"


def _resolve_project_path(path_value: Optional[str]) -> Optional[str]:
    """Resolve relative paths from the project root."""
    if not path_value:
        return None

    candidate = Path(path_value)
    if candidate.is_absolute():
        return str(candidate)
    return str((PROJECT_ROOT / candidate).resolve())


def load_blockchain_config(config_path: Optional[str] = None) -> dict[str, Any]:
    """Load blockchain configuration from disk when available."""
    selected_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    if selected_path.exists():
        with open(selected_path, "r", encoding="utf-8-sig") as config_file:
            data = json.load(config_file)
    else:
        data = {}

    # Migrate older configs that accidentally stored raw Pinata values under *_env keys.
    if data.get("pinata_jwt_env") and not data.get("pinata_jwt") and str(data["pinata_jwt_env"]).startswith("eyJ"):
        data["pinata_jwt"] = data["pinata_jwt_env"]
        data.pop("pinata_jwt_env", None)

    if data.get("pinata_api_key_env") and not data.get("pinata_api_key") and str(data["pinata_api_key_env"]) != "PINATA_API_KEY":
        data["pinata_api_key"] = data["pinata_api_key_env"]
        data.pop("pinata_api_key_env", None)

    if data.get("pinata_secret_api_key_env") and not data.get("pinata_secret_api_key") and str(data["pinata_secret_api_key_env"]) != "PINATA_SECRET_API_KEY":
        data["pinata_secret_api_key"] = data["pinata_secret_api_key_env"]
        data.pop("pinata_secret_api_key_env", None)

    if data.get("report_contract_abi_path"):
        data["report_contract_abi_path"] = _resolve_project_path(data["report_contract_abi_path"])
    if data.get("doctor_registry_abi_path"):
        data["doctor_registry_abi_path"] = _resolve_project_path(data["doctor_registry_abi_path"])

    return data


def _is_local_rpc_url(url: Optional[str]) -> bool:
    """Return True when the RPC URL points to the local Hardhat node."""
    if not url:
        return False

    parsed = urlparse(url)
    return parsed.hostname in {"127.0.0.1", "localhost"}


class BlockchainManager:
    """Handle contract loading, Pinata uploads, and report verification."""

    def __init__(
        self,
        web3_provider: Optional[str] = None,
        contract_address: Optional[str] = None,
        ipfs_gateway: str = "https://gateway.pinata.cloud/ipfs/",
        contract_abi_path: Optional[str] = None,
        doctor_registry_address: Optional[str] = None,
        doctor_registry_abi_path: Optional[str] = None,
        doctor_account_address: Optional[str] = None,
        config_path: Optional[str] = None
    ):
        self.config = load_blockchain_config(config_path)
        self.web3_provider = web3_provider or self.config.get("rpc_url", "http://127.0.0.1:8545")
        self.contract_address = contract_address or self.config.get("report_contract_address")
        self.ipfs_gateway = ipfs_gateway
        self.contract_abi_path = contract_abi_path or self.config.get("report_contract_abi_path")
        self.doctor_registry_address = doctor_registry_address or self.config.get("doctor_registry_address")
        self.doctor_registry_abi_path = doctor_registry_abi_path or self.config.get("doctor_registry_abi_path")
        self.doctor_account_address = doctor_account_address or self.config.get("doctor_account_address")
        self.web3 = None
        self.contract = None
        self.doctor_registry = None
        self.web3_available = WEB3_AVAILABLE
        self.last_error = ""
        self.local_node_started = False

    def _set_error(self, message: str) -> None:
        """Store the latest blockchain error for the UI and scripts."""
        self.last_error = message
        print(message)

    def get_last_error(self) -> str:
        """Return the latest blockchain error message."""
        return self.last_error

    def _has_contract_config(self) -> bool:
        return (
            bool(self.contract_address)
            and bool(self.contract_abi_path)
            and os.path.exists(self.contract_abi_path)
        )

    def _has_doctor_registry_config(self) -> bool:
        return (
            bool(self.doctor_registry_address)
            and bool(self.doctor_registry_abi_path)
            and os.path.exists(self.doctor_registry_abi_path)
        )

    def _load_abi(self, abi_path: str) -> list[dict[str, Any]]:
        with open(abi_path, "r", encoding="utf-8") as abi_file:
            return json.load(abi_file)

    def initialize_contracts(self) -> bool:
        """Initialize both smart contracts if config is present."""
        if not self.web3:
            self._set_error("Blockchain connection not initialized.")
            return False

        try:
            if self._has_doctor_registry_config():
                registry_abi = self._load_abi(self.doctor_registry_abi_path)
                self.doctor_registry = self.web3.eth.contract(
                    address=self.web3.to_checksum_address(self.doctor_registry_address),
                    abi=registry_abi
                )

            if self._has_contract_config():
                report_abi = self._load_abi(self.contract_abi_path)
                self.contract = self.web3.eth.contract(
                    address=self.web3.to_checksum_address(self.contract_address),
                    abi=report_abi
                )

            if not self.doctor_registry:
                self._set_error("Doctor registry contract is not configured correctly.")
                return False

            if not self.contract:
                self._set_error("Report registry contract is not configured correctly.")
                return False

            self.last_error = ""
            return self.contract is not None
        except Exception as exc:
            self._set_error(f"Error initializing smart contracts: {exc}")
            self.contract = None
            self.doctor_registry = None
            return False

    def _wait_for_rpc(self, timeout_seconds: int = 20) -> bool:
        """Poll the configured RPC endpoint until it becomes available."""
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                self.web3 = Web3(Web3.HTTPProvider(self.web3_provider))
                if self.web3.is_connected():
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def _maybe_start_local_hardhat_node(self) -> bool:
        """Start the local Hardhat node automatically when localhost is configured."""
        if self.local_node_started:
            return True

        if not _is_local_rpc_url(self.web3_provider):
            return False

        if not PACKAGE_JSON_PATH.exists():
            return False

        try:
            if os.name == "nt":
                subprocess.Popen(
                    [
                        "powershell",
                        "-NoExit",
                        "-Command",
                        "npm run node",
                    ],
                    cwd=str(PROJECT_ROOT),
                    creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
                )
            else:
                subprocess.Popen(
                    ["npm", "run", "node"],
                    cwd=str(PROJECT_ROOT),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            self.local_node_started = True
            return self._wait_for_rpc()
        except Exception as exc:
            self._set_error(f"Unable to start the local Hardhat node automatically: {exc}")
            return False

    def _maybe_deploy_local_contracts(self) -> bool:
        """Deploy contracts automatically when the local node is reachable but contracts are missing."""
        if not _is_local_rpc_url(self.web3_provider) or not PACKAGE_JSON_PATH.exists():
            return False

        try:
            result = subprocess.run(
                ["npm", "run", "deploy:local"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if result.returncode != 0:
                message = result.stderr.strip() or result.stdout.strip() or "Unknown deployment error."
                self._set_error(f"Local contract deployment failed: {message}")
                return False

            self.config = load_blockchain_config()
            self.contract_address = self.config.get("report_contract_address")
            self.contract_abi_path = self.config.get("report_contract_abi_path")
            self.doctor_registry_address = self.config.get("doctor_registry_address")
            self.doctor_registry_abi_path = self.config.get("doctor_registry_abi_path")
            self.doctor_account_address = self.doctor_account_address or self.config.get("doctor_account_address")
            return True
        except Exception as exc:
            self._set_error(f"Unable to deploy local contracts automatically: {exc}")
            return False

    def connect_to_blockchain(self) -> bool:
        """Connect to the configured RPC endpoint."""
        if not self.web3_available:
            self._set_error("Web3.py not installed. Install with: pip install web3 eth-account eth-utils")
            return False

        try:
            self.web3 = Web3(Web3.HTTPProvider(self.web3_provider))

            if not self.web3.is_connected():
                if not self._maybe_start_local_hardhat_node():
                    self._set_error(f"Failed to connect to blockchain network at {self.web3_provider}")
                    return False

            if not self.initialize_contracts():
                if _is_local_rpc_url(self.web3_provider) and self._maybe_deploy_local_contracts() and self.initialize_contracts():
                    print("Local Hardhat contracts were deployed automatically.")
                else:
                    return False

            print(f"Connected to blockchain network. Current block: {self.web3.eth.block_number}")
            self.last_error = ""
            return True
        except Exception as exc:
            self._set_error(f"Error connecting to blockchain: {exc}")
            return False

    def hash_pdf(self, file_path: str) -> Optional[str]:
        """Calculate the SHA256 hash of a PDF file."""
        try:
            if not os.path.exists(file_path):
                self._set_error(f"File not found: {file_path}")
                return None

            with open(file_path, "rb") as report_file:
                file_data = report_file.read()

            self.last_error = ""
            return hashlib.sha256(file_data).hexdigest()
        except Exception as exc:
            self._set_error(f"Error hashing PDF: {exc}")
            return None

    def generate_report_id(self, pdf_hash: str) -> str:
        """Generate a deterministic report id from the PDF hash."""
        return hashlib.sha256(pdf_hash.encode("utf-8")).hexdigest()

    def _pinata_headers(self) -> dict[str, str]:
        def resolve_secret(config_value: Optional[str], env_name: Optional[str]) -> Optional[str]:
            if env_name:
                env_value = os.getenv(env_name)
                if env_value:
                    return env_value

            if config_value:
                return config_value

            if env_name and env_name not in {"PINATA_JWT", "PINATA_API_KEY", "PINATA_SECRET_API_KEY"}:
                return env_name

            return None

        jwt_name = self.config.get("pinata_jwt_env", "PINATA_JWT")
        api_name = self.config.get("pinata_api_key_env", "PINATA_API_KEY")
        secret_name = self.config.get("pinata_secret_api_key_env", "PINATA_SECRET_API_KEY")

        jwt = resolve_secret(self.config.get("pinata_jwt"), jwt_name)
        if jwt:
            return {"Authorization": f"Bearer {jwt}"}

        api_key = resolve_secret(self.config.get("pinata_api_key"), api_name)
        secret_key = resolve_secret(self.config.get("pinata_secret_api_key"), secret_name)
        if api_key and secret_key:
            return {
                "pinata_api_key": api_key,
                "pinata_secret_api_key": secret_key
            }

        return {}

    def upload_to_ipfs(self, file_path: str) -> Optional[str]:
        """Upload a PDF file to Pinata and return its CID."""
        if not REQUESTS_AVAILABLE:
            self._set_error("Requests is not installed. Install with: pip install requests")
            return None

        if not os.path.exists(file_path):
            self._set_error(f"File not found: {file_path}")
            return None

        headers = self._pinata_headers()
        if not headers:
            self._set_error(
                "Pinata credentials are missing. Set PINATA_JWT or PINATA_API_KEY and "
                "PINATA_SECRET_API_KEY, or add pinata_jwt / pinata_api_key / pinata_secret_api_key "
                "to blockchain_config.json."
            )
            return None

        endpoint = "https://api.pinata.cloud/pinning/pinFileToIPFS"

        try:
            with open(file_path, "rb") as upload_file:
                files = {"file": (os.path.basename(file_path), upload_file, "application/pdf")}
                response = requests.post(endpoint, headers=headers, files=files, timeout=60)

            if not response.ok:
                self._set_error(f"Pinata upload failed: {response.status_code} {response.text}")
                return None

            payload = response.json()
            cid = payload.get("IpfsHash")
            if not cid:
                self._set_error("Pinata upload succeeded but no CID was returned.")
                return None

            self.last_error = ""
            return cid
        except Exception as exc:
            self._set_error(f"Error uploading to Pinata: {exc}")
            return None

    def check_doctor_integrity(self, doctor_address: Optional[str] = None) -> bool:
        """Return True when the doctor wallet is registered and active on-chain."""
        if not self.doctor_registry:
            self._set_error("Doctor registry contract is not initialized.")
            return False

        address_to_check = doctor_address or self.doctor_account_address
        if not address_to_check:
            self._set_error("Doctor account address is not configured.")
            return False

        try:
            checksum_address = self.web3.to_checksum_address(address_to_check)
            result = bool(self.doctor_registry.functions.isDoctorInGoodStanding(checksum_address).call())
            if not result:
                self._set_error("The configured doctor wallet is not verified and active on-chain.")
            else:
                self.last_error = ""
            return result
        except Exception as exc:
            self._set_error(f"Error checking doctor integrity: {exc}")
            return False

    def get_readiness_issues(self) -> list[str]:
        """Return a list of missing prerequisites before report publishing."""
        issues: list[str] = []

        if not self.web3_available:
            issues.append("web3.py is not installed in the current virtual environment.")

        if not self.config:
            issues.append("blockchain_config.json was not found.")

        if not self.web3_provider:
            issues.append("RPC URL is missing from blockchain_config.json.")

        if not self.contract_address:
            issues.append("Report contract address is missing from blockchain_config.json.")

        if not self.doctor_registry_address:
            issues.append("Doctor registry address is missing from blockchain_config.json.")

        if not self.contract_abi_path or not os.path.exists(self.contract_abi_path):
            issues.append("Report contract ABI file is missing.")

        if not self.doctor_registry_abi_path or not os.path.exists(self.doctor_registry_abi_path):
            issues.append("Doctor registry ABI file is missing.")

        if not self.doctor_account_address:
            issues.append("Doctor account address is missing from blockchain_config.json.")

        if not self._pinata_headers():
            issues.append(
                "Pinata credentials are missing. Set PINATA_JWT or PINATA_API_KEY and PINATA_SECRET_API_KEY, "
                "or add them to blockchain_config.json."
            )

        return issues

    def _transaction_sender(self) -> dict[str, Any]:
        if not self.doctor_account_address:
            return {}
        return {"from": self.web3.to_checksum_address(self.doctor_account_address)}

    def _owner_sender(self) -> dict[str, Any]:
        owner_address = self.config.get("owner_address")
        if owner_address:
            return {"from": self.web3.to_checksum_address(owner_address)}

        accounts = self.web3.eth.accounts
        if not accounts:
            return {}
        return {"from": self.web3.to_checksum_address(accounts[0])}

    def get_local_accounts(self) -> list[str]:
        """Return available accounts from the local JSON-RPC node."""
        if not self.web3 and not self.connect_to_blockchain():
            return []

        try:
            return [self.web3.to_checksum_address(account) for account in self.web3.eth.accounts]
        except Exception as exc:
            self._set_error(f"Error fetching local blockchain accounts: {exc}")
            return []

    def choose_doctor_wallet(
        self,
        used_wallets: Optional[list[str]] = None,
        preferred_wallet: Optional[str] = None
    ) -> Optional[str]:
        """Pick a local wallet for a doctor, avoiding the owner and already-used wallets."""
        if not self.web3 and not self.connect_to_blockchain():
            return None

        owner_address = self.config.get("owner_address")
        normalized_used_wallets = {
            self.web3.to_checksum_address(wallet)
            for wallet in (used_wallets or [])
            if wallet
        }

        if preferred_wallet:
            checksum_wallet = self.web3.to_checksum_address(preferred_wallet)
            if checksum_wallet != owner_address:
                return checksum_wallet

        for account in self.get_local_accounts():
            if account == owner_address:
                continue
            if account in normalized_used_wallets:
                continue
            return account

        self._set_error("No unused local blockchain wallet is available for this doctor.")
        return None

    def doctor_exists(self, doctor_address: str) -> bool:
        """Return True when the doctor wallet is already present in the registry."""
        if not self.doctor_registry:
            self._set_error("Doctor registry contract is not initialized.")
            return False

        try:
            checksum_address = self.web3.to_checksum_address(doctor_address)
            self.doctor_registry.functions.getDoctor(checksum_address).call()
            self.last_error = ""
            return True
        except Exception:
            return False

    def register_doctor(
        self,
        doctor_name: str,
        doctor_email: str,
        doctor_hospital: str,
        wallet_address: str
    ) -> bool:
        """Register or reactivate a doctor in the on-chain doctor registry."""
        if not self.doctor_registry:
            self._set_error("Doctor registry contract is not initialized.")
            return False

        try:
            checksum_wallet = self.web3.to_checksum_address(wallet_address)
            doctor_id_hash = hashlib.sha256(f"{doctor_name}:{doctor_email}".encode("utf-8")).hexdigest()
            license_hash = hashlib.sha256(f"{doctor_hospital}:{doctor_email}".encode("utf-8")).hexdigest()

            if self.doctor_exists(checksum_wallet):
                tx_hash = self.doctor_registry.functions.updateDoctorStatus(
                    checksum_wallet,
                    True,
                    True
                ).transact(self._owner_sender())
                self.web3.eth.wait_for_transaction_receipt(tx_hash)
                self.last_error = ""
                return True

            tx_hash = self.doctor_registry.functions.registerDoctor(
                checksum_wallet,
                Web3.to_bytes(hexstr=doctor_id_hash),
                Web3.to_bytes(hexstr=license_hash),
                doctor_hospital
            ).transact(self._owner_sender())
            self.web3.eth.wait_for_transaction_receipt(tx_hash)
            self.last_error = ""
            return True
        except Exception as exc:
            self._set_error(f"Error registering doctor on-chain: {exc}")
            return False

    def publish_report(self, file_path: str, patient_name: str, patient_age: str) -> bool:
        """Hash, upload, and publish a PDF report to the blockchain."""
        try:
            pdf_hash = self.hash_pdf(file_path)
            if not pdf_hash:
                return False

            report_id = self.generate_report_id(pdf_hash)
            cid = self.upload_to_ipfs(file_path)
            if not cid:
                return False

            patient_hash = hashlib.sha256(f"{patient_name}{patient_age}".encode("utf-8")).hexdigest()

            if not self.contract:
                self._set_error("Report contract not initialized. Check blockchain_config.json and ABI files.")
                return False

            if not self.check_doctor_integrity():
                return False

            tx_hash = self.contract.functions.publishReport(
                Web3.to_bytes(hexstr=report_id),
                Web3.to_bytes(hexstr=pdf_hash),
                cid,
                Web3.to_bytes(hexstr=patient_hash)
            ).transact(self._transaction_sender())

            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                print(f"Report published successfully. Transaction: {tx_hash.hex()}")
                self.last_error = ""
                return True

            self._set_error("Transaction failed.")
            return False
        except Exception as exc:
            self._set_error(f"Error publishing report: {exc}")
            return False

    def verify_report(self, file_path: str, report_id: str) -> str:
        """Verify a report hash against the chain."""
        try:
            current_hash = self.hash_pdf(file_path)
            if not current_hash:
                return "ERROR"

            if not self.contract:
                self._set_error("Report contract not initialized.")
                return "ERROR"

            stored_data = self.contract.functions.getReport(Web3.to_bytes(hexstr=report_id)).call()
            stored_pdf_hash = Web3.to_hex(stored_data[1]).removeprefix("0x")

            self.last_error = ""
            return "VALID" if current_hash.lower() == stored_pdf_hash.lower() else "MODIFIED"
        except Exception as exc:
            self._set_error(f"Error verifying report: {exc}")
            return "ERROR"


def connect_to_blockchain(
    provider_url: Optional[str] = None,
    contract_address: Optional[str] = None,
    config_path: Optional[str] = None
) -> Optional[BlockchainManager]:
    """Connect to blockchain and return an initialized manager."""
    manager = BlockchainManager(
        web3_provider=provider_url,
        contract_address=contract_address,
        config_path=config_path
    )
    if manager.connect_to_blockchain():
        return manager
    return None


def hash_pdf(file_path: str) -> Optional[str]:
    manager = BlockchainManager()
    return manager.hash_pdf(file_path)


def generate_report_id(pdf_hash: str) -> str:
    manager = BlockchainManager()
    return manager.generate_report_id(pdf_hash)


def upload_to_ipfs(file_path: str) -> Optional[str]:
    manager = BlockchainManager()
    return manager.upload_to_ipfs(file_path)


def publish_report(
    file_path: str,
    patient_name: str,
    patient_age: str,
    provider_url: Optional[str] = None,
    contract_address: Optional[str] = None,
    config_path: Optional[str] = None,
    doctor_account_address: Optional[str] = None
) -> bool:
    result = publish_report_detailed(
        file_path=file_path,
        patient_name=patient_name,
        patient_age=patient_age,
        provider_url=provider_url,
        contract_address=contract_address,
        config_path=config_path,
        doctor_account_address=doctor_account_address
    )
    return bool(result["success"])


def publish_report_detailed(
    file_path: str,
    patient_name: str,
    patient_age: str,
    provider_url: Optional[str] = None,
    contract_address: Optional[str] = None,
    config_path: Optional[str] = None,
    doctor_account_address: Optional[str] = None
) -> dict[str, Any]:
    """Publish a report and return detailed status for the UI."""
    manager = BlockchainManager(
        web3_provider=provider_url,
        contract_address=contract_address,
        config_path=config_path,
        doctor_account_address=doctor_account_address
    )
    pdf_hash = manager.hash_pdf(file_path)
    report_id = manager.generate_report_id(pdf_hash) if pdf_hash else None

    if not pdf_hash:
        return {
            "success": False,
            "error": manager.get_last_error() or "Could not hash the report file.",
            "issues": [manager.get_last_error()] if manager.get_last_error() else [],
            "report_id": None,
            "pdf_hash": None,
        }

    readiness_issues = manager.get_readiness_issues()
    if readiness_issues:
        return {
            "success": False,
            "error": "\n".join(readiness_issues),
            "issues": readiness_issues,
            "report_id": report_id,
            "pdf_hash": pdf_hash,
        }

    if not manager.connect_to_blockchain():
        return {
            "success": False,
            "error": manager.get_last_error() or "Failed to connect to blockchain.",
            "issues": [manager.get_last_error()] if manager.get_last_error() else [],
            "report_id": report_id,
            "pdf_hash": pdf_hash,
        }

    success = manager.publish_report(file_path, patient_name, patient_age)
    return {
        "success": success,
        "error": "" if success else (manager.get_last_error() or "Report publishing failed."),
        "issues": [] if success else ([manager.get_last_error()] if manager.get_last_error() else []),
        "report_id": report_id,
        "pdf_hash": pdf_hash,
    }


def provision_doctor_identity(
    doctor_name: str,
    doctor_email: str,
    doctor_hospital: str,
    preferred_wallet: Optional[str] = None,
    used_wallets: Optional[list[str]] = None,
    config_path: Optional[str] = None
) -> dict[str, Any]:
    """Assign a local wallet to a doctor and ensure the doctor is registered on-chain."""
    manager = BlockchainManager(config_path=config_path)

    if not manager.connect_to_blockchain():
        return {
            "success": False,
            "error": manager.get_last_error() or "Failed to connect to blockchain.",
            "wallet_address": None,
        }

    wallet_address = manager.choose_doctor_wallet(
        used_wallets=used_wallets,
        preferred_wallet=preferred_wallet
    )
    if not wallet_address:
        return {
            "success": False,
            "error": manager.get_last_error() or "No wallet could be assigned to this doctor.",
            "wallet_address": None,
        }

    if not manager.register_doctor(
        doctor_name=doctor_name,
        doctor_email=doctor_email,
        doctor_hospital=doctor_hospital,
        wallet_address=wallet_address
    ):
        return {
            "success": False,
            "error": manager.get_last_error() or "Failed to register doctor on-chain.",
            "wallet_address": wallet_address,
        }

    return {
        "success": True,
        "error": "",
        "wallet_address": wallet_address,
    }
