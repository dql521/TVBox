# Zaka 聚合订阅 · 自托管 + 多线路镜像版

整仓自带全部资源，不依赖任何第三方托管。传到你自己的 GitHub 仓库就能跑。

这一版专门解决了**国内访问 GitHub raw 抽风**的问题：脚本一键把配置生成**多条镜像线路**的版本，
哪条通就用哪条；外加一份**镜像多仓版**——一个地址装下所有线路，某条挂了在壳里切仓就行。

---

## 一、包里有什么

| 文件 | 说明 |
|---|---|
| `okys-full.json` | **全能版** · 940 个点播源 + 65 路直播（含成人源，排在最后） |
| `okys-best.json` | **精选版** · 584 源，只留直连采集 + 本地驱动，启动最快（无成人源） |
| `okys-green.json` | **绿源纯净版** · 856 源，一个成人源都没有 |
| `okys-multi.json` | **多仓版** · 内置上面 3 份 + 16 个外部仓 |
| `_spider.jar` | 主驱动（顶层 spider 字段指向它） |
| `assets/` `js/` `lib/` `json/` `config/` `py/` `cat/` `ext/` `XBPQ/` … | 各源依赖的驱动、规则、清单 |
| `wall/` + `wall.json` | 38 张壁纸，全部本地自带 |
| `set-repo.py` | **一键生成镜像线路版配置**（第三节，核心工具） |
| `check-lines.html` | **线路体检页**（双击打开就能实测哪条线路通，不装任何东西） |
| `.gitattributes` | 防止 push 时把 jar / 图片转坏（别删） |

**规模**：500+ 个文件，约 116 MB。原来的配置里所有资源引用都指向本仓库内部。

> 四个主配置（`okys-full/best/green/multi.json`）用的是**同仓相对路径**（`./assets/xxx.jar`），
> 大多数壳能自己拼。嫌不稳就按第三节生成**绝对地址的镜像版**，一劳永逸。

---

## 二、传到你的 GitHub

先在 GitHub 网页上点 **New repository** 建仓库（比如叫 `okys`），**Visibility 必须选 Public**（私有仓库壳拉不动）。

```bash
cd zaka-tvbox-repo
git init -b main
git add .
git commit -m "zaka subscription"
git remote add origin https://github.com/你的用户名/okys.git
git push -u origin main
```

首次 push 有 116 MB，慢是正常的。

- 用 **GitHub Desktop**：File → Add local repository → 选本文件夹 → Publish repository，记得**去掉** "Keep this code private" 的勾。
- 用**网页拖拽**：Upload files 一次最多 100 个文件，500+ 个文件得拖 6 批，目录结构别改。

---

## 三、国内怎么访问（重点）

`raw.githubusercontent.com` 在国内经常打不开或被限速，所以不要只填它。有三种办法，从省事到彻底：

### 办法 1 · 一键生成镜像线路版（推荐，30 秒）

在仓库目录里跑：

```bash
python3 set-repo.py --check            # ① 先在你本机实测：哪几条线路通、多快
python3 set-repo.py --mirror           # ② 按主力线路生成全部配置
```

`--check` 会像这样输出（在**你自己的网络**实测，就是你所在地的真实结果）：

```
  ✅ fastly      412ms  通畅   jsDelivr · Fastly 节点
  ✅ jsd        1380ms  通畅   jsDelivr CDN · 主入口
  ✅ ghproxy     510ms  通畅   gh-proxy.com 代理
  ❌ raw            连不上   官方 raw 直连
```

`--mirror` 会生成 30 个文件，全部校验过引用完整性：

- `okys-full-jsd.json` / `okys-green-jsd.json` / `okys-best-jsd.json` / `okys-multi-jsd.json` / `wall-jsd.json`
- 同样一套 `-fastly` `-gcore` `-ghproxy` `-ghfast`
- **`okys-mirror-*.json`** ← **镜像多仓版**：一个地址里装下所有线路的所有配置

然后 push 上去：

```bash
git add . && git commit -m "add mirrors" && git push
```

常用参数：

```bash
python3 set-repo.py --mirror all                 # 生成全部 10 条线路
python3 set-repo.py --mirror jsd ghproxy fastly  # 只生成指定的
python3 set-repo.py --list                       # 看所有线路代号
python3 set-repo.py --at 9f8c1a3                 # 用 commit 号生成（替掉分支名）
python3 set-repo.py 你的用户名 仓库名             # 不在 git 目录里也能跑
```

> **坑**：jsDelivr 对 `main` 分支有缓存，刚 push 完可能要等几分钟才生效，
> 且如果它在你 push 完成前就请求过、缓存了一个 404，那会卡更久。
> **急着用就先填 ghproxy 类代理线路**；或者 `--at <commit号>` 生成基于 commit 的地址（内容寻址，没有缓存延迟）。

### 办法 2 · 线路体检页（不装任何东西）

双击 `check-lines.html`（线路体检页），填上用户名和仓库名，点「开始测速」。

它会并发测 10 条线路，按速度排序，直接给出可用地址和**复制按钮** —— 包括镜像多仓版和壁纸清单。
哪条绿了填哪条。不依赖 Python、不联网抓别的站，纯本地页面。

### 办法 3 · Cloudflare Pages（最稳，一劳永逸）

把 GitHub 仓库接到 Cloudflare Pages，得到一个自己的域名，国内可达性明显比 raw 好，而且免费。

1. 打开 Cloudflare 控制台 → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
2. 授权 GitHub，选你那个仓库，分支 `main`
3. 构建设置：**Framework preset = None**，Build command 留空，**Build output directory = `/`**
4. Deploy，等 1 分钟，拿到 `你的项目.pages.dev`

之后你的地址就是：

```
https://你的项目.pages.dev/okys-full.json
https://你的项目.pages.dev/assets/xxxx.jar
```

**以后更新仓库，CF 会自动重新发布**，不用管。想更稳可以在 CF 里绑自己的域名。

### 附 · 用自己的 Cloudflare Worker 反代（可选）

有 CF 账号的话，也可以建个 Worker 当自己的加速器：

```js
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const target = 'https://raw.githubusercontent.com/你的用户名/你的仓库名/main' + url.pathname;
    const r = await fetch(target, { headers: { 'User-Agent': 'Mozilla/5.0' } });
    return new Response(r.body, {
      status: r.status,
      headers: {
        'content-type': r.headers.get('content-type') || 'application/octet-stream',
        'access-control-allow-origin': '*',
        'cache-control': 'public, max-age=600',
      },
    });
  },
};
```

出来的 `xxx.workers.dev` 域名直接当订阅前缀用（`https://xxx.workers.dev/okys-full.json`）。

---

## 四、壳里填哪条

**蜂蜜影视 / FongMi / OK影视（TVBox 系都一样）**：设置 → 配置地址 → 粘贴地址 → 确定，壳自动重启加载。

| 想要什么 | 填这个 |
|---|---|
| **最省心** | `okys-mirror-xxx.json`（镜像多仓版）—— 一条线路挂了，壳里切仓切到另一条，不用改地址 |
| 全都要 | `okys-full-xxx.json` |
| 无成人源 | `okys-green-xxx.json` |
| 启动最快 | `okys-best-xxx.json` |
| 配置里选仓 | `okys-multi-xxx.json` |

`xxx` 就是线路代号：`jsd` / `fastly` / `gcore` / `ghproxy` / `ghfast` …

- 带 `[py]` 的源需要壳带 Python 引擎（蜂蜜影视手机版带 python + quickjs + node，TV 版不一定）。
- 带 `[js]` 的需要 JS 引擎。

---

## 五、壁纸

- 想固定一张：填 `wall/wall-01.jpg` ~ `wall-38.jpg` 里任意一张（配上你的仓库前缀）。
- 想有个清单挑：填 `wall.json`（或镜像版的 `wall-xxx.json`）。
- 想每天自动换：`https://api.dujin.org/bing/1920.php`
- 想每次进去换一张：`https://picsum.photos/1920/1080`

## 六、主题

主题是壳自己的设置（设置 → 外观 / 主题），配置管不到。
配置能控的是**壁纸 + 左上角 logo + 启动公告**，这三样都配好了。

---

## 七、绿源 / 成人源分区

- **绿源在前**，成人源全部压在配置最尾部，名字统一带 `🔞` 前缀（全能版里前 856 个是干净的）。
- 想隐藏：设置 → 点播 → 站点，拉到最底下，把带 `🔞` 的取消勾选。
- 想彻底不要：直接用 `okys-green-*.json`。

---

## 八、以后怎么更新

配置有变化时，只重传改动的文件（通常是那几份 json + 少数驱动）：

```bash
git add . && git commit -m "update" && git push
```

- 用 CF Pages 的：等它自动重新发布（约 1 分钟）。
- 用镜像线路的：jsDelivr 那几条可能有缓存延迟，急的话重新跑一次 `set-repo.py --at <新commit号>`。
- 壳里刷新：设置 → 配置地址 → 重新确定一次。

---

## 九、常见坑

1. **仓库必须 Public** —— 私有仓库、或地址里带 `.git`，壳都拉不到。
2. **别改目录结构、别改文件名** —— `assets/` 里的文件名是配置按哈希对应的，改一个死一个源。
3. **别开 Git LFS** —— 包里的 `.gitattributes` 已经禁掉了，别手动 `git lfs track`，否则 CDN 拿到的是指针不是真文件。
4. **第一次加载慢正常** —— 900+ 个源要解析，壳会转几圈。
5. **某条线路忽然不通** —— 镜像站本身会波动，换一条（`--check` 再测一次），或用镜像多仓版切仓。
6. **某个源点开没数据** —— 大概率是那个源站自己挂了。把源名字发我，我单独测它接口，能修的改配置你刷新就行。
7. **jsDelivr 报文件不存在** —— 要么是刚 push 还没缓存好，要么仓库不是 Public。先换 ghproxy 线路验证一下仓库本身是好的。
8. **push 卡住** —— 116 MB 首次上传，网络差会慢，耐心等，别 Ctrl+C。

---

整理：Zaka
