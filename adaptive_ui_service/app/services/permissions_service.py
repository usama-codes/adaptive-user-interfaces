import json
from dataclasses import dataclass

from adaptive_ui_service.app.core.openproject_client import OpenProjectClient


@dataclass
class Membership:
    project_id: int
    project_name: str
    role_ids: list[int]


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
