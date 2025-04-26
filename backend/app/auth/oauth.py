from authlib.integrations.starlette_client import OAuth
import secrets
import string

from ..config import settings

oauth = OAuth()

# Setup OAuth providers
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


# Function to generate a random username for social users
def generate_username(prefix="user"):
    random_suffix = "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )
    return f"{prefix}_{random_suffix}"
