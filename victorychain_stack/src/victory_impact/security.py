from typing import Callable

from fastapi import Depends, Header, HTTPException


ROLE_TOKENS = {
    "donor-token": "donor",
    "admin-token": "admin",
    "board-token": "board",
    "compliance-token": "compliance",
}


def current_role(x_api_token: str = Header(default="donor-token")) -> str:
    role = ROLE_TOKENS.get(x_api_token)
    if not role:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return role


def require_role(*allowed_roles: str) -> Callable[[str], str]:
    def checker(role: str = Depends(current_role)) -> str:  # pragma: no cover
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return role

    return checker
