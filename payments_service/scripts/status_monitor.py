import requests
import redis
import os
import time
import logging
import xml.etree.ElementTree as ET

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STRIPE_RSS_URL = "https://www.stripestatus.com/history.rss"
ADYEN_STATUS_URL = "https://www.adyen.com" # Placeholder for heartbeat

def check_stripe():
    try:
        response = requests.get(STRIPE_RSS_URL, timeout=10)
        if response.status_code == 200:
            # Simple check: search for "resolved" or monitor recent items
            # For this prototype, if it's reachable and doesn't contain "Investigating" in top item, it's UP.
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            if not items:
                return "up"
            
            latest_title = items[0].find('title').text
            if "Investigating" in latest_title or "Identified" in latest_title:
                 return "down"
            return "up"
    except Exception as e:
        logger.error(f"Error checking Stripe: {e}")
    return "down"

def check_adyen():
    try:
        response = requests.get(ADYEN_STATUS_URL, timeout=10)
        return "up" if response.status_code == 200 else "down"
    except Exception as e:
        logger.error(f"Error checking Adyen: {e}")
    return "down"

def main():
    redis_client = redis.from_url(REDIS_URL)
    
    while True:
        logger.info("Checking provider health...")
        stripe_health = check_stripe()
        adyen_health = check_adyen()
        
        # Store in Redis
        redis_client.set("provider_health:stripe", stripe_health)
        redis_client.set("provider_health:adyen", adyen_health)
        
        logger.info(f"Health status updated: Stripe={stripe_health}, Adyen={adyen_health}")
        
        # Poll every 5 minutes (for prototype, we'll just run once or loop with sleep)
        time.sleep(300)

if __name__ == "__main__":
    main()
