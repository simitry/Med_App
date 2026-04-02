#!/usr/bin/env python3
"""
Medical Report Verification Script

This script verifies the integrity of a medical PDF report by comparing
its hash against the blockchain record.

Usage:
    python verify_report.py <pdf_file_path> <report_id>

Example:
    python verify_report.py report.pdf 0x1234567890abcdef...

Dependencies:
- web3.py
- The blockchain.py module
"""

import os
import sys

from blockchain import BlockchainManager


def main():
    """Main verification function."""
    if len(sys.argv) != 3:
        print("Usage: python verify_report.py <pdf_file_path> <report_id>")
        print("Example: python verify_report.py report.pdf 0x1234567890abcdef...")
        sys.exit(1)

    pdf_file = sys.argv[1]
    report_id = sys.argv[2]

    if not os.path.exists(pdf_file):
        print(f"Error: PDF file '{pdf_file}' not found.")
        sys.exit(1)

    print("Medical Report Verification")
    print("=" * 40)
    print(f"PDF File: {pdf_file}")
    print(f"Report ID: {report_id}")
    print()

    provider_url = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"
    contract_address = "0xYOUR_CONTRACT_ADDRESS"

    manager = BlockchainManager(provider_url, contract_address)

    print("Connecting to blockchain...")
    if not manager.connect_to_blockchain():
        print("Failed to connect to blockchain. Please check your configuration.")
        sys.exit(1)

    print("Verifying report integrity...")
    result = manager.verify_report(pdf_file, report_id)

    print()
    print("Verification Result:")
    print("=" * 20)

    if result == "VALID":
        print("REPORT IS VALID")
        print("The PDF file matches the blockchain record.")
        print("The medical report has not been modified since publication.")
    elif result == "MODIFIED":
        print("REPORT HAS BEEN MODIFIED")
        print("The PDF file does not match the blockchain record.")
        print("The medical report may have been tampered with.")
    else:
        print("VERIFICATION ERROR")
        print("Could not verify the report. Please check:")
        print("- PDF file integrity")
        print("- Report ID correctness")
        print("- Blockchain connection")
        print("- Smart contract configuration")

    print()
    return result == "VALID"


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
