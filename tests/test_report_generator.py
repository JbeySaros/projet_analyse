import pytest
from unittest.mock import MagicMock, patch
from visualization.report_generator import ReportGenerator

@pytest.mark.asyncio
async def test_generate_html(tmp_path):
    output = tmp_path / "report.html"

    with patch("visualization.report_generator.HTML") as mock_html:
        mock_html.return_value.write_pdf = MagicMock()

        rg = ReportGenerator()
        await rg.generate_report_html("<h1>Test</h1>", output)

    assert output.exists()
