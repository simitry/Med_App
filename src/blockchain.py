"""
Blockchain Integration Module for Medical AI Application

This module provides blockchain verification functionality for medical reports,
including PDF hashing, IPFS storage, and smart contract interactions.

Dependencies:
- web3.py
- hashlib (built-in)
- requests
- json (built-in)

Author: GitHub Copilot
"""

import hashlib
import json
import os
from typing import Optional

# Try to import web3, but handle gracefully if not installed
try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("Warning: web3.py not installed. Blockchain features will be limited.")
    print("Install with: pip install web3 eth-account eth-utils")

# Try to import optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not installed. IPFS features will be limited.")
    print("Install with: pip install requests")


class BlockchainManager:
    """
    Manages blockchain operations for medical report verification.

    This class handles:
    - PDF hashing and verification
    - IPFS file storage
    - Smart contract interactions
    """

    def __init__(self,
                 web3_provider: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                 contract_address: str = "0xYOUR_CONTRACT_ADDRESS",
                 ipfs_gateway: str = "https://ipfs.infura.io/ipfs/",
                 contract_abi_path: Optional[str] = None):
        """
        Initialize the blockchain manager.

        Args:
            web3_provider: Web3 provider URL (Infura, Alchemy, etc.)
            contract_address: Deployed smart contract address
            ipfs_gateway: IPFS gateway URL for retrieving files
        """
        self.web3_provider = web3_provider
        self.contract_address = contract_address
        self.ipfs_gateway = ipfs_gateway
        self.contract_abi_path = contract_abi_path
        self.web3 = None
        self.contract = None
        self.web3_available = WEB3_AVAILABLE

    def _has_contract_config(self) -> bool:
        """Return True when the manager has enough information to build a contract."""
        return (
            self.contract_address
            and self.contract_address != "0xYOUR_CONTRACT_ADDRESS"
            and self.contract_abi_path
            and os.path.exists(self.contract_abi_path)
        )

    def initialize_contract(self) -> bool:
        """
        Initialize the smart contract instance if ABI and address are configured.
        """
        if not self.web3:
            print("Blockchain connection not initialized.")
            return False

        if not self._has_contract_config():
            print("Smart contract ABI/address not configured. Blockchain publishing is disabled.")
            return False

        try:
            with open(self.contract_abi_path, "r", encoding="utf-8") as abi_file:
                contract_abi = json.load(abi_file)

            checksum_address = self.web3.to_checksum_address(self.contract_address)
            self.contract = self.web3.eth.contract(address=checksum_address, abi=contract_abi)
            return True
        except Exception as e:
            print(f"Error initializing smart contract: {e}")
            self.contract = None
            return False

    def connect_to_blockchain(self) -> bool:
        """
        Connect to the blockchain network.

        Returns:
            bool: True if connection successful, False otherwise
        """
        if not self.web3_available:
            print("Web3.py not installed. Cannot connect to blockchain.")
            print("Install with: pip install web3 eth-account eth-utils")
            return False

        try:
            self.web3 = Web3(Web3.HTTPProvider(self.web3_provider))

            if not self.web3.is_connected():
                print("Failed to connect to blockchain network")
                return False

            if self._has_contract_config():
                self.initialize_contract()

            print(f"Connected to blockchain network. Current block: {self.web3.eth.block_number}")
            return True

        except Exception as e:
            print(f"Error connecting to blockchain: {e}")
            return False

    def hash_pdf(self, file_path: str) -> Optional[str]:
        """
        Calculate SHA256 hash of a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            str: Hexadecimal hash string, or None if error
        """
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return None

            with open(file_path, 'rb') as f:
                file_data = f.read()

            # Calculate SHA256 hash
            hash_object = hashlib.sha256(file_data)
            hash_hex = hash_object.hexdigest()

            print(f"PDF hash calculated: {hash_hex}")
            return hash_hex

        except Exception as e:
            print(f"Error hashing PDF: {e}")
            return None

    def generate_report_id(self, pdf_hash: str) -> str:
        """
        Generate a unique report ID from PDF hash.

        Args:
            pdf_hash: SHA256 hash of the PDF

        Returns:
            str: Report ID as hex string
        """
        # Use hash of the PDF hash as report ID
        report_id = hashlib.sha256(pdf_hash.encode()).hexdigest()
        print(f"Generated report ID: {report_id}")
        return report_id

    def upload_to_ipfs(self, file_path: str) -> Optional[str]:
        """
        Upload a file to IPFS and return the Content Identifier (CID).

        Args:
            file_path: Path to the file to upload

        Returns:
            str: IPFS CID, or None if upload failed
        """
        if not REQUESTS_AVAILABLE:
            print("Requests library not installed. Using mock IPFS upload.")
            print("Install with: pip install requests")
            # Mock CID for demonstration
            mock_cid = "QmYourMockCIDHere123456789012345678901234567890"
            print(f"Mock IPFS upload successful. CID: {mock_cid}")
            return mock_cid

        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return None

            # For this example, we'll use a simple IPFS HTTP API
            # In production, you might want to use Pinata, Web3.Storage, or local IPFS node

            # Note: This is a simplified example. Real IPFS upload requires:
            # 1. Running IPFS daemon locally, or
            # 2. Using a service like Pinata with API key

            print("Note: IPFS upload requires IPFS daemon or service API key")
            print("For demonstration, returning mock CID")

            # Mock CID for demonstration - replace with actual IPFS upload
            mock_cid = "QmYourMockCIDHere123456789012345678901234567890"
            print(f"Mock IPFS upload successful. CID: {mock_cid}")
            return mock_cid

        except Exception as e:
            print(f"Error uploading to IPFS: {e}")
            return None

    def publish_report(self, file_path: str, patient_name: str, patient_age: str) -> bool:
        """
        Publish a medical report to the blockchain.

        Args:
            file_path: Path to the PDF report file
            patient_name: Patient's name
            patient_age: Patient's age

        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            # Step 1: Hash the PDF
            pdf_hash = self.hash_pdf(file_path)
            if not pdf_hash:
                return False

            # Step 2: Generate report ID
            report_id = self.generate_report_id(pdf_hash)

            # Step 3: Upload to IPFS
            cid = self.upload_to_ipfs(file_path)
            if not cid:
                return False

            # Step 4: Hash patient data (for privacy)
            patient_data = f"{patient_name}{patient_age}"
            patient_hash = hashlib.sha256(patient_data.encode()).hexdigest()

            # Step 5: Publish to blockchain
            if not self.contract:
                print("Smart contract not initialized. Provide a contract address and ABI file, then call connect_to_blockchain().")
                return False

            # Convert strings to bytes32
            report_id_bytes = Web3.to_bytes(hexstr=report_id)
            pdf_hash_bytes = Web3.to_bytes(hexstr=pdf_hash)
            patient_hash_bytes = Web3.to_bytes(hexstr=patient_hash)

            # Call smart contract function
            tx_hash = self.contract.functions.publishReport(
                report_id_bytes,
                pdf_hash_bytes,
                cid,
                patient_hash_bytes
            ).transact()

            # Wait for transaction confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                print(f"Report published successfully! Transaction: {tx_hash.hex()}")
                return True
            else:
                print("Transaction failed")
                return False

        except Exception as e:
            print(f"Error publishing report: {e}")
            return False

    def verify_report(self, file_path: str, report_id: str) -> str:
        """
        Verify a PDF report against blockchain records.

        Args:
            file_path: Path to the PDF file
            report_id: Report ID from blockchain

        Returns:
            str: "VALID" if hashes match, "MODIFIED" if they don't, "ERROR" on failure
        """
        try:
            # Hash the current PDF
            current_hash = self.hash_pdf(file_path)
            if not current_hash:
                return "ERROR"

            # Get stored hash from blockchain
            if not self.contract:
                print("Smart contract not initialized")
                return "ERROR"

            # Call smart contract to get stored PDF hash
            report_id_bytes = Web3.to_bytes(hexstr=report_id)
            stored_data = self.contract.functions.getReport(report_id_bytes).call()
            stored_pdf_hash = Web3.to_hex(stored_data[1])  # Assuming function returns (reportId, pdfHash, cid, patientHash)

            # Compare hashes
            if current_hash.lower() == stored_pdf_hash.lower():
                return "VALID"
            else:
                return "MODIFIED"

        except Exception as e:
            print(f"Error verifying report: {e}")
            return "ERROR"


# Convenience functions for easy integration
def connect_to_blockchain(provider_url: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                         contract_address: str = "0xYOUR_CONTRACT_ADDRESS") -> Optional[BlockchainManager]:
    """
    Connect to blockchain and return manager instance.

    Args:
        provider_url: Web3 provider URL
        contract_address: Smart contract address

    Returns:
        BlockchainManager instance or None if connection failed
    """
    manager = BlockchainManager(provider_url, contract_address)
    if manager.connect_to_blockchain():
        return manager
    return None


def hash_pdf(file_path: str) -> Optional[str]:
    """
    Calculate SHA256 hash of a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        str: Hexadecimal hash string, or None if error
    """
    manager = BlockchainManager()
    return manager.hash_pdf(file_path)


def generate_report_id(pdf_hash: str) -> str:
    """
    Generate a unique report ID from PDF hash.

    Args:
        pdf_hash: SHA256 hash of the PDF

    Returns:
        str: Report ID as hex string
    """
    manager = BlockchainManager()
    return manager.generate_report_id(pdf_hash)


def upload_to_ipfs(file_path: str) -> Optional[str]:
    """
    Upload a file to IPFS and return the CID.

    Args:
        file_path: Path to the file to upload

    Returns:
        str: IPFS CID, or None if upload failed
    """
    manager = BlockchainManager()
    return manager.upload_to_ipfs(file_path)


def publish_report(file_path: str, patient_name: str, patient_age: str,
                  provider_url: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                  contract_address: str = "0xYOUR_CONTRACT_ADDRESS") -> bool:
    """
    Publish a medical report to the blockchain.

    Args:
        file_path: Path to the PDF report file
        patient_name: Patient's name
        patient_age: Patient's age
        provider_url: Web3 provider URL
        contract_address: Smart contract address

    Returns:
        bool: True if published successfully, False otherwise
    """
    manager = BlockchainManager(provider_url, contract_address)
    if not manager.connect_to_blockchain():
        return False
    return manager.publish_report(file_path, patient_name, patient_age)
