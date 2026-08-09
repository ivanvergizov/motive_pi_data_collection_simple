SIGNAL_DEFINITIONS = {
    "Position X": ("position", 0),
    "Position Y": ("position", 1),
    "Position Z": ("position", 2),
    "Euler X": ("euler", 0),
    "Euler Y": ("euler", 1),
    "Euler Z": ("euler", 2),
    "Quaternion X": ("quaternion", 0),
    "Quaternion Y": ("quaternion", 1),
    "Quaternion Z": ("quaternion", 2),
    "Quaternion W": ("quaternion", 3),
}

PLOT_COLORS = [
    "#e31212", "#fa7704", "#f7f308", "#2bdc0b", "#15dbfa",
    "#fe21f3", "#be018c", "#942f2f", "#934907", "#9d9c2f",
    "#437c39", "#2c808d", "#81217c", "#80002f", "#890346",
]

DEFAULT_PREVIEW_AA = "MSAA 4x"
PREVIEW_AA_OPTIONS = ["Off", "MSAA 2x", "MSAA 4x", "MSAA 8x", "MSAA 16x", "SSAA"]

EXPORT_RESOLUTION_OPTIONS = [
    "1280 x 720",
    "1920 x 1080",
    "2560 x 1440",
    "3840 x 2160",
]
EXPORT_MSAA_OPTIONS = ["Off", "2x", "4x", "8x", "16x"]
SSAA_OPTIONS = ["1x", "2x", "3x", "4x"]
VIDEO_CODEC_OPTIONS = [
    "H.264 RGB lossless (MP4)",
    "FFV1 lossless (MKV)",
    "H.264 high quality (MP4)",
    "H.265 high quality (MP4)",
]

# Shared by interactive PyVista playback and off-screen video export.
PYVISTA_AXIS_FONT_SIZE = 26
PYVISTA_BODY_LABEL_FONT_SIZE = 10
PYVISTA_BODY_LABEL_OFFSET = 6
PYVISTA_AXIS_COLOR = (0.30, 0.30, 0.30)
PYVISTA_GRID_COLOR = (0.68, 0.68, 0.68)


def color_for_curve(curve_index: int) -> str:
    return PLOT_COLORS[curve_index % len(PLOT_COLORS)]


def parse_preview_aa(text: str) -> tuple[str, int]:
    if text == "Off":
        return "off", 0
    if text == "SSAA":
        return "ssaa", 2
    if text.startswith("MSAA "):
        return "msaa", int(text.removeprefix("MSAA ").removesuffix("x"))
    raise ValueError(f"Unknown anti-aliasing option: {text!r}")
