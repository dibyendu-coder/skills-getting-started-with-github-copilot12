from urllib.parse import quote


def test_root_redirects_to_static_frontend(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"]["max_participants"] == 12
    assert isinstance(activities["Chess Club"]["participants"], list)


def test_signup_adds_participant(client):
    activity = "Soccer Club"
    email = "new.student@mergington.edu"

    response = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in client.get("/activities").json()[activity]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    activity = "Soccer Club"
    email = "duplicate.student@mergington.edu"
    signup_url = f"/activities/{quote(activity)}/signup"

    first_response = client.post(signup_url, params={"email": email})
    duplicate_response = client.post(signup_url, params={"email": email})

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()[activity]["participants"].count(email) == 1


def test_unregister_removes_participant(client):
    activity = "Soccer Club"
    email = "remove.student@mergington.edu"
    signup_url = f"/activities/{quote(activity)}/signup"
    unregister_url = (
        f"/activities/{quote(activity)}/participants/{quote(email, safe='')}"
    )

    client.post(signup_url, params={"email": email})
    response = client.delete(unregister_url)

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in client.get("/activities").json()[activity]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Club/participants/student%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unknown_participant(client):
    activity = "Soccer Club"
    email = "not.registered@mergington.edu"
    unregister_url = (
        f"/activities/{quote(activity)}/participants/{quote(email, safe='')}"
    )

    response = client.delete(unregister_url)

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
