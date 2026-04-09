const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

function loadExistingConfig(configPath) {
  if (!fs.existsSync(configPath)) {
    return {};
  }

  try {
    return JSON.parse(fs.readFileSync(configPath, "utf8"));
  } catch {
    return {};
  }
}

async function main() {
  const configPath = path.join(__dirname, "..", "blockchain_config.json");
  const existingConfig = loadExistingConfig(configPath);
  const [deployer, doctor] = await ethers.getSigners();

  console.log(`Deploying contracts with owner: ${deployer.address}`);
  console.log(`Bootstrap doctor wallet: ${doctor.address}`);

  const DoctorRegistry = await ethers.getContractFactory("DoctorRegistry");
  const doctorRegistry = await DoctorRegistry.deploy();
  await doctorRegistry.waitForDeployment();

  const doctorRegistryAddress = await doctorRegistry.getAddress();
  console.log(`DoctorRegistry deployed to: ${doctorRegistryAddress}`);

  const MedicalReportRegistry = await ethers.getContractFactory("MedicalReportRegistry");
  const reportRegistry = await MedicalReportRegistry.deploy(doctorRegistryAddress);
  await reportRegistry.waitForDeployment();

  const reportRegistryAddress = await reportRegistry.getAddress();
  console.log(`MedicalReportRegistry deployed to: ${reportRegistryAddress}`);

  const doctorId = `DOC-${doctor.address.slice(2, 10).toUpperCase()}`;
  const doctorIdHash = ethers.keccak256(ethers.toUtf8Bytes(doctorId));
  const licenseHash = ethers.keccak256(ethers.toUtf8Bytes("LOCAL_LICENSE_PLACEHOLDER"));

  const registerTx = await doctorRegistry.registerDoctor(
    doctor.address,
    doctorIdHash,
    licenseHash,
    "pinata-doctor-metadata-placeholder"
  );
  await registerTx.wait();
  console.log(`Registered bootstrap doctor: ${doctor.address}`);

  const artifactsDir = path.join(__dirname, "..", "artifacts", "contracts");
  const doctorArtifactPath = path.join(artifactsDir, "DoctorRegistry.sol", "DoctorRegistry.json");
  const reportArtifactPath = path.join(artifactsDir, "MedicalReportRegistry.sol", "MedicalReportRegistry.json");

  const doctorArtifact = JSON.parse(fs.readFileSync(doctorArtifactPath, "utf8"));
  const reportArtifact = JSON.parse(fs.readFileSync(reportArtifactPath, "utf8"));

  const outputDir = path.join(__dirname, "..", "blockchain_artifacts");
  fs.mkdirSync(outputDir, { recursive: true });

  fs.writeFileSync(
    path.join(outputDir, "DoctorRegistry.abi.json"),
    JSON.stringify(doctorArtifact.abi, null, 2)
  );
  fs.writeFileSync(
    path.join(outputDir, "MedicalReportRegistry.abi.json"),
    JSON.stringify(reportArtifact.abi, null, 2)
  );

  const config = {
    network: "localhost",
    rpc_url: "http://127.0.0.1:8545",
    chain_id: 31337,
    owner_address: deployer.address,
    doctor_account_address: doctor.address,
    report_contract_address: reportRegistryAddress,
    doctor_registry_address: doctorRegistryAddress,
    report_contract_abi_path: path.join(outputDir, "MedicalReportRegistry.abi.json"),
    doctor_registry_abi_path: path.join(outputDir, "DoctorRegistry.abi.json"),
    pinata_api_key: existingConfig.pinata_api_key || existingConfig.pinata_api_key_env || "",
    pinata_secret_api_key: existingConfig.pinata_secret_api_key || existingConfig.pinata_secret_api_key_env || "",
    pinata_jwt: existingConfig.pinata_jwt || existingConfig.pinata_jwt_env || ""
  };

  fs.writeFileSync(
    configPath,
    JSON.stringify(config, null, 2)
  );

  const summary = {
    generated_at: new Date().toISOString(),
    doctor_id_preview: doctorId,
    doctor_id_hash: doctorIdHash,
    license_hash: licenseHash,
    deployment_id: crypto.randomUUID()
  };

  fs.writeFileSync(
    path.join(outputDir, "deployment-summary.json"),
    JSON.stringify(summary, null, 2)
  );

  console.log("Saved ABI files and blockchain_config.json");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
