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

# Basic validation
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    logging.error("AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) not found in environment variables.")
    # In a real app, you might raise an exception or handle this more gracefully
    # For now, we'll allow it to proceed, but boto3 calls will likely fail.
    SESSION = None
else:
    try:
        SESSION = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        logging.info(f"AWS session created successfully for region {AWS_REGION}.")
    except Exception as e:
        logging.error(f"Failed to create AWS session: {e}")
        SESSION = None

def get_aws_session():
    """Returns the initialized Boto3 session."""
    if SESSION is None:
        logging.warning("Attempting to get AWS session, but it was not initialized successfully.")
    return SESSION

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

    if not SESSION:
        logging.warning("AWS Session could not be initialized. Check .env file and credentials.")