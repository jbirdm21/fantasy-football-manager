
# Test file for task: Secrets management
# Task ID: task-039c1290-a4bb-40cb-98b0-4a5ca2d11ec7

def get_auth_config():
    """
    Returns authentication configuration.
    
    This is a test function created for task: Secrets management
    """
    return {
        "auth_enabled": True,
        "oauth_providers": ["google", "github"],
        "jwt_expiration": 3600,
        "refresh_token_expiration": 86400
    }
