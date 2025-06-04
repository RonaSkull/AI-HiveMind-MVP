import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
// ethers will be available from hre (Hardhat Runtime Environment)
// dotenv configuration is handled by hardhat.config.cjs

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying contracts with the account:", deployer.address);
    
    // Verify the deployer matches the expected address
    const expectedDeployer = process.env.DEPLOYER_ADDRESS;
    if (deployer.address.toLowerCase() !== expectedDeployer.toLowerCase()) {
        console.error(`Deployer address mismatch. Expected: ${expectedDeployer}, Got: ${deployer.address}`);
        process.exit(1);
    }

    const balance = await deployer.getBalance();
    console.log("Account balance:", balance.toString());

    const AINFTVault = await hre.ethers.getContractFactory("AINFTVault");
    const vault = await AINFTVault.deploy(deployer.address);

    console.log("AINFTVault deployed to:", vault.address);

    // Save contract address to .env.development
    // dotenv.config() is not needed here as hardhat.config.cjs handles it.
    const envPath = path.resolve(__dirname, '../.env.development');
    const envContent = fs.readFileSync(envPath, 'utf8');
    const lines = envContent.split('\n');
    const newLines = lines.map(line => {
        if (line.startsWith('CONTRACT_ADDRESS=')) {
            return `CONTRACT_ADDRESS=${vault.address}`;
        }
        return line;
    });
    
    fs.writeFileSync(envPath, newLines.join('\n'), 'utf8');
    console.log("Contract address saved to .env");
}

main()
    .then(() => process.exit(0))
    .catch(error => {
        console.error(error);
        process.exit(1);
    });
