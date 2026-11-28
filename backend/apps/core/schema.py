def filter_versioned_api_paths(endpoints):
    return [
        endpoint
        for endpoint in endpoints
        if endpoint[0].startswith("/api/v1/")
    ]
