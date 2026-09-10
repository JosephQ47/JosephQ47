# 维护说明

Matrix 主题的 GitHub profile README。所有视觉资源均在本仓库内生成，
除 shields.io 与两个 demolab 服务外无第三方依赖。

## 文件结构

```
README.md                        主页内容（仓库名与用户名一致，GitHub 才会把它渲染到主页）
gen_matrix.py                    数字雨生成器，仅标准库，seed 固定所以输出确定
assets/matrix-banner.svg         顶部数字雨横幅   由 banner.yml 生成
assets/matrix-footer.svg         底部数字雨页脚   由 banner.yml 生成
assets/metrics-calendar.svg      3D 等距提交日历  由 metrics.yml 生成
.github/workflows/banner.yml     跑 gen_matrix.py 生成横幅与页脚 + XML 校验
.github/workflows/metrics.yml    调 lowlighter/metrics 生成日历
.github/workflows/snake.yml      调 Platane/snk 生成贡献蛇（当前 README 未引用）
```

## 配色

```
背景   #0D0208
主绿   #00FF41
中绿   #008F11
暗绿   #003B00
```

## 三个 workflow

| workflow | 触发 | 需要 token |
|---|---|---|
| `banner.yml` | 改动 `gen_matrix.py` 时自动，或手动 | 不需要 |
| `metrics.yml` | 每日 00:00 UTC，或手动 | 需要 `METRICS_TOKEN` |
| `snake.yml` | 每日 00:10 UTC，或手动 | 不需要 |

`metrics.yml` 与 `snake.yml` **刻意不在 push 时触发**。三个 workflow 同时往
`main` 提交会互相顶掉 —— 首次部署就栩在这上面：banner 先推成功，
snake 的 checkout 基于上一个 commit，9 秒后推时远端已前进，
non-fast-forward 被拒。现在 cron 错开 10 分钟，提交步骤也加了
`pull --rebase --autostash` 重试兵底。

## 配 METRICS_TOKEN

1. https://github.com/settings/tokens → Generate new token (classic)
2. Expiration 选长一些；到期后日历就不再刷新
3. scope 勾 **`read:user`**；仓库全是 private 时还得勾 **`repo`**，
   不然统计基本是空的
4. 生成后立即复制（只显示一次）
5. 仓库 Settings → Secrets and variables → Actions → New repository secret
   Name 填 `METRICS_TOKEN`

隐私：`metrics.yml` 的 `base` 刻意不含 `repositories` 插件 —— 那个插件会把
仓库名列在卡片上，加了 `repo` scope 后私有仓库名会因此出现在公开主页。
现在只输出“哪天有多少提交”的格子。

另外若仓库全为 private，需到 https://github.com/settings/profile 勾上
**Include private contributions on my profile**，不然热力图是空的。
该开关只显示“某天有提交”，不显示仓库名。

## 改数字雨

参数在 `gen_matrix.py` 底部的 `build()` 调用：

- `title` / `subtitle` —— 大字与副标题
- `col_w` —— 列间距，调小更密（现 20）
- `n_rows` —— 每列字符数（现 20）
- `GLYPHS` —— 字符集
- 颜色在 `depth_style()` 里，`depth=0` 是下落的“头”

改完 push，`banner.yml` 会自动重新生成。本地验证直接跑
`python gen_matrix.py`，输出字节级确定。

注意脚本 `print` 的是 Python **字符数**不是字节数 —— 片假名每个占 3 字节
（UTF-8），两者差约 1000，不是文件不一致。

## 改打字机台词

README 里 `readme-typing-svg` 那个 URL，`lines=` 用 `;` 分隔每行，空格写 `%20`。

## 踩过的坑

### 1. 为何全自托管

2026-09-10 实测，常用的公共 README 服务已大面积停服：

```
github-readme-stats.vercel.app          503  DEPLOYMENT_PAUSED
github-readme-activity-graph.vercel.app 402  Payment Required
github-profile-trophy.vercel.app        402  Payment Required
capsule-render.vercel.app               连续超时，21s 无响应
```

拿作者本人账号去测 github-readme-stats 也是同样 503，所以是公共实例
全局停服，不是参数或账号问题。存活的：shields.io、
readme-typing-svg.demolab.com、streak-stats.demolab.com、komarev.com。

结论：能自托管的就自托管。GitHub Actions 生成 SVG + raw 引用这条路不会失效。

### 2. metrics 自己提交，不要再加 git 步骤

`lowlighter/metrics` 通过 GitHub API 提交产物（`committer_token` 默认用内置
`GITHUB_TOKEN`），所以它的 job 里本来就不应有 `actions/checkout`。
若额外加了手动 `git add / commit / push`，workspace 不是 git 仓库，
git 直接 fatal，**exit code 128**。

### 3. isocalendar 不读 CSS 变量

它把颜色写死在每个 `path` 元素的 `fill` 属性上，实测 `var()` 在输出里
出现 **0 次**，`--color-calendar-graph-day-*` 那套变量根本没人读。
1077 个 `path` 带着 `fill="#ebedf0"`（GitHub 浅色主题的空格子色），
所以底板是白的。只能用属性选择器覆盖（CSS 规则优先级高于
presentation attribute），具体见 `metrics.yml` 里的 `extras_css`。

空格子不要取背景色 `#0D0208` —— 与背景同色会让柱子悬在虚空里，
看不出是个日历，留一点暗绿才保得住网格形态。

### 4. 日历标题会被裁

`h2` 带 `class="field"`，规则是 `display:flex` 加 `line-height:normal`，
实测 `getBoundingClientRect` 高度只有 21px 而字号 16px。
把 SVG 当文档直接打开看不出问题，但用 `img` 引入时超出 box 的部分
会被边界裁掉，标题就缺下半截。给 `padding-bottom` 或 `line-height` 即可。

两个容易误判的方向（都验证过不成立）：不是 `display:none` 影响了 puppeteer
测高，也不是 `img width=100%` 把 480 拉到 880 的缩放问题 —— 原生
480x310 一样被裁。

### 5. extras_css 里不能出现尖括号

`extras_css` 会被内嵌进 SVG，而 SVG 按 XML 解析。**CSS 注释对 XML 不是注释**，
注释里写一个 less-than 就会被当成标签开头，`mismatched tag`，
整个 SVG 报废。

### 6. 图片缓存

更新 SVG 后主页可能仍显示旧图（GitHub camo 代理缓存），等几分钟或强制刷新。

## 关于项目仓库

README 的 `./projects` 一节只写文字描述、不放仓库链接，
因为那些仓库为私有。如果以后要公开某个仓库，建议新建一个干净仓库
重新提交，而不是把现有私有仓库转公开 —— 删文件只能改变当前快照，
Git 历史里的内容仍然可以被翻出来。
