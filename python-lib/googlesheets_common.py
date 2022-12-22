def extract_credentials(config):
    auth_type = config.get("auth_type", "legacy-service-account")

    if auth_type == "legacy-service-account":
        # Legacy mode
        credentials = config.get("credentials")
        return credentials, "service-account"
    elif auth_type == "preset-service-account":
        preset_credentials_service_account = config.get("preset_credentials_service_account", {})
        credentials = preset_credentials_service_account.get("credentials", None)
        return credentials, "service-account"
    elif auth_type == "single-sign-on":
        oauth_credentials = config.get("oauth_credentials", {})
        access_token = oauth_credentials.get("access_token", None)
        return access_token, "personnal-account"
    return None, None
