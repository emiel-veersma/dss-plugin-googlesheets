def get_credentials(config):
    auth_type = config.get("auth_type", "credentials")

    if auth_type == "credentials":
        # Legacy mode
        credentials = config.get("credentials")
        return credentials, "service-account"
    elif auth_type == "service-account":
        preset_credentials = config.get("preset_credentials", {})
        credentials = preset_credentials.get("credentials", None)
        return credentials, "service-account"
    elif auth_type == "single-sign-on":
        oauth_credentials = config.get("oauth_credentials", {})
        access_token = oauth_credentials.get("access_token", None)
        return access_token, "personnal-account"
    return None, None
