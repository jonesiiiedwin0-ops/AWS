"""IAM service integration."""

from typing import Any, Callable, Dict

from .base import BaseService


class IAMService(BaseService):
    """Identity and Access Management operations."""

    service_name = "iam"
    display_name = "IAM"
    description = "Identity and Access Management - users, roles, and policies"

    def _build_tools(self) -> Dict[str, Callable]:
        return {
            "list_users": self.list_users,
            "get_user": self.get_user,
            "list_roles": self.list_roles,
            "list_attached_user_policies": self.list_attached_user_policies,
        }

    async def list_users(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List IAM users."""
        client = self.get_client(params.get("region"))
        response = client.list_users(MaxItems=params.get("max_items", 100))
        users = [
            {
                "username": u.get("UserName"),
                "user_id": u.get("UserId"),
                "arn": u.get("Arn"),
                "created": str(u.get("CreateDate")),
            }
            for u in response.get("Users", [])
        ]
        return {"count": len(users), "users": users}

    async def get_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a single IAM user."""
        client = self.get_client(params.get("region"))
        kwargs: Dict[str, Any] = {}
        if username := params.get("username"):
            kwargs["UserName"] = username
        response = client.get_user(**kwargs)
        user = response.get("User", {})
        return {
            "username": user.get("UserName"),
            "user_id": user.get("UserId"),
            "arn": user.get("Arn"),
            "created": str(user.get("CreateDate")),
        }

    async def list_roles(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List IAM roles."""
        client = self.get_client(params.get("region"))
        response = client.list_roles(MaxItems=params.get("max_items", 100))
        roles = [
            {
                "role_name": r.get("RoleName"),
                "role_id": r.get("RoleId"),
                "arn": r.get("Arn"),
                "created": str(r.get("CreateDate")),
            }
            for r in response.get("Roles", [])
        ]
        return {"count": len(roles), "roles": roles}

    async def list_attached_user_policies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List managed policies attached to a user."""
        client = self.get_client(params.get("region"))
        response = client.list_attached_user_policies(UserName=params["username"])
        policies = [
            {"name": p.get("PolicyName"), "arn": p.get("PolicyArn")}
            for p in response.get("AttachedPolicies", [])
        ]
        return {"count": len(policies), "policies": policies}
