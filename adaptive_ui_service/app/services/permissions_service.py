import asyncio
import json
from dataclasses import dataclass

from adaptive_ui_service.app.core.openproject_client import OpenProjectClient


@dataclass
class Membership:
    project_id: int
    project_name: str
    role_ids: list[int]


@dataclass
class PermissionSet:
    user_id: int
    project_id: int
    permissions: list[str]


def _extract_project_id(href: str) -> int:
    return int(href.rstrip("/").split("/")[-1])


def _extract_role_ids(element: dict) -> list[int]:
    embedded_roles = element.get("_embedded", {}).get("roles", [])
    if embedded_roles:
        return [role["id"] for role in embedded_roles]

    link_roles = element.get("_links", {}).get("roles", [])
    return [_extract_project_id(role["href"]) for role in link_roles]


async def get_user_memberships(
    user_id: int, client: OpenProjectClient
) -> list[Membership]:
    filters = json.dumps([{"principal": {"operator": "=", "values": [str(user_id)]}}])
    data = await client.get("/api/v3/memberships", params={"filters": filters})

    elements = data.get("_embedded", {}).get("elements", [])
    memberships = []

    for element in elements:
        project_link = element["_links"]["project"]
        memberships.append(
            Membership(
                project_id=_extract_project_id(project_link["href"]),
                project_name=project_link.get("title", ""),
                role_ids=_extract_role_ids(element),
            )
        )

    return memberships


async def get_role_permissions(role_id: int, client: OpenProjectClient) -> list[str]:
    data = await client.get(f"/api/v3/roles/{role_id}")
    return data.get("permissions", [])


async def get_user_permissions(
    user_id: int, project_id: int, client: OpenProjectClient
) -> PermissionSet:
    memberships = await get_user_memberships(user_id, client)
    project_membership = next(
        (
            membership
            for membership in memberships
            if membership.project_id == project_id
        ),
        None,
    )

    if project_membership is None:
        return PermissionSet(user_id=user_id, project_id=project_id, permissions=[])

    role_permissions_lists = await asyncio.gather(
        *[
            get_role_permissions(role_id, client)
            for role_id in project_membership.role_ids
        ]
    )

    seen: set[str] = set()
    permissions: list[str] = []
    for role_permissions in role_permissions_lists:
        for permission in role_permissions:
            if permission not in seen:
                seen.add(permission)
                permissions.append(permission)

    return PermissionSet(
        user_id=user_id,
        project_id=project_id,
        permissions=permissions,
    )
