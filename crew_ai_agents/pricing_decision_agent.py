from crewai import Agent
from crewai_tools import BaseTool
from typing import List, Optional, Dict, Any
import json
from config.settings import settings

class PricingDecisionAgent:
    def __init__(self, tools: Optional[List[BaseTool]] = None):
        self.tools = tools or []
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create and configure the PricingDecisionAgent."""
        return Agent(
            role="Pricing Strategist",
            goal="Analyze market conditions and vault metrics to determine optimal pricing strategies",
            backstory="""You are an expert in market analysis and pricing strategies for digital assets. 
            Your role is to analyze transaction history, market conditions, and vault metrics to 
            recommend optimal pricing strategies for NFTs in the AINFTVault.""",
            verbose=True,
            tools=self.tools,
            allow_delegation=True,
            memory=True
        )
    
    def analyze_market_conditions(self, vault_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market conditions and recommend pricing strategy.
        
        Args:
            vault_metrics (dict): Current metrics from the vault
            
        Returns:
            dict: Pricing strategy recommendations
        """
        # Prepare the context for the agent
        context = {
            "vault_metrics": vault_metrics,
            "current_market_conditions": "Analyze recent transaction volume and pricing trends"
        }
        
        # Execute the agent's analysis
        analysis = self.agent.execute_task(
            task=f"""Analyze the current market conditions and vault metrics to determine 
                  the optimal pricing strategy. Consider the following metrics: {vault_metrics}.
                  Provide specific recommendations for price adjustments based on the data.""",
            context=context
        )
        
        # Parse the agent's response into a structured format
        try:
            # Try to parse JSON if the agent returns structured data
            return json.loads(analysis)
        except json.JSONDecodeError:
            # If not JSON, return as text
            return {"analysis": analysis}
    
    def get_price_recommendation(self, nft_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get price recommendation for a specific NFT or for new mints.
        
        Args:
            nft_id (str, optional): ID of the NFT to price. If None, price for new mints.
            
        Returns:
            dict: Price recommendation with justification
        """
        task = f"""Provide a detailed price recommendation for {"NFT ID: " + nft_id if nft_id else "a new NFT mint"}.
                 Consider factors like rarity, transaction history, and current market conditions.
                 Return your recommendation in a structured format with 'recommended_price' and 'justification'."""
        
        result = self.agent.execute_task(task)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "recommended_price": None,
                "justification": result,
                "error": "Could not parse agent response as JSON"
            }
