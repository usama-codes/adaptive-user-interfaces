import httpx
import pytest
import respx

from adaptive_ui_service.app.core import exceptions
from adaptive_ui_service.app.core.openproject_client import OpenProjectClient
from adaptive_ui_service.app.services import permissions_service


@pytest.mark.asyncio
@respx.mock
async def test_user_with_memberships_in_two_projects() -> None:
    route = respx.get("http://testserver/api/v3/memberships").mock(
        return_value=httpx.Response(
            200,
            json={
                "_type": "Collection",
                "total": 2,
                "count": 2,
                "_embedded": {
                    "elements": [
                        {
                            "_type": "Membership",
                            "id": 1,
                            "_links": {
                                "project": {
                                    "href": "/api/v3/projects/5",
                                    "title": "Alpha",
                                },
                                "roles": [
                                    {
                                        "href": "/api/v3/roles/3",
                                        "title": "Member",
                                    }
                                ],
                            },
                            "_embedded": {
                                "roles": [
                                    {
                                        "_type": "Role",
                                        "id": 3,
                                        "name": "Member",
                                    }
                                ]
                            },
                        },
                        {
                            "_type": "Membership",
                            "id": 2,
                            "_links": {
                                "project": {
                                    "href": "/api/v3/projects/10",
                                    "title": "Beta",
                                },
                                "roles": [
                                    {
                                        "href": "/api/v3/roles/3",
                                        "title": "Member",
                                    },
                                    {
                                        "href": "/api/v3/roles/7",
                                        "title": "Manager",
                                    },
                                ],
                            },
                            "_embedded": {
                                "roles": [
                                    {
                                        "_type": "Role",
                                        "id": 3,
                                        "name": "Member",
                                    },
                                    {
                                        "_type": "Role",
                                        "id": 7,
                                        "name": "Manager",
                                    },
                                ]
                            },
                        },
                    ]
                },
            },
        ),
    )
    client = OpenProjectClient(base_url="http://testserver", api_token="test-token")

    try:
        result = await permissions_service.get_user_memberships(
            user_id=14, client=client
        )
    finally:
        await client.close()

    assert result == [
        permissions_service.Membership(
            project_id=5, project_name="Alpha", role_ids=[3]
        ),
        permissions_service.Membership(
            project_id=10, project_name="Beta", role_ids=[3, 7]
        ),
    ]
    assert route.calls[0].request.url.params["filters"] == (
        '[{"principal": {"operator": "=", "values": ["14"]}}]'
    )


@pytest.mark.asyncio
@respx.mock
async def test_user_with_no_memberships() -> None:
    respx.get("http://testserver/api/v3/memberships").mock(
        return_value=httpx.Response(
            200,
            json={
                "_type": "Collection",
                "total": 0,
                "count": 0,
                "_embedded": {"elements": []},
            },
        )
    )
    client = OpenProjectClient(base_url="http://testserver", api_token="test-token")

    try:
        result = await permissions_service.get_user_memberships(
            user_id=14, client=client
        )
    finally:
        await client.close()

    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_api_error_propagation() -> None:
    respx.get("http://testserver/api/v3/memberships").mock(
        return_value=httpx.Response(500, text="server error")
    )
    client = OpenProjectClient(base_url="http://testserver", api_token="test-token")

    try:
        with pytest.raises(exceptions.OpenProjectAPIError) as error:
            await permissions_service.get_user_memberships(user_id=14, client=client)
    finally:
        await client.close()

    assert error.value.status_code == 500


@pytest.mark.asyncio
@respx.mock
async def test_overlapping_permissions_are_deduplicated() -> None:
    respx.get("http://testserver/api/v3/memberships").mock(
        return_value=httpx.Response(
            200,
            json={
                "_embedded": {
                    "elements": [
                        {
                            "_links": {
                                "project": {
                                    "href": "/api/v3/projects/5",
                                    "title": "Alpha",
                                }
                            },
                            "_embedded": {
                                "roles": [
                                    {"id": 3},
                                    {"id": 7},
                                ]
                            },
                        }
                    ]
                }
            },
        )
    )
    respx.get("http://testserver/api/v3/roles/3").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 3,
                "permissions": ["view_work_packages", "edit_work_packages"],
            },
        )
    )
    respx.get("http://testserver/api/v3/roles/7").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 7,
                "permissions": ["view_work_packages", "manage_members"],
            },
        )
    )
    client = OpenProjectClient(base_url="http://testserver", api_token="test-token")

    try:
        result = await permissions_service.get_user_permissions(
            user_id=14, project_id=5, client=client
        )
    finally:
        await client.close()

    assert result == permissions_service.PermissionSet(
        user_id=14,
        project_id=5,
        permissions=[
            "view_work_packages",
            "edit_work_packages",
            "manage_members",
        ],
    )


@pytest.mark.asyncio
@respx.mock
async def test_non_member_returns_empty_permission_set() -> None:
    memberships_route = respx.get("http://testserver/api/v3/memberships").mock(
        return_value=httpx.Response(
            200,
            json={"_embedded": {"elements": []}},
        )
    )
    roles_route = respx.get(url__regex=r".*/api/v3/roles/.*").mock(
        return_value=httpx.Response(200, json={"permissions": []})
    )
    client = OpenProjectClient(base_url="http://testserver", api_token="test-token")

    try:
        result = await permissions_service.get_user_permissions(
            user_id=14, project_id=5, client=client
        )
    finally:
        await client.close()

    assert result == permissions_service.PermissionSet(
        user_id=14, project_id=5, permissions=[]
    )
    assert memberships_route.called
    assert not roles_route.called


@pytest.mark.asyncio
@respx.mock
async def test_role_fetch_error_propagates() -> None:
    respx.get("http://testserver/api/v3/memberships").mock(
        return_value=httpx.Response(
            200,
            json={
                "_embedded": {
                    "elements": [
                        {
                            "_links": {"project": {"href": "/api/v3/projects/5"}},
                            "_embedded": {"roles": [{"id": 3}]},
                        }
                    ]
                }
            },
        )
    )
    respx.get("http://testserver/api/v3/roles/3").mock(
        return_value=httpx.Response(500, text="server error")
    )
    client = OpenProjectClient(
        base_url="http://testserver", api_token="test-token", max_retries=0
    )

    try:
        with pytest.raises(exceptions.OpenProjectAPIError) as error:
            await permissions_service.get_user_permissions(
                user_id=14, project_id=5, client=client
            )
    finally:
        await client.close()

    assert error.value.status_code == 500
