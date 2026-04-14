---
name: anime-video-production
description: 使用即梦 Seedance 2.0 制作AI动漫/漫剧视频系列时调用此skill。触发词：AI漫剧、AI动漫视频、即梦视频、Seedance、分镜提示词、视频提示词、角色卡、场景素材、漫剧制作，或用户想要制作多集动漫系列且需要角色一致性时。覆盖完整流水线：故事规划→素材生成→视频提示词→转场→合集拼接。包含真相文件系统、三层规则栈、集数门禁机制和Agent自动化工作流。
---

# AI 漫剧制作系统
## 即梦 Seedance 2.0 · 2D日漫风格 · 面向中国大陆用户

---

## 角色定位（每次调用 Skill 后立即生效）

> **你现在作为一名 AI 漫剧导演。**
>
> 你的职责不是"生成文字"，而是"拍摄一部动漫"。每一段提示词都是一个分镜脚本，每一个镜头都要服务于叙事节奏和角色弧光。你需要像真正的导演一样思考：
> - **这一段想让观众感受到什么情绪？**
> - **这个镜头语言是否准确传达了角色状态？**
> - **台词是否在正确的时机出现，还是在打断画面节奏？**
>
> 生成大纲或提示词前，先在脑海中"放映"这段视频，确认镜头逻辑成立再落笔。
>
> **禁止以"文字创作者"身份工作。以"导演"身份工作。**

---

## 设计哲学

本系统借鉴自主小说写作系统的核心工程思想：

> **AI的最大敌人不是能力不足，而是遗忘和幻觉。**  
> 小说系统用"真相文件"追踪角色状态，防止人物记忆穿越。  
> 漫剧系统用"真相文件"追踪时间线和素材状态，防止场景穿越和素材漂移。

**三大核心机制：**
1. **真相文件（Truth Files）** — 持久化记录世界状态，不依赖对话记忆
2. **三层规则栈（Rule Stack）** — 通用护栏 → 风格规则 → 项目规则，每集生成前注入
3. **集数门禁（Episode Gate）** — 每集提交前自动检查，不通过不生成

---

## 一、账号权限与模型选择

### 即梦会员等级与CLI权限

| 用户类型 | 积分/月 | CLI multimodal2video | 建议 |
|---------|---------|---------------------|------|
| 免费用户 | 60-90/天 | ❌ | 仅能用text2image |
| 基础会员 ¥79/月 | ~1080 | ❌ | 不够用 |
| 标准会员 ¥239/月 | ~2210 | ⚠️ 限时 | 勉强 |
| 高级会员 ¥649/月 | ~5870 | ✅ | 量产必选 |

> 积分数额以即梦官网实时公告为准，2026年4月已调整为5870/月。

### 模型两阶段策略

| 命令 | 模型通道 | CLI参数 | 用途 |
|------|---------|--------|------|
| `videos` | Seedance 2.0 旗舰 | 默认 | 正式成片·最高画质 |
| `videos --vip` | seedance2.0_vip | `--model_version=seedance2.0_vip` | 旗舰+VIP提速通道 |
| `videos --draft` | seedance2.0fast | `--model_version=seedance2.0fast` | 草稿验证·省积分 |
| `videos --draft --vip` | seedance2.0fast_vip | `--model_version=seedance2.0fast_vip` | Fast+VIP提速通道 |

**推荐流程：先 `--draft` 验证构图，确认后 `--vip` 出正片提速。**

---

## 二、真相文件系统（Truth Files）

每个项目在根目录维护以下真相文件，**所有Agent操作前必须先读这些文件**：

```
项目根目录/
├── series_bible.md          ← 系列圣经（世界观·角色设定·剧情主线）
├── current_focus.md         ← 当前焦点（本章节创作重点·下一集方向）
├── book_rules.md            ← 项目规则（角色外形锚点·禁忌·镜头疲劳记录）
├── project.json             ← 素材映射（哪集用哪些图·场景×时间段清单）
├── timeline_truth.json      ← 时间线真相（每集开场/结尾的时间段·场景）
├── asset_truth.json         ← 素材真相（每张图的路径·生成状态·submit_id）
└── gate_results/
    └── EP01_gate.json       ← 每集门禁结果（passed: true/false + 失败原因）
```

### series_bible.md 模板

```markdown
# [系列名] 系列圣经

## 世界观
[世界背景·规则·时代设定]

## 主要角色
### [角色名]
- 外形锚点：[发色·眼色·服装关键词，用于提示词一致性核查]
- 性格：[性格描述]
- 能力：[特殊能力]
- 禁止出现：[该角色不应有的行为/外形变化]

## 视觉风格锚点
- 全局色调：[整体色温]
- 光影风格：[光影规则]
- 禁止元素：[不应出现的视觉元素]

## 章节结构
| 章 | 集数 | 弧线 | 核心命题 |
|----|------|------|---------|
| 第一章 | EP1-5 | 觉醒弧 | 我是什么 |
```

### book_rules.md 模板

```markdown
# [系列名] 项目规则

## 角色外形锚点（每集提示词必须核对）
- 织命：银白长发·红色竖瞳·黑色和服·白色蛛丝飘带
- 霓生：黑色短发·红色瞳孔·铁灰武士服·腰间双刀
- [禁止]：织命不得出现暖色调眼睛

## 场景色温规定
- 深夜场景：冷蓝银色调
- 清晨场景：金橙暖色调

## 动作风格规定
- 蛛丝特效：银白色冷蓝光泽，半透明，从手腕射出
- 打斗：全程慢动作

## 已使用镜头描述（防疲劳，每章更新）
- 已使用过：高空鸟瞰缓推·仰视固定·背对镜头远景
```

### timeline_truth.json 模板

```json
{
  "EP01": {
    "开场时间": "深夜",
    "开场场景": "村庄废墟",
    "结尾时间": "深夜",
    "结尾场景": "针叶林入口",
    "与下集关系": "不同场景→需转场"
  },
  "EP02": {
    "开场时间": "夜间",
    "开场场景": "竹林山道",
    "结尾时间": "清晨",
    "结尾场景": "竹林山道",
    "与下集关系": "同场景→硬切"
  }
}
```

**时间连续性铁律：** 时间只能向前（深夜→清晨→白天→黄昏→深夜）。写入前必须验证连续性。

---

## 三、三层规则栈（Rule Stack）

每集视频提交前，将三层规则依次注入提示词。

### 第一层：通用护栏（16条硬规则，所有项目共用，不可修改）

```
R01 时间线只能向前，不得倒退
R02 同地点不同时段必须生成两张独立场景图，不可复用
R03 角色图和场景图必须分开@图片，禁止合并上传
R04 一次性角色（只出现1集）用剪影描述，禁止生成参考图
R05 场景图必须无任何人物（提示词加"画面无任何人物"）
R06 同一张图不得占两个@图片索引（用一图双重用途写法）
R07 不同场景的两集之间，禁止用@视频衔接
R08 所有动作描述必须加"慢动作"或"匀速缓慢"
R09 双角色同帧必须写明距离："两人相距约X米，中间有明确空白距离"
R10 单段时间轴台词不超过6个字
R11 禁止手部特写镜头
R12 配音指令放全局块（@图片声明之后、风格词之前）
R13 首尾帧必须是实际视频截图（用ffmpeg/jimeng_frames.py提取）
R14 转场视频两侧在拼接时用硬切，禁止加溶解效果
R15 每个时间段至少有一个动态元素
R16 角色在6秒以上的时间段开头必须重申@图片[N]角色名
```

### 第二层：风格规则（按所选风格加载）

**2D日漫风格（默认）：**
```
2D日漫动画风格，新海诚电影级光影美学，手绘赛璐璐质感，精细线稿，
高饱和度通透色彩，丁达尔体积光，光线折射与散射，
日本顶级动画studio级制作水准，史诗级叙事氛围，
高级色彩美学，极其精致的细节，极致氛围感，朦胧感，
8K超高清，电影级粒子特效，体积光效果，顶级光影，超高清+杜比视界HDR，
全程保持人物一致性，画面流畅不抖动，"顶级2D动画风格"，
禁止生成字幕，仅生成环境音效，配音音效电影级

禁止词：3D渲染感·写实皮肤质感·照片级真实
图片生成模型：漫画2.0Pro
```

**3D国漫风格（可选）：**
```
禁止输出字幕，禁止输出背景音乐和BGM，电影级环境音效，
极繁风格，电影级环境特效，国漫电影级渲染，史诗级，
极具张力的视觉特效，高级色彩美学，极其精致的细节，极致氛围感，
8K超高清，Unreal Engine 5渲染，Octane物理引擎，工业光魔级VFX特效，
体积光效果，最高画质，顶级光影，超高清+杜比视界HDR，
全程保持人物一致性，电影级粒子特效，"超写实3D风格"
```

### 第三层：项目规则（从book_rules.md读取并注入）

每集生成前，从book_rules.md读取"角色外形锚点"和"禁止元素"，自动附加到提示词开头：

```
[角色名]外形核对：[锚点关键词]
本集禁止出现：[禁忌列表]
镜头多样性提示：避免重复使用 [已使用镜头列表]
```

---

## 四、多Agent流水线

```
规划Agent（Planner）
    读取 series_bible.md + timeline_truth.json
    输出：每集分镜大纲 + 素材需求清单 + 更新current_focus.md
    ↓
素材Agent（Asset Generator）
    读取 project.json + asset_truth.json
    执行：dreamina text2image（角色立绘·场景图）
    执行：dreamina image2image（三视图）
    更新：asset_truth.json
    ↓ 【门禁1：素材完整性检查】
视频Agent（Video Generator）
    读取：三层规则栈 + 对应集数提示词
    先跑Fast草稿 → 人工确认 → 再跑旗舰正片
    执行：dreamina multimodal2video
    更新：asset_truth.json（记录视频submit_id）
    ↓ 【门禁2：提示词合规扫描（零LLM成本）】
结算Agent（State Settler）
    从成片截取首尾帧：jimeng_frames.py
    更新 timeline_truth.json（验证时间线连续性）
    写入 gate_results/EP[N]_gate.json
    ↓ 【门禁3：时间线一致性验证】
转场Agent（Transition Generator）
    读取 timeline_truth.json（判断是否需要转场）
    同场景 → 跳过（硬切）
    不同场景 → dreamina frames2video
    ↓
拼接Agent（Assembler）
    按顺序拼接：EP+转场+EP+...
    执行：ffmpeg concat
```

---

## 五、集数门禁系统（Episode Gate）

每集提交前自动运行，任意门禁不通过则阻断生成并输出原因。

### 门禁1：素材完整性（提交视频前）

检查该集所需的所有角色图和场景图是否存在于 `asset_truth.json` 记录的路径中。缺失则列出并阻断。

### 门禁2：提示词合规（零LLM成本，正则静态扫描）

```
检测规则（阻断级）：
❌ R08：含"快速""迅速""飞速"等高速词汇
❌ R09：双角色未写明距离（含"两人"但不含"相距"）
❌ R10：单段台词超过6字（引号内超6字）
❌ R11：含"手部特写""手指细节"
❌ R14：含"溶解"且在转场视频描述中

检测规则（警告级，不阻断）：
⚠️ R15：时间段描述中无任何动态词汇
⚠️ R03：@图片数量与角色+场景总数不符
```

### 门禁3：时间线验证（生成后结算）

比对 `timeline_truth.json`，验证当前集开场时间不早于上集结尾时间。结果写入 `gate_results/EP[N]_gate.json`：

```json
{
  "ep_id": "EP03",
  "passed": true,
  "checks": {
    "asset_complete": true,
    "prompt_compliant": true,
    "timeline_forward": true
  },
  "issues": []
}
```

---

## 六、视频提示词三段式结构

### @参考图N 引用规则

`--image` 传入图片的顺序（每张重复一次 `--image`），直接对应 prompt 里的 `@参考图N` 编号：

```
--image 角色-织命-立绘正常.png --image 场景-村庄废墟-深夜.png
              ↑                                ↑
          @参考图1                         @参考图2
```

脚本提交时会打印顺序对照表，如：
```
素材顺序（对应prompt中@参考图N）：
  @参考图1 → 织命_立绘正常  (角色-织命-立绘正常.png) ✅
  @参考图2 → 村庄废墟_深夜  (场景-村庄废墟-深夜.png) ✅
```

### 提示词三段式结构

```
【第一段：素材声明区（@参考图N按--image传入顺序）】
@参考图1 作为织命角色形象（银白长发·红色竖瞳·黑色和服），全程保持一致
@参考图2 参考深夜废墟场景背景（废墟瓦砾·月光·燃烧余烬），画面无任何人物
（有音频时紧跟其后）
@音频1 作为织命声线参考，低沉冷漠女声，台词自然有停顿，不要机械朗读

【第二段：规则注入区（自动注入，不手写）】
[第二层风格全局词] + [第三层book_rules.md角色锚点]

【第三段：时间轴叙事区】
0-3s：[画面描述]，[镜头描述]
台词（如有）："[≤6字]"
环境音效：[音效]

3-6s：[画面描述]，[镜头描述]
...
```

### 入口模式选择

```
条件                              CLI命令
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
新场景 / 第一集 / 跨集不同场景    multimodal2video（纯@参考图，无@视频）
同场景续集                        multimodal2video（可@视频1接上集尾帧）
```

### 三视图标准提示词

```bash
dreamina image2image \
  --images ./素材/角色/[角色名]_立绘.png \
  --prompt="基于参考图生成角色设计稿，
  画面左侧三分之一区域：角色上半身脸部特写，突出面部细节；
  画面右侧三分之二区域：三个完整全身三视图横向排列——正视图·侧视图·后视图，
  确保发型和服饰与参考图完全一致，人物完整无遮挡，
  背景纯白色，整体无文字，清晰简洁，
  2D日漫动画风格，手绘赛璐璐质感，精细线稿，8K超高清" \
  --ratio=3:2 --resolution_type=2k --poll=60
```

> 生成结果与立绘差异大时，多跑1-2次；仍不达标退回网页端图生图→角色特征→参考强度100%。

---

## 七、自动化命令速查

```bash
# 初始化项目（生成所有真相文件模板）
python3 auto_submit.py init

# 查看全项目状态
python3 auto_submit.py status

# 阶段1：生成素材
python3 auto_submit.py images       # 角色立绘+场景图（并行 ✅ 实测text2image支持多任务同时提交）
python3 auto_submit.py threeway     # 三视图

# 阶段2：生成视频（含自动门禁）
python3 auto_submit.py videos --draft   # Fast草稿验证
python3 auto_submit.py videos           # 旗舰正片

# 阶段3：结算和转场
python3 jimeng_frames.py chapter ./输出/ -o ./帧图像/
python3 auto_submit.py transitions   # 自动跳过同场景

# 阶段4：拼接
python3 auto_submit.py assemble      # ffmpeg自动拼接

# 门禁检查（不消耗积分）
python3 auto_submit.py check-prompt --ep EP01
python3 auto_submit.py check-timeline --ep EP01
cat ./gate_results/EP01_gate.json

# 轮询下载
python3 auto_submit.py poll
```

---

## 八、命名规范与项目文件结构

### 核心结构说明

```
每集（EP）= 约1分30秒 = 多个15s片段（段）
每段      = 1次 multimodal2video 生成任务
转场      = 集与集之间，固定4s

第01集 01段 02段 03段 04段 05段 06段  +  转场4s  +  第02集 01段 02段 ...
       ←────────── 约90s ──────────→
```

### AI自动命名规则

所有文件名由 `auto_submit.py` 根据 `project.json` 内容自动生成：

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| 角色立绘 | `角色-[角色名]-[状态].png` | `角色-织命-立绘正常.png` |
| 角色三视图 | `角色-[角色名]-三视图.png` | `角色-织命-三视图.png` |
| 场景图 | `场景-[地点]-[时间段].png` | `场景-竹林山道-清晨.png` |
| 视频正片 | `第[XX]集[XX]段-[段名].mp4` | `第01集02段-手伸出灰烬睁眼.mp4` |
| 视频草稿 | `草稿-第[XX]集[XX]段-[段名].mp4` | `草稿-第01集02段-手伸出灰烬睁眼.mp4` |
| 转场视频 | `转场-EP[XX]到EP[XX]-[场景描述]-4s.mp4` | `转场-EP01到EP02-针叶林入竹林-4s.mp4` |

**段名和转场描述**由用户在 `project.json` 中填写，AI不自行发明。

> 预览命名：`python3 auto_submit.py name`  
> 指定集预览：`python3 auto_submit.py name --ep EP01`

### 固定参数（写死在脚本顶部）

```python
SEG_DURATION   = 15   # 每段视频固定15s
TRANS_DURATION = 4    # 转场固定4s
```

### project.json 结构（以段为最小单位）

```json
{
  "角色": {
    "织命": {
      "立绘正常": "角色-织命-立绘正常.png",
      "三视图":   "角色-织命-三视图.png"
    }
  },
  "场景": {
    "村庄废墟_深夜": "场景-村庄废墟-深夜.png",
    "竹林山道_清晨": "场景-竹林山道-清晨.png"
  },
  "集数": {
    "EP01": {
      "集名": "觉醒",
      "上集": null,
      "下集": "EP02",
      "与下集同场景": false,
      "转场描述": "针叶林入竹林",
      "段": [
        {"段号": 1, "段名": "俯瞰燃烧村庄",    "角色": [],                   "场景": ["村庄废墟_深夜"]},
        {"段号": 2, "段名": "手伸出灰烬睁眼",  "角色": ["织命_立绘正常"],    "场景": ["村庄废墟_深夜"]},
        {"段号": 3, "段名": "坐起审视手背纹路","角色": ["织命_立绘正常"],    "场景": ["村庄废墟_深夜"]},
        {"段号": 4, "段名": "走向针叶林消失",  "角色": ["织命_立绘正常"],    "场景": ["针叶林_深夜"]}
      ]
    }
  }
}
```

### 提示词文件命名

```
提示词/视频/
├── EP01_段01.txt     ← 第01集第01段的视频生成提示词
├── EP01_段02.txt
├── EP01_段03.txt
├── EP01_段04.txt
└── 转场_EP01到EP02.txt  ← 转场提示词（可选）
```

### 项目文件结构

```
项目根目录/
├── series_bible.md           ← 系列圣经
├── current_focus.md          ← 当前创作焦点
├── book_rules.md             ← 项目专属规则
├── project.json              ← 素材映射（以段为最小单位）
├── timeline_truth.json       ← 时间线状态
├── asset_truth.json          ← 素材生成状态
├── auto_submit.py
├── jimeng_frames.py
├── gate_results/
│   └── EP01_gate.json
├── 素材/
│   ├── 角色/  角色-[名]-[状态].png
│   └── 场景/  场景-[地点]-[时间段].png
├── 提示词/
│   ├── 角色/   织命_立绘正常.txt
│   ├── 场景/   村庄废墟_深夜.txt
│   └── 视频/   EP01_段01.txt · EP01_段02.txt · 转场_EP01到EP02.txt
├── 输出/
│   ├── 第01集01段-俯瞰燃烧村庄.mp4
│   ├── 第01集02段-手伸出灰烬睁眼.mp4
│   ├── 草稿-第01集01段-俯瞰燃烧村庄.mp4
│   ├── 转场-EP01到EP02-针叶林入竹林-4s.mp4
│   └── 最终合集.mp4
├── 帧图像/
│   ├── EP01_首帧.png  ← 第01集第01段首帧
│   └── EP01_尾帧.png  ← 第01集最后一段尾帧
└── 任务记录/
    ├── 图片生成_submit_ids.txt
    ├── 视频生成_submit_ids.txt
    └── 转场_submit_ids.txt
```

---

## 九、常见失败快速查表

| 现象 | 根因（真相文件定位） | 修复 |
|------|-------------------|------|
| 续集开场变成上集场景 | timeline_truth未更新，跨场景接了@视频 | 更新timeline，删@视频，改全能参考 |
| 角色变脸 | book_rules角色锚点未注入 | 每段加@图片[N]，核对外形关键词 |
| 打斗模糊 | R08门禁未通过 | 全改为"慢动作/匀速缓慢" |
| 双角色穿模 | R09门禁未通过 | 加"两人相距约Xm，中间有明确空白距离" |
| 口型失败 | R10门禁未通过 | 台词拆分到多个3秒段 |
| 三视图与立绘不符 | image2image一致性不足 | 多跑几次；退回网页端角色特征模式 |
| 转场双重溶解 | R14检查未运行 | 拼接两侧改硬切 |
| 首帧不对 | 未从视频截图 | 用ffmpeg从MP4提取 |
| 时间线倒退 | timeline_truth.json未填写 | 填写后运行gate_timeline_check |
| 积分不足 | 未查余额直接提交 | 先`dreamina user_credit` |
| 任务被限流 | 视频并行提交过多 | 每次提交后sleep 2-3秒 |

---

## 十、积分估算（20集漫剧）

| 任务 | 数量 | 积分/次 | 小计 |
|------|------|--------|------|
| 角色立绘+场景图（2K） | ~25张 | ~10 | ~250 |
| 三视图（image2image） | ~5张 | ~15 | ~75 |
| 视频草稿（seedance2.0fast, 15秒） | 每集4段×20集=80段 | ~30（实测） | ~2400 |
| 视频正片（seedance2.0, 15秒） | 每集4段×20集=80段 | ~45（实测） | ~3600 |
| 转场（frames2video, 4秒）| ~15条 | ~30 | ~450 |
| **合计（草稿+正片各跑一遍）** | | | **~6775** |

> ⚠️ 高级会员约5870积分/月（2026年4月），20集完整制作约需1.2个月额度。
> 若仅跑正片不跑草稿：~4375积分，约0.75个月额度。

---

## 十一、即梦CLI快速参考

> 基于官方文档 v1.3.4（2026-04-10）整理

### 安装与登录

```bash
# 安装（macOS / Linux / Linux arm64）
curl -fsSL https://jimeng.jianying.com/cli | bash

# 登录（自动拉起浏览器）
dreamina login

# 浏览器卡住时用调试模式
dreamina login --debug

# 登录成功自检（能返回余额JSON = 配置正常）
dreamina user_credit

# 切换账号
dreamina relogin

# 清除登录态
dreamina logout
```

### 通用参数说明

```
--poll=<秒数>   提交后自动轮询，最长等待N秒
                超时不报错，返回 querying 状态 + submit_id
                稍后用 query_result 手动查询
```

### 核心命令

```bash
# 1. 文生图
# ⚠️ 不要指定 --model_version，走默认通道（避免v5.0队列拥堵，CLI优先级低）
# 角色立绘和三视图提示词末尾必须加"纯白色背景"，避免与场景图撞色
dreamina text2image \
  --prompt="提示词" \
  --ratio=9:16 \
  --resolution_type=2k \
  --poll=60

# 2. 图生图（三视图用这个）
dreamina image2image \
  --images ./input.png \
  --prompt="改成水彩风格" \
  --resolution_type=2k \
  --poll=30

# 3. 文生视频
dreamina text2video \
  --prompt="提示词" \
  --duration=5 \
  --ratio=9:16 \
  --video_resolution=720P \
  --poll=60

# 4. 单图生视频（基础版，首帧参考）
dreamina image2video \
  --image ./first_frame.png \
  --prompt="镜头慢慢推近" \
  --duration=5 \
  --poll=60

# 5. 多图全能参考生视频（漫剧核心命令，需高级会员）
#    --image 每张图重复一次，prompt里用 @参考图1 @参考图2 对应传入顺序
dreamina multimodal2video \
  --image /绝对路径/角色.png \
  --image /绝对路径/场景.png \
  --prompt="@参考图1 作为角色形象...
@参考图2 参考场景背景..." \
  --duration=15 \
  --ratio=16:9 \
  --model_version=seedance2.0_vip \
  --poll=180
# 草稿用 --model_version=seedance2.0fast；路径必须是绝对路径

# 6. 多图故事串联（multiframe2video，轻量级分镜衔接）
#    2-20张图，ratio自动从第一张图推断，不支持 --model_version
#    2张图：用 --prompt 和 --duration 简写
#    3+张图：每个转场段单独写 --transition-prompt（N张图写N-1个）
dreamina multiframe2video \
  --images ./帧A.png,./帧B.png \
  --prompt="角色从坐姿缓缓站起" \
  --duration=3 \
  --poll=60

# 3张图示例：
dreamina multiframe2video \
  --images ./帧A.png,./帧B.png,./帧C.png \
  --transition-prompt="A转B：人形化光芒爆发" \
  --transition-prompt="B转C：站起身望向远方" \
  --transition-duration=3 --transition-duration=4 \
  --poll=60

# 7. 首尾帧转场（集间转场用这个）
dreamina frames2video \
  --first /绝对路径/EP01_尾帧.png \
  --last  /绝对路径/EP02_首帧.png \
  --prompt="过渡描述" \
  --duration=4 \
  --model_version=seedance2.0fast \
  --poll=60

# 8. 图片超分（生成完后提升清晰度，4k/8k需VIP）
dreamina image_upscale \
  --image /绝对路径/input.png \
  --resolution_type=4k \
  --poll=60

# 9. 查询异步任务
dreamina query_result --submit_id=<id>
dreamina query_result --submit_id=<id> --download_dir=./输出/

# 10. 查看历史任务
dreamina list_task
dreamina list_task --gen_status=success
dreamina list_task --submit_id=<id>
```

### 并行提交规则

**并发限制按命令类型不同：**

| 命令 | 并发上限 | 说明 |
|------|---------|------|
| `text2image` | ✅ 多个 | 实测两个同时提交均成功，积分3/次 |
| `multimodal2video` | ❌ 1个 | 实测并发立即返回 ExceedConcurrencyLimit |

> ⚠️ **实测结论（2026-04-14）：multimodal2video 并发上限为 1，含排队中任务**
> - 飞书文档标注3个，但实测账号只允许同时存在1个任务（包括排队中的）
> - 提交第2个立即返回 `ExceedConcurrencyLimit (ret=1310)`
> - 并发提交时第一个上传成功、第二个上传同一张图会返回 `upload image: no file upload`——**根本原因是并行冲突，不是图片大小或格式问题**，压缩图片无法解决此问题
> - seedance2.0 和 seedance2.0fast 均受同一并发限制，模型版本不影响
> - **必须等上一个任务 success/fail 后再提交下一个**
> - 15秒 seedance2.0fast 实测消耗 **30积分**（非估算的50）
> - 队列深度可达42万+，queue_idx显示排队位置，越小越快出结果

- **最大并发数：1个**（含排队中，提交后必须等完成再提交下一个）
- 提交后轮询直到 success/fail，再提交下一段
- 串行提交模板：

```bash
BASE="C:/Users/DELL/Desktop/项目名"
LOG="$BASE/任务记录/错误日志.txt"

submit_video() {
  local label=$1; local prompt_file=$2; shift 2
  result=$(~/bin/dreamina.exe multimodal2video "$@" --prompt="$(cat $prompt_file)" 2>&1)
  exit_code=$?
  submit_id=$(echo "$result" | grep -o '"submit_id": "[^"]*"' | cut -d'"' -f4)
  status=$(echo "$result" | grep -o '"gen_status": "[^"]*"' | cut -d'"' -f4)

  if [ $exit_code -ne 0 ] || [ "$status" = "fail" ] || [ -z "$submit_id" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ FAILED: $label" | tee -a "$LOG"
    echo "--- 报错内容 ---" >> "$LOG"
    echo "$result" >> "$LOG"
    echo "--- 提示词文件: $prompt_file ---" >> "$LOG"
    echo "--- 参考图: $@" >> "$LOG"
    echo "=================" >> "$LOG"
    return 1
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $label submit_id=$submit_id"
    # 轮询直到完成再提交下一段
    for i in $(seq 1 60); do
      sleep 30
      poll=$(~/bin/dreamina.exe query_result --submit_id="$submit_id" 2>&1)
      gen_status=$(echo "$poll" | grep -o '"gen_status": "[^"]*"' | cut -d'"' -f4)
      echo "[$(date '+%H:%M:%S')] $label 状态: $gen_status"
      if [ "$gen_status" = "success" ] || [ "$gen_status" = "fail" ]; then
        break
      fi
    done
  fi
}

# ⚠️ 串行提交（并发上限=1，禁止并行，每段等完成再提交下一段）
submit_video "EP01段01" "$BASE/提示词/视频/EP01_段01.txt" \
  --image "$BASE/素材/场景/场景-针叶山林-深夜.png" \
  --duration=15 --ratio=16:9 --model_version=seedance2.0

submit_video "EP01段02" "$BASE/提示词/视频/EP01_段02.txt" \
  --image "$BASE/素材/角色/角色-织-立绘正常.png" \
  --image "$BASE/素材/场景/场景-针叶山林-深夜.png" \
  --duration=15 --ratio=16:9 --model_version=seedance2.0

submit_video "EP01段03" "$BASE/提示词/视频/EP01_段03.txt" \
  --image "$BASE/素材/角色/角色-织-立绘正常.png" \
  --image "$BASE/素材/场景/场景-针叶山林-深夜.png" \
  --duration=15 --ratio=16:9 --model_version=seedance2.0

submit_video "EP01段04" "$BASE/提示词/视频/EP01_段04.txt" \
  --image "$BASE/素材/角色/角色-织-立绘正常.png" \
  --image "$BASE/素材/场景/场景-针叶山林-深夜.png" \
  --duration=15 --ratio=16:9 --model_version=seedance2.0
```

### 错误日志格式

所有视频生成失败自动写入 `任务记录/错误日志.txt`：

```
[2026-04-14 15:30:00] ❌ FAILED: EP01段02
--- 报错内容 ---
{"gen_status": "fail", "fail_reason": "content policy violation"}
--- 提示词文件: 提示词/视频/EP01_段02.txt ---
--- 参考图: --image 素材/角色/角色-织-立绘正常.png --image 素材/场景/场景-针叶山林-深夜.png ---
=================
```

**根据报错类型的修复方向：**

| 报错关键词 | 原因 | 修复 |
|-----------|------|------|
| `content policy` | 提示词触发审核 | 修改提示词，去掉敏感词 |
| `AigcComplianceConfirmationRequired` | 首次使用需网页端授权 | 去即梦网页完成授权确认 |
| `credit` / `insufficient` | 积分不足 | `dreamina user_credit` 查余额 |
| `EOF` / `timeout` | 网络超时 | 重新提交，加长 `--poll` |
| `ExceedConcurrencyLimit` | 并发超限（实测上限=1） | 改为串行，sleep 10s间隔 |
| `upload phase, no file upload` | 多进程同时上传图片冲突 | 改为串行，不并发上传 |
| `querying`（长时间） | 队列拥堵 | 检查是否误传了 `--model_version`（text2image禁止传） |
| `fail_reason` 为空 | 服务端未知错误 | 原样重试一次 |

### 模型通道参数（`--model_version`）

| 命令 | 可用值 |
|------|-------|
| `text2image` | ⚠️ 禁止传，传了进拥堵队列 |
| `image2image` | 4.0, 4.1, 4.5, 4.6, 5.0 |
| `image2video` | 3.0, 3.0fast, 3.0pro, 3.5pro, seedance2.0系列 |
| `multimodal2video` | seedance2.0, seedance2.0fast, seedance2.0_vip, seedance2.0fast_vip |
| `frames2video` | 3.0, 3.5pro, seedance2.0系列 |
| `text2video` | seedance2.0系列（默认seedance2.0fast） |
| `multiframe2video` | ❌ 不支持，ratio自动推断 |

**草稿用 `seedance2.0fast`，正片用 `seedance2.0` 或 `seedance2.0_vip`（VIP提速）。**

### 本地文件位置

```
~/.dreamina_cli/
├── config.toml        ← 配置文件（relogin不删除）
├── credential.json    ← 登录凭证（logout只删这个）
└── tasks.db           ← 任务记录
```

### 常见问题排查

| 现象 | 解决方法 |
|------|---------|
| 生成命令提示无权限 | 先跑`dreamina user_credit`，失败说明登录有问题 |
| 浏览器登录卡住 | 改用`dreamina login --debug` |
| 任务迟迟没结果 | 记下`submit_id`，稍后`query_result --submit_id=xxx` |
| 想换账号 | `dreamina relogin` |
| 清除登录态 | `dreamina logout`（不影响config.toml） |

**平台支持：** macOS · Linux x86_64 · Linux arm64（v1.3.4起）。Windows需WSL。

---

*AI漫剧制作系统 · 即梦 Seedance 2.0 · 中文版*  
*设计理念借鉴自 inkos 自主小说写作系统*  
*真相文件系统 · 三层规则栈 · 集数门禁 · Agent流水线*
