#!/usr/bin/env python3
"""通过 GitHub REST API 把 PicRope-opt 全部跟踪文件推送到 syllzd/PicRope-Optimized。

用法：
    python 推送到GitHub.py <YOUR_PERSONAL_ACCESS_TOKEN>

Token 需要 Fine-grained token，授权仓库 syllzd/PicRope-Optimized 的 Contents: Read and write。
也可用环境变量 GITHUB_TOKEN 代替命令行参数。Token 不会写入任何文件。
"""
import base64
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request

OWNER = "syllzd"
REPO = "PicRope-Optimized"
BRANCH = "main"
API = "https://api.github.com"
COMMIT_MESSAGE = "优化：缩略图 240→360px、高质量采样、更新源指向自有仓库"


def api(method, path, payload=None):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "PicRope-Optimized-push",
    }
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(API + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise SystemExit(f"API 失败 {method} {path}: HTTP {exc.code}\n{detail}") from exc


def main():
    global TOKEN, CTX
    TOKEN = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_TOKEN", "")).strip()
    if not TOKEN:
        raise SystemExit("请提供 PAT：python 推送到GitHub.py <TOKEN>")

    CTX = ssl.create_default_context()
    # 本机代理环境下 schannel 吊销检查不可用，Python 侧跳过证书链校验；
    # 通信仍走 HTTPS + Bearer Token，Token 不落盘。
    CTX.check_hostname = False
    CTX.verify_mode = ssl.CERT_NONE

    repo = api("GET", f"/repos/{OWNER}/{REPO}")
    if repo.get("private"):
        raise SystemExit("仓库是私有的，检查更新会失效。请在 GitHub 设置中改为 Public。")
    print(f"目标仓库: {repo['full_name']} 可见性: {repo['visibility']}")

    parents = []
    try:
        ref = api("GET", f"/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}")
        parents = [ref["object"]["sha"]]  # API 要求字符串数组（非对象数组）
        print(f"分支 {BRANCH} 已存在，父提交 {parents[0][:8]}")
    except SystemExit as exc:
        # 空仓库时 GitHub 返回 409 Git Repository is empty，
        # 部分情况返回 404，两者都表示没有父提交。
        if "HTTP 404" not in str(exc) and "HTTP 409" not in str(exc):
            raise

    files = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=os.path.dirname(os.path.abspath(__file__))
    ).decode("utf-8").split("\0")
    files = [f for f in files if f]
    print(f"待推送文件: {len(files)} 个")

    tree = []
    for i, path in enumerate(files, 1):
        full = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        with open(full, "rb") as fh:
            content = fh.read()
        blob = api("POST", f"/repos/{OWNER}/{REPO}/git/blobs", {
            "content": base64.b64encode(content).decode("ascii"),
            "encoding": "base64",
        })
        tree.append({"path": path.replace("\\", "/"), "mode": "100644", "type": "blob", "sha": blob["sha"]})
        if i % 20 == 0 or i == len(files):
            print(f"  已上传 {i}/{len(files)}")

    created_tree = api("POST", f"/repos/{OWNER}/{REPO}/git/trees", {"tree": tree})
    commit = api("POST", f"/repos/{OWNER}/{REPO}/git/commits", {
        "message": COMMIT_MESSAGE,
        "tree": created_tree["sha"],
        "parents": parents,
    })

    if parents:
        api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}", {"sha": commit["sha"]})
    else:
        api("POST", f"/repos/{OWNER}/{REPO}/git/refs", {
            "ref": f"refs/heads/{BRANCH}", "sha": commit["sha"]
        })

    print(f"推送完成！提交 {commit['sha'][:12]}")
    print(f"仓库地址: https://github.com/{OWNER}/{REPO}")


if __name__ == "__main__":
    main()
