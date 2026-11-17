"""Review finding 1: CI scanner images are pinned (version tag + digest)."""
import re
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
IMAGE_RE = re.compile(r"docker\.io/[a-z0-9._/-]+(?::[A-Za-z0-9._-]+)?(?:@sha256:[0-9a-f]{64})?")


def test_container_images_pinned_by_version_and_digest():
    images = [m.group(0) for f in WORKFLOWS.glob("*.yml") for m in IMAGE_RE.finditer(f.read_text())]
    assert images, "expected scanner images in workflows"
    for image in images:
        assert ":latest" not in image, image
        assert re.search(r":v?\d+\.\d+\.\d+@sha256:[0-9a-f]{64}$", image), image
