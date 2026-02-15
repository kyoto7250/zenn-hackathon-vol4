from app.services.gen_scenario import generate_mock_scenario
import json
from unittest.mock import patch, MagicMock


def test_yaml_storage():
    step1_response_text = json.dumps(
        {
            "description": "mock description",
            "yaml": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: test-pod",
        }
    )
    step2_response_text = json.dumps(
        {
            "mermaid": "flowchart TD\n  subgraph cluster[Cluster]\n    pod_test[Pod: test-pod]\n  end",
            "events": [],
        }
    )

    with patch("requests.post") as mock_post:
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": step1_response_text}]}}]
        }
        mock_response1.status_code = 200

        mock_response2 = MagicMock()
        mock_response2.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": step2_response_text}]}}]
        }
        mock_response2.status_code = 200
        mock_post.side_effect = [mock_response1, mock_response2]

        with patch("app.services.gen_scenario.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "dummy"

            with patch("app.services.gen_scenario.get_k8s_client") as mock_get_client:
                mock_client = MagicMock()
                mock_get_client.return_value = mock_client

                with patch("app.services.gen_scenario.utils.create_from_dict"):
                    scenario = generate_mock_scenario("test")

                    print(f"YAML Content length: {len(scenario.yaml_content)}")
                    print(f"YAML Content: {scenario.yaml_content}")

                    assert "apiVersion: v1" in scenario.yaml_content
                    assert "kind: Pod" in scenario.yaml_content
                    assert "flowchart TD" in scenario.topology_json["mermaid"]
                    print("Test PASSED: YAML content stored in scenario object.")


if __name__ == "__main__":
    test_yaml_storage()
