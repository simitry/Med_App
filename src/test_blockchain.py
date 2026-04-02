#!/usr/bin/env python3
"""
Blockchain Integration Test Script

This script demonstrates the blockchain functionality without requiring
actual blockchain connection or IPFS upload.

Usage:
    python test_blockchain.py

Author: GitHub Copilot
"""

import os
import hashlib
from blockchain import BlockchainManager


def create_test_pdf():
    """Create a simple test PDF for demonstration."""
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)
        pdf.cell(200, 10, text="Test Medical Report", new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.cell(200, 10, text="Patient: John Doe", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(200, 10, text="Age: 35", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(200, 10, text="Diagnosis: Normal", new_x="LMARGIN", new_y="NEXT")

        test_pdf_path = "test_report.pdf"
        pdf.output(test_pdf_path)
        return test_pdf_path
    except ImportError:
        print("FPDF not installed. Creating mock PDF file.")
        print("Install with: pip install fpdf2")
        # Create a simple text file as mock PDF
        test_pdf_path = "test_report.pdf"
        with open(test_pdf_path, 'w') as f:
            f.write("Test Medical Report\nPatient: John Doe\nAge: 35\nDiagnosis: Normal\n")
        return test_pdf_path


def test_blockchain_functions():
    """Test all blockchain functions."""
    print("Testing Blockchain Integration")
    print("=" * 40)

    # Create test PDF
    print("1. Creating test PDF...")
    pdf_path = create_test_pdf()
    if not pdf_path:
        print("Failed to create test PDF")
        return

    print(f"   Test PDF created: {pdf_path}")

    # Initialize blockchain manager
    print("\n2. Initializing blockchain manager...")
    manager = BlockchainManager()

    # Test PDF hashing
    print("\n3. Testing PDF hashing...")
    pdf_hash = manager.hash_pdf(pdf_path)
    if pdf_hash:
        print(f"   PDF hash: {pdf_hash}")
    else:
        print("   PDF hashing failed")
        return

    # Test report ID generation
    print("\n4. Testing report ID generation...")
    report_id = manager.generate_report_id(pdf_hash)
    print(f"   Report ID: {report_id}")

    # Test IPFS upload (mock)
    print("\n5. Testing IPFS upload (mock)...")
    cid = manager.upload_to_ipfs(pdf_path)
    if cid:
        print(f"   IPFS CID: {cid}")
    else:
        print("   IPFS upload failed")

    # Test patient data hashing
    print("\n6. Testing patient data hashing...")
    patient_name = "John Doe"
    patient_age = "35"
    patient_data = f"{patient_name}{patient_age}"
    patient_hash = hashlib.sha256(patient_data.encode()).hexdigest()
    print(f"   Patient hash: {patient_hash}")

    # Test blockchain connection (will fail without real config)
    print("\n7. Testing blockchain connection...")
    connected = manager.connect_to_blockchain()
    if connected:
        print("   Connected to blockchain successfully")
    else:
        print("   Blockchain connection failed (expected without real configuration)")

    # Test report publishing (will fail without real config)
    print("\n8. Testing report publishing...")
    published = manager.publish_report(pdf_path, patient_name, patient_age)
    if published:
        print("   Report published successfully")
    else:
        print("   Report publishing failed (expected without real configuration)")

    # Test report verification
    print("\n9. Testing report verification...")
    verification_result = manager.verify_report(pdf_path, report_id)
    print(f"   Verification result: {verification_result}")

    # Cleanup
    print("\n10. Cleaning up...")
    try:
        os.remove(pdf_path)
        print("    Test PDF removed")
    except:
        pass

    print("\n" + "=" * 40)
    print("Blockchain integration test completed!")
    print("\nNote: Some tests fail because they require real blockchain")
    print("configuration (Infura API key, deployed contract, etc.)")
    print("\nTo use real blockchain features:")
    print("1. Get an Infura API key")
    print("2. Deploy the smart contract")
    print("3. Update configuration in blockchain.py")
    print("4. Set up IPFS service (Pinata, local node, etc.)")


if __name__ == "__main__":
    test_blockchain_functions()
