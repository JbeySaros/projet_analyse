import pytest

@pytest.mark.asyncio
async def test_file_upload(client, tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("col1,col2\n1,2")

    with file_path.open("rb") as f:
        response = await client.post(
            "/api/upload",
            files={"file": ("sample.csv", f, "text/csv")},
        )

    assert response.status_code == 200
    assert "filename" in response.json()
