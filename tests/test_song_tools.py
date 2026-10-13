"""Stubbed pipeline check for suno_create_song (no browser, no download quota)."""
import asyncio, json, shutil, subprocess, tempfile
from pathlib import Path

from suno_mcp.tools import song_tools
from suno_mcp.tools.song_tools import SongTools

OLD, NEW1, NEW2, PREV = "1" * 8, "2" * 8, "3" * 8, "4" * 8


def listing(*clips):
    return "Library:\n```json\n" + json.dumps([{"id": i, "title": t, "type": k} for i, t, k in clips]) + "\n```"


class Lib:
    calls = 0
    async def library_list(self, limit):
        Lib.calls += 1
        if Lib.calls == 1:
            return listing((OLD, "Old", "gen"))
        return listing((PREV, "My Song!", "preview"), (NEW1, "My Song!", "gen"), (NEW2, "My Song!", "gen"), (OLD, "Old", "gen"))


class Gen:
    calls = 0
    async def generate_track(self, *a):
        Gen.calls += 1
        return "ok"


class Dl:
    fails = 1
    async def download_track(self, clip, path):
        if Dl.fails:
            Dl.fails -= 1
            raise song_tools.SunoError("not ready", "X")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=d=12",
                        "-q:a", "2", f"{path}/{clip}.mp3"], check=True)


def main():
    song_tools.POLL_SECONDS = 0
    with tempfile.TemporaryDirectory() as d:
        out = asyncio.run(SongTools(Gen(), Lib(), Dl()).create_song(
            "p", "s", "My Song!", download_path=d, max_seconds=5, both_versions=True))
        files = sorted(p.name for p in Path(d).iterdir())
        assert files == ["my-song-2.mp3", "my-song.mp3"], files
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    f"{d}/my-song.mp3"], capture_output=True, text=True).stdout)
        assert 4.5 <= dur <= 5.5, dur
        assert NEW1 in out and NEW2 in out and PREV not in out  # previews are never downloaded
        # Second request with the same title: reuses the existing clip, no new generation (no credits).
        asyncio.run(SongTools(Gen(), Lib(), Dl()).create_song("p", "s", "My Song!", download_path=d))
        assert Gen.calls == 1, Gen.calls
    print("PASS", files, dur)


if __name__ == "__main__":
    assert shutil.which("ffmpeg")
    main()
