# macOS 常见垃圾文件位置速查

## 安全清理（清理不影响应用运行）

### 用户缓存
| 路径 | 说明 |
|------|------|
| `~/Library/Caches/` | 所有应用缓存，可整个清空 |
| `~/Library/Caches/Google/` | Chrome 缓存 |
| `~/Library/Caches/Microsoft Edge/` | Edge 缓存 |
| `~/Library/Caches/pip/` | Python pip 下载缓存 |
| `~/Library/Caches/Homebrew/` | Homebrew 下载缓存 |
| `~/Library/Caches/CloudKit/` | iCloud 同步缓存 |
| `~/Library/Caches/com.tencent.inputmethod.wetype/` | 微信输入法缓存 |

### 系统缓存
| 路径 | 说明 |
|------|------|
| `/System/Volumes/Data/private/var/log/` | 系统日志 |
| `/System/Volumes/Data/Library/Caches/` | 系统级缓存 |
| `~/Library/Logs/` | 用户应用日志 |

### 浏览器数据
| 路径 | 说明 |
|------|------|
| `~/Library/Caches/Google/` | Chrome 缓存 |
| `~/Library/Application Support/Google/Chrome/Default/Service Worker/` | Chrome Service Worker |
| `~/Library/Caches/Microsoft Edge/` | Edge 缓存 |

## 应用残留（应用已卸载但数据还在）

### 已知常见残留
| Bundle ID 前缀 | 应用 | 典型大小 |
|------|------|------|
| `com.netease.mumu` | 网易 MuMu 模拟器 | 10-30 GB |
| `com.docker.docker` | Docker Desktop | 1-20 GB |
| `com.valvesoftware.steam` | Steam | 1-10 GB |
| `com.riotgames.leagueoflegends` | 英雄联盟 | 1-5 GB |
| `com.blizzard.*` | 暴雪游戏 | 1-10 GB |
| `com.epicgames.*` | Epic 游戏 | 1-10 GB |

### 残留数据位置（需要在以下目录搜索）
1. `~/Library/Application Support/<bundle-id>/`
2. `~/Library/Caches/<bundle-id>/`
3. `~/Library/Containers/<bundle-id>/`
4. `~/Library/Group Containers/<team-id>.<bundle-id>/`
5. `~/Library/HTTPStorages/<bundle-id>/`
6. `~/Library/WebKit/<bundle-id>/`
7. `~/Library/Saved Application State/<bundle-id>.savedState/`
8. `~/Library/Preferences/<bundle-id>.plist`

## 开发工具残留

### Xcode
| 路径 | 说明 | 可安全清理 |
|------|------|:---:|
| `~/Library/Developer/Xcode/DerivedData/` | 构建缓存 | ✅ |
| `~/Library/Developer/Xcode/iOS DeviceSupport/` | iOS 设备支持文件 | ✅ (旧版) |
| `~/Library/Developer/CoreSimulator/` | iOS 模拟器镜像 | ✅ (不用的) |
| `~/Library/Developer/Xcode/Archives/` | 归档文件 | 按需 |

### 其他开发工具
| 路径 | 说明 |
|------|------|
| `~/.gradle/` | Gradle 缓存 |
| `~/.m2/repository/` | Maven 本地仓库 |
| `~/.npm/_cacache/` | npm 缓存 |
| `~/Library/Caches/ms-playwright/` | Playwright 浏览器缓存 |
| `~/.cargo/registry/` | Cargo 注册表缓存 |

## Time Machine
| 命令 | 说明 |
|------|------|
| `tmutil listlocalsnapshots /` | 查看本地快照 |
| `sudo tmutil deletelocalsnapshots /` | 删除所有本地快照 |

## 注意事项

1. **永远不清理** `~/Library/Application Support/` 中正在使用的应用数据（需先确认应用是否已卸载）
2. **永远不清理** `~/Library/Keychains/`、`~/Library/Accounts/`
3. 清理前检查应用是否在 `/Applications/` 中
4. 使用 `osascript` 移到废纸篓而非 `rm -rf`
5. 单次最多清理 10 个目录/文件
