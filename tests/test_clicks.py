def test_multiple_clicks_recorded(authenticated_client):
    """Test that multiple visits create multiple click records"""

    link_response = authenticated_client.post(
        "/links", json={"original_url": "https://example.com/"}
    )
    assert link_response.status_code == 201
    link_data = link_response.json()
    short_code = link_data["short_code"]
    link_id = link_data["id"]

    for _ in range(3):
        authenticated_client.get(f"/{short_code}", follow_redirects=False)

    clicks_response = authenticated_client.get(f"/clicks/{link_id}")
    assert clicks_response.status_code == 200
    clicks = clicks_response.json()
    assert len(clicks) == 3


def test_click_stats(authenticated_client):
    """Test aggregated click stats"""

    link_response = authenticated_client.post(
        "/links", json={"original_url": "https://example.com/"}
    )

    link_data = link_response.json()
    short_code = link_data["short_code"]

    for _ in range(5):
        authenticated_client.get(f"/{short_code}", follow_redirects=False)

    stats_response = authenticated_client.get(f"/clicks/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()

    assert stats["total_clicks"] == 5
    assert stats["clicks_today"] == 5
    assert stats["clicks_this_week"] == 5
    assert stats["clicks_this_month"] == 5
    assert isinstance(stats["top_referrers"], list)
