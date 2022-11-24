def get_credentials(config):
    auth_type = config.get("auth_type", "credentials")

    if auth_type == "credentials":
        # Legacy mode
        credentials = config.get("credentials")
        return credentials
    elif auth_type == "service-account":
        preset_credentials = config.get("preset_credentials", {})
        credentials = preset_credentials.get("credentials", None)
        return credentials
    return None
