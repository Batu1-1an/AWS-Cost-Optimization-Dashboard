import boto3
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Fetch credentials and region from environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1") # Default to us-east-1 if not set

# Module-level variable to hold the session once created
_session = None
def get_aws_session():
    """
    Returns the Boto3 session, creating it lazily if it doesn't exist.
    Ensures session creation happens after potential patching (e.g., by moto).
    """
    global _session
    if _session is None:
        logging.info("Creating new AWS session...")
        # Fetch credentials again inside the function to ensure they are current
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1")

        if not aws_access_key_id or not aws_secret_access_key:
            logging.error("AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) not found in environment variables during session creation.")
            # Cannot create a session without credentials
            return None
        else:
            try:
                _session = boto3.Session(
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=aws_region
                )
                logging.info(f"AWS session created successfully for region {aws_region}.")
            except Exception as e:
                logging.error(f"Failed to create AWS session: {e}")
                _session = None # Ensure it remains None on failure

    if _session is None:
         logging.warning("Attempting to get AWS session, but it could not be initialized successfully.")

    return _session

def get_client(service_name, region_name=None):
    """
    Gets a Boto3 client for the specified service.

    Args:
        service_name (str): The name of the AWS service (e.g., 'ec2', 'ce', 'cloudwatch').
        region_name (str, optional): The region for the client. Defaults to the session's region.

    Returns:
        boto3.client: The Boto3 client instance, or None if the session is invalid.
    """
    session = get_aws_session()
    if not session:
        logging.error(f"Cannot get client for '{service_name}': AWS session is invalid.")
        return None
    try:
        client = session.client(service_name, region_name=region_name or AWS_REGION)
        logging.debug(f"Successfully obtained client for '{service_name}' in region '{region_name or AWS_REGION}'.")
        return client
    except Exception as e:
        logging.error(f"Failed to get client for '{service_name}': {e}")
        return None

# Example usage (optional, for testing this module directly)
if __name__ == '__main__':
    logging.info("Attempting to get clients...")
    ce_client = get_client('ce') # Cost Explorer client
    ec2_client = get_client('ec2') # EC2 client
    cw_client = get_client('cloudwatch') # CloudWatch client

    if ce_client:
        logging.info("Cost Explorer client obtained.")
    if ec2_client:
        logging.info("EC2 client obtained.")
    if cw_client:
        logging.info("CloudWatch client obtained.")

    # Attempt to get the session to trigger initialization if needed
    session = get_aws_session()
    if not session:
        logging.warning("AWS Session could not be initialized. Check .env file and credentials.")