"""Firebase Authentication implementation."""

from typing import Dict, Any, Optional
from firebase_admin import auth, credentials, initialize_app
from ...core.ports import AbstractAuthService


class AuthenticationError(Exception):
    """Authentication failed."""

    pass


class FirebaseAuthService(AbstractAuthService):
    """Firebase Authentication service."""

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Firebase Auth service.

        Args:
            credentials_path: Path to Firebase credentials JSON (optional)
        """
        # Initialize Firebase Admin SDK
        if credentials_path:
            cred = credentials.Certificate(credentials_path)
            initialize_app(cred)
        else:
            # Use application default credentials
            try:
                initialize_app()
            except ValueError:
                # Already initialized
                pass

        self.user_tiers: Dict[str, str] = {}  # Cache for user tiers

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token.

        Args:
            token: Firebase ID token

        Returns:
            Decoded token with user information

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Verify the token
            decoded_token = auth.verify_id_token(token)

            return {
                "uid": decoded_token["uid"],
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name"),
                "email_verified": decoded_token.get("email_verified", False),
                "user_id": decoded_token["uid"],
            }

        except auth.InvalidIdTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")
        except auth.ExpiredIdTokenError as e:
            raise AuthenticationError(f"Token expired: {e}")
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {e}")

    async def get_user_tier(self, user_id: str) -> str:
        """
        Get user's subscription tier.

        Args:
            user_id: User identifier

        Returns:
            Tier name (e.g., 'free', 'premium', 'enterprise')
        """
        # Check cache first
        if user_id in self.user_tiers:
            return self.user_tiers[user_id]

        try:
            # Get user from Firebase
            user = auth.get_user(user_id)

            # Check custom claims for tier
            custom_claims = user.custom_claims or {}
            tier = custom_claims.get("tier", "free")

            # Cache the tier
            self.user_tiers[user_id] = tier

            return tier

        except Exception as e:
            # Default to free tier on error
            print(f"Error getting user tier: {e}")
            return "free"


class MockAuthService(AbstractAuthService):
    """Mock authentication service for testing/development."""

    def __init__(self):
        """Initialize mock auth service."""
        self.valid_tokens = {
            "test-token-123": {
                "uid": "test-user-1",
                "email": "test@example.com",
                "name": "Test User",
                "user_id": "test-user-1",
            }
        }
        self.user_tiers = {
            "test-user-1": "premium",
        }

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify mock token."""
        if token in self.valid_tokens:
            return self.valid_tokens[token]

        if token.startswith("valid-"):
            # Generate user info for any valid- prefix
            return {
                "uid": f"user-{token[6:]}",
                "email": f"{token[6:]}@example.com",
                "name": f"User {token[6:]}",
                "user_id": f"user-{token[6:]}",
            }

        raise AuthenticationError("Invalid token")

    async def get_user_tier(self, user_id: str) -> str:
        """Get user tier."""
        return self.user_tiers.get(user_id, "free")
