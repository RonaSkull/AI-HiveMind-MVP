from crewai import Agent
from crewai_tools import BaseTool
from typing import List, Optional, Dict, Any
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
import json
import os
from pathlib import Path
from eth_account import Account
from config.settings import settings

class PriceExecutionAgent:
    def __init__(self, tools: Optional[List[BaseTool]] = None):
        self.tools = tools or []
        self.agent = self._create_agent()
        self.web3 = self._initialize_web3()
        self.contract = self._initialize_contract()
    
    def _initialize_web3(self):
        """Initialize Web3 connection with the configured provider."""
        web3 = Web3(HTTPProvider(settings.SEPOLIA_URL))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3
    
    def _initialize_contract(self):
        """Initialize the AINFTVault contract instance."""
        # Load contract ABI from the artifacts directory
        contract_abi_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'artifacts', 
            'smart-contracts', 
            'AINFTVault.sol', 
            'AINFTVault.json'
        )
        
        with open(contract_abi_path, 'r') as f:
            contract_data = json.load(f)
            
        contract_abi = contract_data.get('abi', [])
        return self.web3.eth.contract(
            address=Web3.to_checksum_address(settings.CONTRACT_ADDRESS),
            abi=contract_abi
        )
    
    def _create_agent(self) -> Agent:
        """Create and configure the PriceExecutionAgent."""
        return Agent(
            role="Blockchain Transaction Executor",
            goal="Safely execute price updates and other transactions on the blockchain",
            backstory="""You are a reliable blockchain transaction executor with expertise in 
            smart contract interactions. Your role is to ensure that pricing decisions are 
            accurately and securely executed on the blockchain with proper gas management 
            and transaction validation.""",
            verbose=True,
            tools=self.tools,
            allow_delegation=False
        )
    
    def execute_price_update(self, new_price_wei: int, gas_price_wei: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a price update on the AINFTVault contract.
        
        Args:
            new_price_wei (int): New minimum price in wei
            gas_price_wei (int, optional): Gas price in wei. If None, it will be estimated.
            
        Returns:
            dict: Transaction receipt or error information
        """
        try:
            # Get the account from the private key
            account = Account.from_key(settings.METAMASK_PRIVATE_KEY)
            nonce = self.web3.eth.get_transaction_count(account.address)
            
            # Build the transaction
            tx = self.contract.functions.setMinimumPrice(new_price_wei).build_transaction({
                'chainId': 11155111,  # Sepolia chain ID
                'gas': 200000,  # Adjust based on contract requirements
                'gasPrice': gas_price_wei or self.web3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign the transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=settings.METAMASK_PRIVATE_KEY)
            
            # Send the transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for the transaction to be mined
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                "status": "success",
                "transaction_hash": tx_hash.hex(),
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def validate_price_update(self, current_price_wei: int, new_price_wei: int) -> Dict[str, Any]:
        """
        Validate if a price update is reasonable.
        
        Args:
            current_price_wei (int): Current price in wei
            new_price_wei (int): Proposed new price in wei
            
        Returns:
            dict: Validation result with 'is_valid' and 'reason' fields
        """
        # This is a simplified validation - in a real implementation, you might want to:
        # 1. Check price change percentage
        # 2. Check recent price trends
        # 3. Consider market conditions
        # 4. Check gas costs vs. price change
        
        # For now, just do a basic validation
        if new_price_wei <= 0:
            return {"is_valid": False, "reason": "Price must be greater than zero"}
            
        if new_price_wei == current_price_wei:
            return {"is_valid": False, "reason": "New price is the same as current price"}
            
        # Check for extreme price changes (more than 100x)
        max_change = max(current_price_wei * 100, current_price_wei / 100)
        if new_price_wei > max_change or new_price_wei < (current_price_wei / 100):
            return {
                "is_valid": False, 
                "reason": f"Price change too extreme (current: {current_price_wei}, new: {new_price_wei})"
            }
            
        return {"is_valid": True, "reason": "Price update is reasonable"}
