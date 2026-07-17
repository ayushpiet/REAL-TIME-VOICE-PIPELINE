import json
import os
from datetime import datetime
from loguru import logger

LEADS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "leads.json"))

async def save_lead(params, name: str, phone: str):
    logger.info(f"ACTIONABLE AI: Triggered 'save_lead' tool! Name: {name}, Phone: {phone}")
    
    lead_entry = {
        "timestamp": datetime.now().isoformat(),
        "name": name,
        "phone": phone
    }
    
    try:
        leads = []
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    leads = json.loads(content)
        
        leads.append(lead_entry)
        
        with open(LEADS_FILE, "w") as f:
            json.dump(leads, f, indent=4)
            
        logger.info(f"Lead saved successfully to {LEADS_FILE}")
        
        # Return success back to the LLM so it can inform the user
        if getattr(params, "result_callback", None):
            await params.result_callback({"status": "success", "message": "Lead saved successfully."})
        
    except Exception as e:
        logger.error(f"Failed to save lead: {e}")
        if getattr(params, "result_callback", None):
            await params.result_callback({"status": "error", "message": "Failed to save lead."})
