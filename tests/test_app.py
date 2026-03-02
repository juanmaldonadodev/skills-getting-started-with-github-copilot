import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: keep a pristine copy of the in-memory database.

    This fixture runs before each test, replacing `app.activities` with a
    deep copy of its original state so tests don't affect one another.
    """
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities():
    # Arrange: fixture has already reset state

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activities


def test_signup_success():
    # Arrange
    activity = next(iter(activities.keys()))
    email = "newstudent@example.com"

    # Act
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert resp.status_code == 200
    assert f"Signed up {email} for {activity}" in resp.json()["message"]
    assert email in activities[activity]["participants"]


def test_signup_nonexistent_activity():
    # Arrange
    bogus = "Nonexistent Club"
    email = "someone@example.com"

    # Act
    resp = client.post(f"/activities/{bogus}/signup", params={"email": email})

    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_signup_already_registered():
    # Arrange
    activity, info = next(((a, v) for a, v in activities.items() if v["participants"]))
    email = info["participants"][0]

    # Act
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student already signed up"


def test_unregister_success():
    # Arrange
    activity, info = next(((a, v) for a, v in activities.items() if v["participants"]))
    email = info["participants"][0]

    # Act
    resp = client.delete(f"/activities/{activity}/unregister", params={"email": email})

    # Assert
    assert resp.status_code == 200
    assert f"Unregistered {email} from {activity}" in resp.json()["message"]
    assert email not in activities[activity]["participants"]


def test_unregister_not_registered():
    # Arrange
    activity = next(iter(activities.keys()))
    email = "absent@example.com"

    # Act
    resp = client.delete(f"/activities/{activity}/unregister", params={"email": email})

    # Assert
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student not registered for this activity"


def test_unregister_nonexistent_activity():
    # Arrange
    bogus = "Ghost Club"
    email = "nobody@example.com"

    # Act
    resp = client.delete(f"/activities/{bogus}/unregister", params={"email": email})

    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_root_redirect():
    # Arrange: none

    # Act
    resp = client.get("/", follow_redirects=False)

    # Assert
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/static/index.html"
