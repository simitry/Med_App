# Medical AI Application with Blockchain Verification

A comprehensive medical AI application that analyzes X-ray images using PyTorch and generates tamper-proof PDF reports with blockchain verification.

## Features

- **AI-Powered Diagnosis**: Uses PyTorch and TorchXRayVision for automated disease detection in X-ray images
- **PDF Report Generation**: Creates professional medical reports using FPDF
- **Blockchain Verification**: Immutable report storage and verification using Ethereum blockchain
- **IPFS Storage**: Decentralized file storage for PDF reports
- **Tkinter GUI**: User-friendly interface with CustomTkinter

## Installation

1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up blockchain configuration (see Blockchain Setup section below)

## Usage

1. Run the application:
   ```bash
   python src/app.py
   ```

2. Configure appearance preferences
3. Log in or register
4. Upload an X-ray image
5. Generate PDF report with optional blockchain verification

## Blockchain Setup

### 1. Smart Contract Deployment

Deploy the `MedicalReportRegistry.sol` contract to your preferred Ethereum network:

- **Testnet**: Sepolia, Goerli, or Mumbai (Polygon)
- **Mainnet**: Ethereum mainnet (requires real ETH)

Use Remix IDE, Hardhat, or Truffle for deployment.

### 2. Configuration

Update the blockchain configuration in `src/main.py` and `src/blockchain.py`:

```python
# Replace with your actual values
provider_url = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"
contract_address = "0xYOUR_DEPLOYED_CONTRACT_ADDRESS"
```

### 3. IPFS Setup

For IPFS uploads, you have several options:

- **Local IPFS Node**: Install and run IPFS daemon locally
- **Pinata**: Use Pinata's API service
- **Web3.Storage**: Use Protocol Labs' service
- **Infura IPFS**: Use Infura's IPFS service

Update the IPFS configuration in `blockchain.py` accordingly.

## Blockchain Features

### PDF Hashing
- Calculates SHA256 hash of generated PDF reports
- Ensures report integrity and tamper detection

### IPFS Storage
- Uploads PDF files to decentralized storage
- Returns Content Identifier (CID) for retrieval

### Smart Contract Integration
- Publishes report metadata to blockchain
- Stores: Report ID, PDF hash, IPFS CID, Patient hash, Doctor address, Timestamp

### Report Verification
Use the verification script to check report integrity:

```bash
python src/verify_report.py path/to/report.pdf REPORT_ID
```

## Project Structure

```
src/
├── app.py              # Preferences/settings app
├── login.py            # Login/registration system
├── main.py             # Main application with AI and PDF generation
├── pdf.py              # PDF generation utilities
├── torch_ai.py         # PyTorch AI model for X-ray analysis
├── blockchain.py       # Blockchain integration module
├── verify_report.py    # Report verification script
└── MedicalReportRegistry.sol  # Smart contract
```

## Dependencies

- **AI/ML**: torch, torchvision, torchxrayvision, scikit-image
- **GUI**: customtkinter, tkinter
- **PDF**: fpdf2
- **Blockchain**: web3.py, eth-account, eth-utils
- **Database**: sqlite3 (built-in)
- **HTTP**: requests

## Security Considerations

- Patient data is hashed before blockchain storage (privacy-preserving)
- PDF hashes ensure tamper detection
- Smart contract prevents duplicate reports
- IPFS provides decentralized, permanent storage

## Development

The code is structured for easy integration and extension:

- Modular blockchain functions in `blockchain.py`
- Clean separation of concerns
- Well-documented code with comments
- Beginner-friendly structure

## License

This project is for educational and research purposes. Ensure compliance with medical data regulations (HIPAA, GDPR, etc.) before production use.

## Disclaimer

This application is not intended for clinical use without proper medical validation and regulatory approval. Always consult qualified medical professionals for diagnosis and treatment.