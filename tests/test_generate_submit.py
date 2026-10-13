"""Stubbed check: after one Create click we wait for the clip (through a Cloudflare check), never re-click."""
import asyncio

from suno_mcp.tools import generate_tools
from suno_mcp.tools.generate_tools import GenerateTools


class Frame:
    url = "https://challenges.cloudflare.com/cdn-cgi/challenge-platform/turnstile"


class Page:
    def __init__(self, polls_until_clip):
        self.polls, self.until = 0, polls_until_clip
    @property
    def frames(self):
        return [Frame()] if self.polls < self.until else []  # person is still ticking the check


def run(polls_until_clip):
    page = Page(polls_until_clip)
    async def fake_ids(p):
        p.polls += 1
        return ["new", "old"] if p.polls > p.until else ["old"]
    generate_tools.clip_ids = fake_ids
    return asyncio.run(GenerateTools(None)._submitted(page, {"old"})), page.polls


async def no_sleep(_): pass


def main():
    generate_tools.asyncio.sleep = no_sleep
    generate_tools.SUBMIT_WAIT_S = 5
    ok, polls = run(3)
    assert ok and polls == 4, "must keep waiting through the Cloudflare check until the clip shows up"
    generate_tools.SUBMIT_WAIT_S = 0.05
    ok, _ = run(10**9)
    assert not ok, "gives up (no re-click) when nothing appears in time"
    print("PASS")


if __name__ == "__main__":
    main()
