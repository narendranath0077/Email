from backend.graph import validate_node, build_prompt_node, _parse_email_json, _extract_json


class TestValidateNode:
    def test_empty_key_points_blocks_generation(self):
        state = {"mode": "generate", "purpose": "Interview", "key_points": "   "}
        result = validate_node(state)
        assert "error" in result
        assert "key point" in result["error"].lower()

    def test_missing_recipient_defaults_to_there(self):
        state = {"mode": "generate", "purpose": "Interview", "key_points": "Monday 11am"}
        result = validate_node(state)
        assert result["recipient_name"] == "there"
        assert "error" not in result

    def test_missing_purpose_defaults_to_general_update(self):
        state = {"mode": "generate", "purpose": "", "key_points": "some point"}
        result = validate_node(state)
        assert result["purpose"] == "General Update"

    def test_missing_tone_and_length_get_defaults(self):
        state = {"mode": "generate", "purpose": "X", "key_points": "Y"}
        result = validate_node(state)
        assert result["tone"] == "Professional"
        assert result["length"] == "Standard"

    def test_valid_input_passes_through_unchanged_where_provided(self):
        state = {
            "mode": "generate",
            "purpose": "Offer Follow-up",
            "recipient_name": "Priya",
            "key_points": "confirm by Friday",
            "tone": "Friendly",
            "length": "Detailed",
        }
        result = validate_node(state)
        assert result["recipient_name"] == "Priya"
        assert result["tone"] == "Friendly"
        assert result["length"] == "Detailed"

    def test_refine_without_instruction_errors(self):
        state = {"mode": "refine", "refinement_instruction": ""}
        result = validate_node(state)
        assert "error" in result

    def test_refine_with_instruction_passes(self):
        state = {"mode": "refine", "refinement_instruction": "make it shorter"}
        result = validate_node(state)
        assert "error" not in result


class TestBuildPromptNode:
    def test_generate_prompt_includes_all_fields(self):
        state = {
            "mode": "generate",
            "purpose": "Interview Scheduling",
            "recipient_name": "Rahul Sharma",
            "designation": "Senior Developer",
            "key_points": "Monday 11 AM Teams",
            "tone": "Professional",
            "length": "Concise",
        }
        result = build_prompt_node(state)
        prompt = result["_prompt"]
        assert "Interview Scheduling" in prompt
        assert "Rahul Sharma" in prompt
        assert "Senior Developer" in prompt
        assert "Monday 11 AM Teams" in prompt
        assert "Professional" in prompt
        assert "Concise" in prompt

    def test_generate_prompt_omits_designation_when_absent(self):
        state = {
            "mode": "generate",
            "purpose": "X",
            "recipient_name": "Priya",
            "designation": "",
            "key_points": "Y",
            "tone": "Professional",
            "length": "Standard",
        }
        result = build_prompt_node(state)
        assert "Recipient: Priya\n" in result["_prompt"]

    def test_refine_prompt_includes_previous_draft_and_instruction(self):
        state = {
            "mode": "refine",
            "previous_subject": "Old Subject",
            "previous_body": "Old body text",
            "refinement_instruction": "make it shorter",
            "tone": "Professional",
            "length": "Standard",
        }
        result = build_prompt_node(state)
        prompt = result["_prompt"]
        assert "Old Subject" in prompt
        assert "Old body text" in prompt
        assert "make it shorter" in prompt

    def test_error_state_skips_prompt_building(self):
        state = {"error": "something went wrong"}
        result = build_prompt_node(state)
        assert "_prompt" not in result


class TestJsonParsing:
    def test_extract_json_strips_markdown_fences(self):
        raw = '```json\n{"subject": "Hi", "body": "Test"}\n```'
        assert _extract_json(raw) == '{"subject": "Hi", "body": "Test"}'

    def test_extract_json_passthrough_when_no_fences(self):
        raw = '{"subject": "Hi", "body": "Test"}'
        assert _extract_json(raw) == raw

    def test_parse_email_json_valid(self):
        raw = '{"subject": "Meeting Confirmed", "body": "Hi Rahul,\\n\\nSee you Monday."}'
        subject, body = _parse_email_json(raw)
        assert subject == "Meeting Confirmed"
        assert "Monday" in body

    def test_parse_email_json_invalid_returns_none(self):
        subject, body = _parse_email_json("this is not json at all")
        assert subject is None
        assert body is None

    def test_parse_email_json_empty_fields_returns_none(self):
        raw = '{"subject": "", "body": ""}'
        subject, body = _parse_email_json(raw)
        assert subject is None
        assert body is None

    def test_parse_email_json_with_fences(self):
        raw = '```json\n{"subject": "Hi", "body": "Test body"}\n```'
        subject, body = _parse_email_json(raw)
        assert subject == "Hi"
        assert body == "Test body"
