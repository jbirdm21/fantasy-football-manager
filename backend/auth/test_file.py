
# Test file for task: Authentication flow
# Task ID: task-184684eb-012f-466f-8b0d-24632110182a

def get_auth_config():
    """
    Returns authentication configuration.
    
    This is a test function created for task: Authentication flow
    """
    return {
        "auth_enabled": True,
        "oauth_providers": ["google", "github"],
        "jwt_expiration": 3600,
        "refresh_token_expiration": 86400
    }
