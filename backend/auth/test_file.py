
# Test file for task: OAuth flow
# Task ID: task-086dee3f-1968-4b9f-8e99-be873ea9e957

def get_auth_config():
    """
    Returns authentication configuration.
    
    This is a test function created for task: OAuth flow
    """
    return {
        "auth_enabled": True,
        "oauth_providers": ["google", "github"],
        "jwt_expiration": 3600,
        "refresh_token_expiration": 86400
    }
