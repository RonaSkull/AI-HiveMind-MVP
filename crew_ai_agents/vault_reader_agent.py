import json
import logging
from typing import List, Optional, Dict, Any
from crewai import Agent
from crewai.tools import BaseTool
from config import settings
from crew_ai_tools.vault_reader_tool import VaultReaderTool

# Set up logging
logger = logging.getLogger(__name__)

class VaultReaderAgent:
    def __init__(self, tools: Optional[List[BaseTool]] = None):
        """Initialize the VaultReaderAgent with optional custom tools."""
        self.tools = tools or self._get_default_tools()
        self.agent = self._create_agent()
        self.vault_reader = self._get_vault_reader_tool()
        
        logger.info("VaultReaderAgent initialized")
    
    def _get_vault_reader_tool(self) -> VaultReaderTool:
        """Get the VaultReaderTool instance from the agent's tools."""
        for tool in self.tools:
            if isinstance(tool, VaultReaderTool):
                return tool
        raise ValueError("VaultReaderTool not found in agent's tools")
    
    def _get_default_tools(self) -> List[BaseTool]:
        """Initialize and return the default tools for the VaultReaderAgent."""
        vault_reader = VaultReaderTool()
        return [vault_reader]
    
    def _create_agent(self) -> Agent:
        """Create and configure the VaultReaderAgent."""
        return Agent(
            role="Vault Data Analyst",
            goal="Retrieve and analyze data from the AINFTVault smart contract",
            backstory="""You are an expert at analyzing blockchain data and smart contract interactions. 
            Your role is to fetch and interpret data from the AINFTVault contract to provide insights 
            about NFT holdings, transactions, and contract state. You have deep knowledge of Ethereum 
            smart contracts and can interpret complex blockchain data structures.""",
            verbose=settings.LOG_LEVEL.lower() == 'debug',
            tools=self.tools,
            allow_delegation=False,
            memory=True
        )
    
    def get_contract_info(self) -> Dict[str, Any]:
        """Get basic information about the connected contract."""
        return self.vault_reader.get_contract_info()
    
    def call_contract_function(self, function_name: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Call a function on the AINFTVault contract.
        
        Args:
            function_name: Name of the contract function to call
            params: Dictionary of parameters for the function
            
        Returns:
            dict: Result of the function call
        """
        try:
            result = self.vault_reader._run(function_name, params or {})
            return json.loads(result)
        except json.JSONDecodeError:
            return {"status": "error", "message": "Failed to parse contract response"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_vault_metrics(self) -> Dict[str, Any]:
        """Get key metrics from the AINFTVault contract."""
        metrics = {}
        
        # Get basic contract info
        contract_info = self.get_contract_info()
        metrics["contract_info"] = contract_info
        
        # Get common metrics
        common_functions = [
            "totalSupply", 
            "getMinimumPrice", 
            "getTotalTransactions",
            "getBaseURI"
        ]
        
        for func in common_functions:
            try:
                result = self.call_contract_function(func)
                if result.get("status") == "success":
                    metrics[func] = result.get("data")
            except Exception as e:
                logger.warning(f"Failed to call {func}: {str(e)}")
        
        return metrics
    
    def analyze_vault_data(self, query: str) -> Dict[str, Any]:
        """
        Analyze vault data based on the given query using the agent.
        
        Args:
            query: The query about the vault data
            
        Returns:
            dict: Analysis of the vault data
        """
        try:
            # First, gather all relevant data
            metrics = self.get_vault_metrics()
            
            # Format the context for the agent
            context = {
                "contract_address": self.vault_reader.contract_address,
                "network": {
                    "chain_id": metrics.get("contract_info", {}).get("network", {}).get("chain_id"),
                    "block_number": metrics.get("contract_info", {}).get("network", {}).get("block_number")
                },
                "metrics": {
                    "total_supply": metrics.get("totalSupply"),
                    "minimum_price": metrics.get("getMinimumPrice"),
                    "total_transactions": metrics.get("getTotalTransactions"),
                    "base_uri": metrics.get("getBaseURI")
                },
                "available_functions": [
                    func for func in metrics.get("contract_info", {}).get("abi_functions", [])
                ]
            }
            
            # Execute the agent with the context
            task = f"""
            Analyze the following vault data and provide insights based on the query:
            
            Query: {query}
            
            Context:
            {json.dumps(context, indent=2)}
            
            Provide a detailed analysis with specific metrics and actionable insights.
            """
            
            result = self.agent.execute_task(task)
            
            return {
                "status": "success",
                "analysis": result,
                "context": context
            }
            
        except Exception as e:
            error_msg = f"Failed to analyze vault data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
