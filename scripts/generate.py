#!/usr/bin/env python3
"""Generate AltStore source JSON for PiliPlus from upstream GitHub releases.

Reads the upstream releases API, maps every release that ships an unsigned
iOS .ipa to an AltStore version entry, and writes:
  - generated/apps.json  (primary source URL)
  - alt_store.json       (equivalent copy, classic source filename)

Standard library only; runs on plain python3 (GitHub Actions ubuntu-latest
has it preinstalled).
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants (verified against the actual released ipa and the upstream repo)
# ---------------------------------------------------------------------------

UPSTREAM_REPO = "bggRGjQaUbCoE/PiliPlus"

SOURCE_NAME = "PiliPlus"
SOURCE_IDENTIFIER = "io.github.piliplus.altstore.source"

BUNDLE_ID = "com.example.piliplus"
DEVELOPER_NAME = "bggRGjQaUbCoE"
MIN_OS_VERSION = "15.0"  # MinimumOSVersion inside the released ipa
TINT_COLOR = "#5CB67B"  # dominant color of the app logo (assets/images/logo/logo.png)
CATEGORY = "entertainment"

WEBSITE = f"https://github.com/{UPSTREAM_REPO}"
ICON_URL = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/main/assets/images/logo/logo.png"
SCREENSHOT_BASE = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/main/assets/screenshots/"

SOURCE_SUBTITLE = "Unofficial PiliPlus AltStore source"
SUBTITLE = "使用 Flutter 开发的 BiliBili 第三方客户端"
DESCRIPTION = (
    "PiliPlus 是使用 Flutter 开发的 BiliBili 第三方客户端，基于 pilipala 与 PiliPalaX，"
    "支持推荐/热门/分区、番剧、直播、动态、搜索、缓存离线等完整功能。"
    "本源收录上游发布的未签名 iOS 构建（ipa），可通过 AltStore / SideStore 使用 Apple ID 自签安装。"
)

SCREENSHOTS = [
    "home.png",
    "bangumi.png",
    "bangumi_detail.png",
    "dynamic.png",
    "search.png",
    "set.png",
]

# Privacy usage descriptions, copied from the app's ios/Runner/Info.plist
PRIVACY = {
    "NSPhotoLibraryUsageDescription": "请允许APP保存图片到相册",
    "NSCameraUsageDescription": "App需要您的同意，才能访问相册",
    "NSAppleMusicUsageDescription": "App需要您的同意，才能访问媒体资料库",
    "NSLocalNetworkUsageDescription": "需要访问本地网络以发现和连接 DLNA 投屏设备",
}

# Match the unsigned iOS build, e.g. "PiliPlus_ios_2.2.0+5598.ipa"
IPA_ASSET_RE = re.compile(r"^PiliPlus[_-]ios.*\.ipa$", re.IGNORECASE)
# Extract the build number from the ipa filename: "...+5598.ipa" -> "5598"
BUILD_RE = re.compile(r"\+(\d+)\.ipa$", re.IGNORECASE)


def fetch_releases() -> list:
    """Fetch up to 100 recent releases from the upstream GitHub API."""
    url = f"https://api.github.com/repos/{UPSTREAM_REPO}/releases?per_page=100"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "PiliPlus-AltStore-Source",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def release_to_version(release: dict) -> dict | None:
    """Map one GitHub release to an AltStore version entry, or None if unusable."""
    if release.get("draft") or release.get("prerelease"):
        return None
    asset = next(
        (a for a in release.get("assets", []) if IPA_ASSET_RE.match(a.get("name", ""))),
        None,
    )
    if asset is None:
        print(f"  skip {release.get('tag_name')}: no iOS ipa asset")
        return None

    version = release.get("tag_name", "")
    body = (release.get("body") or "").strip() or f"PiliPlus {version}"

    entry = {
        "version": version,
        "date": release.get("published_at", ""),
        "localizedDescription": body,
        "downloadURL": asset["browser_download_url"],
        "size": asset.get("size", 0),
        "minOSVersion": MIN_OS_VERSION,
    }
    build = BUILD_RE.search(asset["name"])
    if build:
        entry["buildVersion"] = build.group(1)
    return entry


def build_source(pairs: list) -> tuple:
    """Build the full AltStore source dict from (release, version) pairs.

    Returns (source, latest_version_entry, latest_release).
    """
    versions = [v for _, v in pairs]
    # GitHub returns newest-first by creation; re-sort by publish date to be safe
    versions.sort(key=lambda v: v["date"], reverse=True)
    latest = versions[0]
    latest_release = pairs[0][0]

    news = [
        {
            "appID": BUNDLE_ID,
            "caption": f"PiliPlus {latest['version']} 已发布",
            "date": latest["date"],
            "identifier": f"release-{latest['version']}",
            "notify": True,
            "tintColor": TINT_COLOR,
            "title": f"PiliPlus {latest['version']}",
            "url": f"{WEBSITE}/releases/tag/{latest['version']}",
        }
    ]

    app = {
        "beta": False,
        "name": SOURCE_NAME,
        "bundleIdentifier": BUNDLE_ID,
        "developerName": DEVELOPER_NAME,
        "subtitle": SUBTITLE,
        "localizedDescription": DESCRIPTION,
        "version": latest["version"],
        "versionDate": latest["date"],
        "versionDescription": latest["localizedDescription"],
        "downloadURL": latest["downloadURL"],
        "size": latest["size"],
        "iconURL": ICON_URL,
        "tintColor": TINT_COLOR,
        "category": CATEGORY,
        "screenshots": {
            "iphone": [SCREENSHOT_BASE + name for name in SCREENSHOTS],
            "ipad": [],
        },
        "appPermissions": {"entitlements": [], "privacy": PRIVACY},
        "versions": versions,
    }

    return {
        "name": SOURCE_NAME,
        "identifier": SOURCE_IDENTIFIER,
        "website": WEBSITE,
        "subtitle": SOURCE_SUBTITLE,
        "description": DESCRIPTION,
        "iconURL": ICON_URL,
        "tintColor": TINT_COLOR,
        "featuredApps": [BUNDLE_ID],
        "apps": [app],
        "news": news,
    }, latest, latest_release


def write_outputs(root: Path, source: dict) -> None:
    out_dir = root / "generated"
    out_dir.mkdir(exist_ok=True)
    payload = json.dumps(source, ensure_ascii=False, indent=2) + "\n"
    (out_dir / "apps.json").write_text(payload, encoding="utf-8")
    (root / "alt_store.json").write_text(payload, encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parent.parent

    releases = fetch_releases()
    print(f"fetched {len(releases)} releases from {UPSTREAM_REPO}")

    pairs = []
    for release in releases:
        version = release_to_version(release)
        if version is not None:
            pairs.append((release, version))

    if not pairs:
        # Refuse to clobber an existing good source with an empty one.
        existing = root / "generated" / "apps.json"
        if existing.is_file():
            old = json.loads(existing.read_text(encoding="utf-8"))
            if old.get("apps") and old["apps"][0].get("versions"):
                print("ERROR: no usable releases found, keeping existing source", file=sys.stderr)
                return 1
        print("ERROR: no usable releases found upstream", file=sys.stderr)
        return 1

    source, latest, latest_release = build_source(pairs)
    write_outputs(root, source)

    print(f"generated source with {len(source['apps'][0]['versions'])} versions")
    print(f"latest: {latest['version']} ({latest['date']})")
    print(f"download: {latest['downloadURL']}")

    # Expose the latest tag to GitHub Actions for the commit message.
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"latest_tag={latest_release.get('tag_name', latest['version'])}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
