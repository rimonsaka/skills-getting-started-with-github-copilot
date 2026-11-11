from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    with TestClient(app) as test_client:
        yield test_client
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activity_data = response.json()
    assert set(activity_data) == set(activities)
    assert activity_data["Chess Club"] == activities["Chess Club"]


def test_signup_adds_student_to_activity(client):
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_signup_rejects_duplicate_registration(client):
    email = activities["Chess Club"]["participants"][0]

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "You are already signed up for this activity"
    }
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_unregister_removes_registered_student(client):
    email = activities["Chess Club"]["participants"][0]

    response = client.delete(f"/activities/Chess Club/participants/{email}")

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Chess Club"
    }
    assert email not in activities["Chess Club"]["participants"]


@pytest.mark.parametrize(
    ("method", "url", "params"),
    [
        ("post", "/activities/Unknown Club/signup", {"email": "student@example.com"}),
        ("delete", "/activities/Unknown Club/participants/student@example.com", None),
    ],
)
def test_requests_for_unknown_activity_return_not_found(client, method, url, params):
    response = getattr(client, method)(url, params=params)

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_student_not_registered_for_activity(client):
    response = client.delete(
        "/activities/Chess Club/participants/not-registered@example.com"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not registered for this activity"
    }


def test_signup_requires_email_query_parameter(client):
    response = client.post("/activities/Chess Club/signup")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]
