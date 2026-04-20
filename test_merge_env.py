import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from merge_env import (
    detect_and_parse,
    format_env,
    format_json,
    parse_env,
    parse_json,
)


# ---------------------------------------------------------------------------
# parse_env
# ---------------------------------------------------------------------------


class TestParseEnv:
    def test_simple_key_value(self):
        assert parse_env("FOO=bar") == {"FOO": "bar"}

    def test_multiple_keys(self):
        assert parse_env("A=1\nB=2") == {"A": "1", "B": "2"}

    def test_strips_comments(self):
        assert parse_env("# comment\nFOO=bar") == {"FOO": "bar"}

    def test_skips_blank_lines(self):
        assert parse_env("\nFOO=bar\n\n") == {"FOO": "bar"}

    def test_skips_lines_without_equals(self):
        assert parse_env("NOEQUALS\nFOO=bar") == {"FOO": "bar"}

    def test_double_quoted_value(self):
        assert parse_env('FOO="hello world"') == {"FOO": "hello world"}

    def test_single_quoted_value(self):
        assert parse_env("FOO='hello world'") == {"FOO": "hello world"}

    def test_value_with_equals_sign(self):
        assert parse_env("FOO=a=b=c") == {"FOO": "a=b=c"}

    def test_empty_value(self):
        assert parse_env("FOO=") == {"FOO": ""}

    def test_empty_quoted_value(self):
        assert parse_env('FOO=""') == {"FOO": ""}

    def test_strips_whitespace_around_key(self):
        assert parse_env("  FOO  =bar") == {"FOO": "bar"}

    def test_later_key_overrides_earlier(self):
        assert parse_env("FOO=first\nFOO=second") == {"FOO": "second"}

    def test_empty_input(self):
        assert parse_env("") == {}

    def test_only_comments(self):
        assert parse_env("# just a comment\n# another") == {}


# ---------------------------------------------------------------------------
# parse_json
# ---------------------------------------------------------------------------


class TestParseJson:
    def test_simple_object(self):
        assert parse_json('{"FOO": "bar"}') == {"FOO": "bar"}

    def test_numeric_values_coerced_to_str(self):
        assert parse_json('{"PORT": 8080}') == {"PORT": "8080"}

    def test_numeric_keys_coerced_to_str(self):
        assert parse_json('{"1": "one"}') == {"1": "one"}

    def test_non_object_raises(self):
        with pytest.raises(ValueError, match="JSON root must be an object"):
            parse_json('["a", "b"]')

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_json("not json")

    def test_empty_object(self):
        assert parse_json("{}") == {}


# ---------------------------------------------------------------------------
# detect_and_parse
# ---------------------------------------------------------------------------


class TestDetectAndParse:
    def test_detects_json_by_leading_brace(self):
        assert detect_and_parse('{"K": "v"}') == {"K": "v"}

    def test_detects_env_by_default(self):
        assert detect_and_parse("FOO=bar") == {"FOO": "bar"}

    def test_json_hint_forces_json_parse(self):
        assert detect_and_parse('{"K": "v"}', hint="secrets.json") == {"K": "v"}

    def test_env_hint_ignored_when_content_is_json(self):
        # content starts with { so JSON wins regardless of hint
        assert detect_and_parse('{"K": "v"}', hint="file.env") == {"K": "v"}

    def test_whitespace_before_brace_still_detected_as_json(self):
        assert detect_and_parse('  \n{"K": "v"}') == {"K": "v"}


# ---------------------------------------------------------------------------
# format_env
# ---------------------------------------------------------------------------


class TestFormatEnv:
    def test_simple_key_value(self):
        assert format_env({"FOO": "bar"}) == "FOO=bar\n"

    def test_value_with_space_is_quoted(self):
        assert format_env({"FOO": "hello world"}) == 'FOO="hello world"\n'

    def test_empty_value_is_quoted(self):
        assert format_env({"FOO": ""}) == 'FOO=""\n'

    def test_value_with_hash_is_quoted(self):
        assert format_env({"FOO": "val#comment"}) == 'FOO="val#comment"\n'

    def test_value_with_double_quote_is_escaped(self):
        result = format_env({"FOO": 'say "hi"'})
        assert result == 'FOO="say \\"hi\\""\n'

    def test_value_with_backslash_is_escaped(self):
        result = format_env({"FOO": "a\\b"})
        assert result == 'FOO="a\\\\b"\n'

    def test_multiple_keys(self):
        lines = format_env({"A": "1", "B": "2"}).splitlines()
        assert "A=1" in lines
        assert "B=2" in lines

    def test_empty_dict_produces_empty_string(self):
        assert format_env({}) == ""

    def test_ends_with_newline(self):
        assert format_env({"K": "v"}).endswith("\n")


# ---------------------------------------------------------------------------
# format_json
# ---------------------------------------------------------------------------


class TestFormatJson:
    def test_produces_valid_json(self):
        out = format_json({"FOO": "bar"})
        assert json.loads(out) == {"FOO": "bar"}

    def test_ends_with_newline(self):
        assert format_json({"K": "v"}).endswith("\n")

    def test_pretty_printed(self):
        out = format_json({"K": "v"})
        assert "\n" in out  # multi-line means indented

    def test_empty_dict(self):
        assert json.loads(format_json({})) == {}


# ---------------------------------------------------------------------------
# main() integration tests via subprocess-style invocation
# ---------------------------------------------------------------------------


def run_main(argv, stdin_text=None):
    """Call main() with patched sys.argv and optional stdin, capture stdout/stderr."""
    import merge_env

    stdout_buf = StringIO()
    stderr_buf = StringIO()
    stdin_buf = StringIO(stdin_text or "")

    with (
        patch.object(sys, "argv", ["merge_env.py"] + argv),
        patch("sys.stdout", stdout_buf),
        patch("sys.stderr", stderr_buf),
        patch("sys.stdin", stdin_buf),
    ):
        try:
            merge_env.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code

    return exit_code, stdout_buf.getvalue(), stderr_buf.getvalue()


class TestMainIntegration:
    def test_single_env_file(self, tmp_path):
        f = tmp_path / "a.env"
        f.write_text("FOO=1\nBAR=2\n")
        code, out, _ = run_main([str(f)])
        assert code == 0
        assert "FOO=1" in out
        assert "BAR=2" in out

    def test_single_json_file(self, tmp_path):
        f = tmp_path / "a.json"
        f.write_text('{"FOO": "1"}')
        code, out, _ = run_main([str(f)])
        assert code == 0
        assert "FOO=1" in out

    def test_later_file_overrides_earlier(self, tmp_path):
        a = tmp_path / "a.env"
        a.write_text("KEY=old\n")
        b = tmp_path / "b.env"
        b.write_text("KEY=new\n")
        code, out, _ = run_main([str(a), str(b)])
        assert code == 0
        assert "KEY=new" in out
        assert "KEY=old" not in out

    def test_merge_env_and_json(self, tmp_path):
        a = tmp_path / "base.env"
        a.write_text("A=1\nB=old\n")
        b = tmp_path / "override.json"
        b.write_text('{"B": "new", "C": "3"}')
        code, out, _ = run_main([str(a), str(b)])
        assert code == 0
        assert "A=1" in out
        assert "B=new" in out
        assert "C=3" in out

    def test_stdin_as_dash(self, tmp_path):
        f = tmp_path / "base.env"
        f.write_text("A=1\n")
        code, out, _ = run_main([str(f), "-"], stdin_text="B=2\n")
        assert code == 0
        assert "A=1" in out
        assert "B=2" in out

    def test_stdin_default_when_no_files(self):
        code, out, _ = run_main([], stdin_text="FOO=bar\n")
        assert code == 0
        assert "FOO=bar" in out

    def test_output_json_format(self, tmp_path):
        f = tmp_path / "a.env"
        f.write_text("FOO=bar\n")
        code, out, _ = run_main(["-f", "json", str(f)])
        assert code == 0
        data = json.loads(out)
        assert data == {"FOO": "bar"}

    def test_output_to_file(self, tmp_path):
        src = tmp_path / "a.env"
        src.write_text("FOO=1\n")
        out_file = tmp_path / "out.env"
        code, stdout, _ = run_main(["-o", str(out_file), str(src)])
        assert code == 0
        assert stdout == ""  # nothing on stdout
        assert "FOO=1" in out_file.read_text()

    def test_missing_file_exits_with_error(self):
        code, _, err = run_main(["/nonexistent/file.env"])
        assert code == 1
        assert "file not found" in err

    def test_invalid_json_exits_with_error(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{not valid json")
        code, _, err = run_main([str(f)])
        assert code == 1
        assert "could not parse" in err

    def test_three_files_merged_in_order(self, tmp_path):
        a = tmp_path / "a.env"
        a.write_text("X=1\nY=a\n")
        b = tmp_path / "b.env"
        b.write_text("Y=b\nZ=b\n")
        c = tmp_path / "c.env"
        c.write_text("Z=c\n")
        code, out, _ = run_main([str(a), str(b), str(c)])
        assert code == 0
        assert "X=1" in out
        assert "Y=b" in out
        assert "Z=c" in out
