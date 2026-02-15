from app.services.gen_scenario import generate_mock_scenario
import json
from unittest.mock import patch, MagicMock


def test_two_step_generation():
    # Mock response for Step 1 (YAML)
    step1_response_text = json.dumps(
        {
            "description": "Step 1 description.",
            "yaml": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: test-pod",
        }
    )

    # Mock response for Step 2 (Mermaid Topology)
    step2_response_text = json.dumps(
        {
            "mermaid": "flowchart TD\n  subgraph cluster[Cluster]\n    pod_test[Pod: test-pod]\n  end",
            "events": [],
        }
    )

    with patch("requests.post") as mock_post:
        # Configure mock to return different responses for the two calls
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
                    print("Testing two-step generation...")
                    scenario = generate_mock_scenario("create pod")

                    # Verify Step 1 Output
                    print(f"Description: {scenario.description}")
                    assert "Step 1 description" in scenario.description
                    assert "apiVersion: v1" in scenario.yaml_content

                    # Verify Step 2 Output
                    print(f"Mermaid: {scenario.topology_json['mermaid'][:60]}...")
                    assert "flowchart TD" in scenario.topology_json["mermaid"]
                    assert "Cluster" in scenario.topology_json["mermaid"]

                    print(f"Verification calls: {mock_post.call_count}")
                    assert mock_post.call_count == 2

                    # Verify the second call prompt contained the YAML from the first call
                    call_args = mock_post.call_args_list
                    second_call_json = call_args[1][1]["json"]
                    sent_prompt = second_call_json["contents"][0]["parts"][0]["text"]
                    assert "apiVersion: v1" in sent_prompt

                    print("Test PASSED: Two-step generation flow verified.")


if __name__ == "__main__":
    test_two_step_generation()
