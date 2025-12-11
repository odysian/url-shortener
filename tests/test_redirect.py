import json


def test_redirect(authenticated_client):
    """Test that a short code successfully redirects"""

    link_response = authenticated_client.post(
        "/links", json={"original_url": "https://example.com/"}
    )
    assert link_response.status_code == 201
    link_data = link_response.json()
    short_code = link_data["short_code"]
    link_id = link_data["id"]

    redirect_response = authenticated_client.get(
        f"/{short_code}", follow_redirects=False
    )
    assert redirect_response.status_code == 302

    clicks_response = authenticated_client.get(f"/clicks/{link_id}")
    assert clicks_response.status_code == 200
    clicks = clicks_response.json()

    assert len(clicks) == 1
    assert clicks[0]["link_id"] == link_id
    assert clicks[0]["referrer"] is None
    assert "user_agent" in clicks[0]
    assert "clicked_at" in clicks[0]


def test_redirect_uses_cache(authenticated_client, test_redis):
    """Test that second redirect uses cache (no DB query)"""

    link_response = authenticated_client.post(
        "/links", json={"original_url": "https://example.com/"}
    )
    short_code = link_response.json()["short_code"]

    redirect1 = authenticated_client.get(f"/{short_code}", follow_redirects=False)
    assert redirect1.status_code == 302

    cache_key = f"link:{short_code}"
    cached_data = test_redis.get(cache_key)
    assert cached_data is not None

    cache_dict = json.loads(cached_data)
    assert cache_dict["url"] == "https://example.com/"

    redirect2 = authenticated_client.get(f"/{short_code}", follow_redirects=False)
    assert redirect2.status_code == 302
    assert redirect1.headers["location"] == redirect2.headers["location"]

    cached = test_redis.get(f"link:{short_code}")
    assert cached is not None
