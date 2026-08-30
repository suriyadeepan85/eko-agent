"""
AWS Bedrock client creation with Streamlit Cloud support.

Supports both local development (AWS credential chain) and Streamlit Cloud
(credentials from st.secrets). Does not hardcode any credential values.
"""

import os
import boto3


def get_bedrock_client():
    """Create Bedrock runtime client with environment-appropriate credentials.

    Priority order:
    1. Streamlit secrets (if running in Streamlit and secrets are configured)
    2. Environment variables (AWS_ACCESS_KEY_ID, etc.)
    3. AWS credential chain (IAM roles, ~/.aws/credentials, etc.)

    Returns:
        boto3 bedrock-runtime client
    """
    # Try to import streamlit (only available when running in Streamlit)
    try:
        import streamlit as st

        # Check if running in Streamlit and secrets are configured
        if hasattr(st, 'secrets'):
            try:
                if 'AWS_ACCESS_KEY_ID' in st.secrets:
                    # Running on Streamlit Cloud with configured secrets
                    return boto3.client(
                        "bedrock-runtime",
                        aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
                        aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'],
                        region_name=st.secrets.get('AWS_REGION', 'us-east-1')
                    )
            except Exception:
                # Secrets not configured, fall through to credential chain
                pass
    except (ImportError, AttributeError):
        # Streamlit not available or not running in Streamlit context
        pass

    # Fall back to environment variables or AWS credential chain
    region = os.environ.get('AWS_REGION', 'us-east-1')
    return boto3.client("bedrock-runtime", region_name=region)


def get_model_id() -> str:
    """Get Bedrock model ID from configuration.

    Priority order:
    1. Streamlit secrets (BEDROCK_MODEL_ID)
    2. Environment variable (ANTHROPIC_MODEL or BEDROCK_MODEL_ID)
    3. Default model

    Returns:
        Model ID string
    """
    # Try Streamlit secrets first
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            try:
                if 'BEDROCK_MODEL_ID' in st.secrets:
                    return st.secrets['BEDROCK_MODEL_ID']
            except Exception:
                pass
    except (ImportError, AttributeError):
        pass

    # Fall back to environment variables
    return os.environ.get(
        'ANTHROPIC_MODEL',
        os.environ.get(
            'BEDROCK_MODEL_ID',
            'us.anthropic.claude-sonnet-4-5-20250929-v1:0'
        )
    )
