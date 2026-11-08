import re

import pytest

import quantize

NAME = re.compile(r"^(rgb[0-5]{3}|gray([0-9]|1[0-9]|2[0-3]))$")


@pytest.mark.parametrize(
    ("hex_color", "name"),
    [
        ("000000", "gray0"),  # not rgb000 (color16, redefined by tinted-shell)
        ("ffffff", "rgb555"),
        ("268bd2", "rgb024"),
        ("dc322f", "rgb400"),
        ("808080", "gray12"),
        ("#5f87af", "rgb123"),  # exact cube entry
    ],
)
def test_nearest_known(hex_color, name):
    assert quantize.nearest(hex_color)[0] == name


def test_reserved_indices_never_chosen():
    for r in range(0, 256, 15):
        for g in range(0, 256, 15):
            for b in range(0, 256, 15):
                name, index = quantize.nearest(f"{r:02x}{g:02x}{b:02x}")
                assert index not in quantize.RESERVED
                assert NAME.match(name), name


def test_ciede2000_reference_pair():
    # Sharma, Wu & Dalal (2005) test data, pair 1: dE00 = 2.0425.
    d = quantize.ciede2000((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485))
    assert d == pytest.approx(2.0425, abs=1e-4)


def test_quantize_line_keeps_source_hex():
    line = "color.warning=hex:002B36 on hex:b58900"
    assert quantize.quantize_line(line) == (
        "color.warning=gray3 on rgb320  # #002b36 on #b58900"
    )
    assert quantize.quantize_line("color.until=") == "color.until="


def test_quantize_file_rejects_malformed_token(tmp_path):
    theme = tmp_path / "bad.theme"
    theme.write_text("color.header=hex:12345\n")
    assert quantize.main([str(theme)]) == 1


def test_quantize_file_is_idempotent(tmp_path):
    theme = tmp_path / "t.theme"
    theme.write_text("# c\ncolor.header=hex:268bd2\ncolor.until=\n")
    quantize.quantize_file(theme)
    first = theme.read_text()
    quantize.quantize_file(theme)
    assert (
        theme.read_text()
        == first
        == ("# c\ncolor.header=rgb024  # #268bd2\ncolor.until=\n")
    )
