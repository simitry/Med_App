# Medical AI Blockchain Setup

This project now uses:

- Hardhat for local smart contract development and deployment
- Pinata for encrypted PDF storage on IPFS
- `DoctorRegistry` to verify doctor integrity
- `MedicalReportRegistry` to publish encrypted report CIDs and verify report hashes

## Contracts

- `contracts/DoctorRegistry.sol`
  Checks whether a doctor wallet is registered, verified, and active.
- `contracts/MedicalReportRegistry.sol`
  Stores report hashes and only accepts publications from doctors in good standing.

## Local Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Install Node dependencies:

```bash
npm install
```

3. Start a local Hardhat node:

```bash
npm run node
```

4. In another terminal, compile and deploy:

```bash
npm run compile
npm run deploy:local
```

This generates:

- `blockchain_config.json`
- `blockchain_artifacts/MedicalReportRegistry.abi.json`
- `blockchain_artifacts/DoctorRegistry.abi.json`

## Pinata Credentials

Set one of these options before publishing a report:

### Option A: JWT

```bash
set PINATA_JWT=your_pinata_jwt
```

### Option B: API key + secret

```bash
set PINATA_API_KEY=your_pinata_api_key
set PINATA_SECRET_API_KEY=your_pinata_secret
```

## How the flow works

1. Hardhat deploys `DoctorRegistry`
2. Hardhat deploys `MedicalReportRegistry` with the doctor registry address
3. The deploy script registers one bootstrap doctor from the local Hardhat accounts
4. The Python app reads `blockchain_config.json`
5. When a PDF is created, the app encrypts it with AES-256-GCM and uploads the encrypted bytes to Pinata
6. The encrypted CID and report hash are published on-chain only if the connected doctor wallet passes the doctor integrity check
7. The desktop app shows the generated `Report ID`, which you use later for verification

The encryption key and nonce are saved only in the local sidecar metadata JSON next to the generated PDF. They are not written to the blockchain.

## App Run

Run the desktop app:

```bash
python src/app.py
```

Open the built-in verifier from the main screen, or run it directly:

```bash
python src/agent_app.py
```

Verify a report later:

```bash
python src/verify_report.py path/to/report.pdf REPORT_ID
```

## Important Notes

- The local doctor account comes from the Hardhat node accounts.
- If Hardhat is not running on `http://127.0.0.1:8545`, the Python app will not connect.
- If Pinata credentials are missing, report publishing will stop before the blockchain transaction.
- `blockchain_config.example.json` is only a template. The deploy script creates the real `blockchain_config.json`.
- The duplicate `medd-main` project is no longer needed after the merge; the root project is now the single integrated app.
