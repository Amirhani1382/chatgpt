#!/usr/bin/env python3
"""Open trackin.post.ir in Google Chrome if available."""
import webbrowser
import shutil

URL = "https://trackin.post.ir"

def open_in_chrome(url: str) -> bool:
    """Try to open the given URL in Chrome and return True if succeeded."""
    potential = [
        "google-chrome",
        "chrome",
        "chromium",
        "google-chrome-stable",
    ]
    for name in potential:
        path = shutil.which(name)
        if path:
            webbrowser.get(f"{path} %s").open(url)
            return True
    return False


def main() -> None:
    if not open_in_chrome(URL):
        print("Chrome not found, opening in default browser.")
        webbrowser.open(URL)


if __name__ == "__main__":
    main()
