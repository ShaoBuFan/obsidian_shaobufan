---
tags: [claude-code, 运维, 手册]
created: 2026-05-29
---

# Claude Code v2.1.153 手动安装手册

## 基本信息

| 字段 | 值 |
|------|-----|
| 版本 | 2.1.153 |
| 发布日期 | 2026-05-28 |
| Commit | `6cfd211761f355dcebba152b66399d0416e445d2` |
| 构建时间 | 2026-05-27T20:11:39Z |

## 下载地址

两个 CDN，任选其一。

**主 CDN：**

```
https://downloads.claude.ai/claude-code-releases/{VERSION}/{PLATFORM}/{FILE}
```

**备选（Google Cloud Storage）：**

```
https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/{VERSION}/{PLATFORM}/{FILE}
```

## 各平台文件及校验

| 平台 | 文件名 | 大小 | SHA256 |
|------|--------|------|--------|
| Linux x64 (glibc) | `claude` | 239 MB | `214f603f31942162dac9a65f18d43b3ac646ae215240fad481c4aad6c60f2e38` |
| Linux x64 (musl) | `claude` | 234 MB | `fb2b406b244466db17b48e2864ec7c90b852ef3f404bbb1d9c9bf914efee39d1` |
| Linux ARM64 (glibc) | `claude` | 240 MB | `6277fbbea72228a069e4719fc3e5fa36f16749247a2321c520dae93e83e92d9c` |
| Linux ARM64 (musl) | `claude` | 233 MB | `5071eceaedd2d4d6b085faa46e1a60befad432176a9ec39fd10c004564381308` |
| macOS ARM64 | `claude` | 214 MB | `449d9c89d7a63b1d427d912a7bd6e6f23f9a7b363866697c9fa9a0012546b254` |
| macOS x64 | `claude` | 217 MB | `4b90521c64b728caabe221737ce8a83d362ef0852eee7d789f014f7ff73ce97b` |
| Windows x64 | `claude.exe` | 236 MB | `8bda00dba0e8b44e67966a07ee32cf23032f7ebb90e77d4f82ab2e39b1118623` |
| Windows ARM64 | `claude.exe` | 232 MB | `240240e32f10bc7d4124c1c5603313e243cabaae80e174e2c6eb27f5b1e1ebe9` |

## 操作步骤：Linux / macOS

```bash
# === 设定参数 ===
VERSION="2.1.153"
PLATFORM="linux-x64"          # 按需替换，见上表
BASE_URL="https://downloads.claude.ai/claude-code-releases"

# === 1. 下载二进制 ===
curl -fsSL "${BASE_URL}/${VERSION}/${PLATFORM}/claude" \
  -o ~/.local/bin/claude

# 如果主 CDN 不通，换 GCS：
# BASE_URL="https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases"

# === 2. 校验 SHA256 ===
MANIFEST_URL="${BASE_URL}/${VERSION}/manifest.json"
EXPECTED=$(curl -fsSL "$MANIFEST_URL" | python3 -c "
import sys, json
m = json.load(sys.stdin)
print(m['platforms']['${PLATFORM}']['checksum'])
")
ACTUAL=$(sha256sum ~/.local/bin/claude | cut -d' ' -f1)

if [ "$EXPECTED" = "$ACTUAL" ]; then
    echo "✔ SHA256 校验通过"
else
    echo "✘ 校验失败！期望: $EXPECTED"
    echo "           实际: $ACTUAL"
    exit 1
fi

# === 3. 赋予执行权限 ===
chmod +x ~/.local/bin/claude

# === 4. 验证 ===
claude --version
# 应输出: 2.1.153 (Claude Code)
```

## 操作步骤：Windows PowerShell

```powershell
# === 设定参数 ===
$VERSION = "2.1.153"
$PLATFORM = "win32-x64"       # 或 win32-arm64
$BASE_URL = "https://downloads.claude.ai/claude-code-releases"
$TARGET = "$env:USERPROFILE\.local\bin\claude.exe"
$TARGET_DIR = Split-Path $TARGET -Parent

# === 0. 创建目录 ===
New-Item -ItemType Directory -Force -Path $TARGET_DIR

# === 1. 下载二进制 ===
Write-Host "Downloading..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "${BASE_URL}/${VERSION}/${PLATFORM}/claude.exe" `
  -OutFile $TARGET

# === 2. 校验 SHA256 ===
$manifest = Invoke-RestMethod -Uri "${BASE_URL}/${VERSION}/manifest.json"
$expected = $manifest.platforms.$PLATFORM.checksum
$actual = (Get-FileHash -Algorithm SHA256 $TARGET).Hash.ToLower()

if ($expected -eq $actual) {
    Write-Host "✔ SHA256 校验通过" -ForegroundColor Green
} else {
    Write-Host "✘ 校验失败！期望: $expected" -ForegroundColor Red
    Write-Host "           实际: $actual" -ForegroundColor Red
    exit 1
}

# === 3. 验证 ===
& $TARGET --version
# 应输出: 2.1.153 (Claude Code)

# === 4. (可选) 加入 PATH ===
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "User") + ";$TARGET_DIR",
    "User"
)
```

## 操作步骤：Alpine Linux (musl)

步骤同 Linux，只需把 `PLATFORM` 改为 `linux-x64-musl` 或 `linux-arm64-musl`。

## 操作步骤：macOS

步骤同 Linux，只需把 `PLATFORM` 改为 `darwin-arm64`（Apple Silicon）或 `darwin-x64`（Intel）。

## GPG 签名验证（可选）

```bash
# 导入 Anthropic 签名公钥
curl -fsSL "https://downloads.claude.ai/keys/claude-code.asc" | gpg --import

# 下载对应的 .sig 文件并验证
curl -fsSL "${BASE_URL}/${VERSION}/${PLATFORM}/claude.sig" -o claude.sig
gpg --verify claude.sig ~/.local/bin/claude
```

## 回滚

如需回退到之前的版本，把 `VERSION` 换成目标版本号重新执行即可：

```bash
VERSION="2.1.141"
curl -fsSL "${BASE_URL}/${VERSION}/linux-x64/claude" -o ~/.local/bin/claude
chmod +x ~/.local/bin/claude
```
