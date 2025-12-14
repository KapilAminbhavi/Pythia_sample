from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
import os

# Initialize rate limiter with Redis from environment variable
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "redis://redis:6379/0")
)


def get_tenant_id(request: Request) -> str:
    """
    Extract tenant_id from request for tenant-based rate limiting.
    Tries multiple sources: body, query params, headers.
    """
    # Try from request body (for POST requests)
    if hasattr(request, '_json'):
        return request._json.get('tenant_id', 'default')

    # Try from query params
    tenant_id = request.query_params.get('tenant_id')
    if tenant_id:
        return tenant_id

    # Try from headers
    tenant_id = request.headers.get('X-Tenant-ID')
    if tenant_id:
        return tenant_id

    # Default fallback
    return 'default'