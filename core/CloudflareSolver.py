from __future__ import annotations

import logging
import re
import urllib.parse as urlparse
from enum import Enum
from typing import Any, Dict, Final, Iterable, List, Optional
from datetime import datetime
from patchright.sync_api import Cookie
from patchright.sync_api import Frame, sync_playwright


class ChallengePlatform(Enum):
    """Cloudflare challenge platform types."""

    JAVASCRIPT = "non-interactive"
    MANAGED = "managed"
    INTERACTIVE = "interactive"


class CloudflareSolver:
    """
    A class for solving Cloudflare challenges with Playwright.

    Parameters
    ----------
    user_agent : Optional[str]
        The user agent string to use for the browser requests.
    timeout : float
        The timeout in seconds to use for browser actions and solving challenges.
    http2 : bool
        Enable or disable the usage of HTTP/2 for the browser requests.
    http3 : bool
        Enable or disable the usage of HTTP/3 for the browser requests.
    headless : bool
        Enable or disable headless mode for the browser.
    proxy : Optional[str]
        The proxy server URL to use for the browser requests.
    """

    def __init__(
            self,
            *,
            user_agent: Optional[str],
            timeout: float,
            http2: bool,
            http3: bool,
            headless: bool,
            proxy: Optional[str],
    ) -> None:
        self._playwright = sync_playwright().start()
        args: List[str] = []

        if not http2:
            args.append("--disable-http2")

        if not http3:
            args.append("--disable-quic")

        if proxy is not None:
            proxy = self._parse_proxy(proxy)
            logging.info(f"Using proxy: {proxy}")

        browser = self._playwright.chromium.launch(
            args=args, headless=headless, proxy=proxy
        )

        context = browser.new_context(user_agent=user_agent)
        context.set_default_timeout(timeout * 1000)

        self.page = context.new_page()
        self._timeout = timeout

    def __enter__(self) -> CloudflareSolver:
        return self

    def __exit__(self, *_: Any) -> None:
        self._playwright.stop()

    @staticmethod
    def _parse_proxy(proxy: str) -> Dict[str, str]:
        """
        Parse a proxy URL string into a dictionary of proxy parameters for
        the Playwright browser.

        Parameters
        ----------
        proxy : str
            Proxy URL string.

        Returns
        -------
        Dict[str, str]
            The dictionary of proxy parameters.
        """
        parsed_proxy = urlparse.urlparse(proxy)
        server = f"{parsed_proxy.scheme}://{parsed_proxy.hostname}"

        if parsed_proxy.port is not None:
            server += f":{parsed_proxy.port}"

        proxy_params = {"server": server}

        if parsed_proxy.username is not None and parsed_proxy.password is not None:
            proxy_params.update(
                {"username": parsed_proxy.username, "password": parsed_proxy.password}
            )

        return proxy_params

    def _get_turnstile_frame(self) -> Optional[Frame]:
        """
        Get the Cloudflare turnstile frame.

        Returns
        -------
        Optional[Frame]
            The Cloudflare turnstile frame.
        """
        return self.page.frame(
            url=re.compile(
                "https://challenges.cloudflare.com/cdn-cgi/challenge-platform/h/[bg]/turnstile"
            ),
        )

    @property
    def cookies(self) -> List[Cookie]:
        """The cookies from the current page."""
        return self.page.context.cookies()

    @staticmethod
    def extract_clearance_cookie(cookies: Iterable[Cookie]) -> Optional[Cookie]:
        """
        Extract the Cloudflare clearance cookie from a list of cookies.

        Parameters
        ----------
        cookies : Iterable[Cookie]
            List of cookies.

        Returns
        -------
        Optional[Cookie]
            The Cloudflare clearance cookie. Returns None if the cookie is not found.
        """
        for cookie in cookies:
            if cookie["name"] == "cf_clearance":
                return cookie

        return None

    def get_user_agent(self) -> str:
        """
        Get the current user agent string.

        Returns
        -------
        str
            The user agent string.
        """
        return self.page.evaluate("navigator.userAgent")

    def detect_challenge(self) -> Optional[ChallengePlatform]:
        """
        Detect the Cloudflare challenge platform on the current page.

        Returns
        -------
        Optional[ChallengePlatform]
            The Cloudflare challenge platform.
        """
        html = self.page.content()

        for platform in ChallengePlatform:
            if f"cType: '{platform.value}'" in html:
                return platform

        return None

    def solve_challenge(self) -> None:
        """Solve the Cloudflare challenge on the current page."""
        verify_button_pattern = re.compile(
            "Verify (I am|you are) (not a bot|(a )?human)"
        )

        verify_button = self.page.get_by_role("button", name=verify_button_pattern)
        challenge_spinner = self.page.locator("#challenge-spinner")
        challenge_stage = self.page.locator("#challenge-stage")
        start_timestamp = datetime.now()

        while (
                self.extract_clearance_cookie(self.cookies) is None
                and self.detect_challenge() is not None
                and (datetime.now() - start_timestamp).seconds < self._timeout
        ):
            if challenge_spinner.is_visible():
                challenge_spinner.wait_for(state="hidden")

            turnstile_frame = self._get_turnstile_frame()

            if verify_button.is_visible():
                verify_button.click()
                challenge_stage.wait_for(state="hidden")
            elif turnstile_frame is not None:
                self.page.mouse.click(210, 290)
                challenge_stage.wait_for(state="hidden")

            self.page.wait_for_timeout(250)
