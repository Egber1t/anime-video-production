#!/usr/bin/env python3
"""
即梦漫剧自动化提交脚本 v3.0
基于即梦CLI官方文档 v1.3.4（2026-04-10）

命令说明：
  image2video       基础图生视频（单张图，--image 单数，无需会员）
  multimodal2video  全能参考视频（多张图，--images 复数，需高级会员）
                    ← 漫剧制作用这个，支持@参考图N多图参考

结构说明：
  每集（EP）= 约1分30秒 = 多个15s片段（段）
  每段 = 1次 multimodal2video 生成任务
  转场 = 集与集之间，固定4s

命名规范：
  视频段：  第01集01段-织命废墟觉醒.mp4
  草稿段：  草稿-第01集01段-织命废墟觉醒.mp4
  转场：    转场-EP01到EP02-针叶林入竹林-4s.mp4
  角色图：  角色-织命-立绘正常.png
  三视图：  角色-织命-三视图.png
  场景图：  场景-村庄废墟-深夜.png

@参考图N 引用规则：
  --images 按顺序传入图片路径（空格分隔）
  prompt里 @参考图1=第1张, @参考图2=第2张, 以此类推
  顺序：先角色图（按段.角色列表顺序），再场景图（按段.场景列表顺序）

固定参数：
  每段时长 = 15s（SEG_DURATION）
  转场时长 = 4s（TRANS_DURATION）

用法：
  python3 auto_submit.py init                          # 生成配置模板
  python3 auto_submit.py name [--ep EP01]              # 预览命名+@参考图N顺序
  python3 auto_submit.py status                        # 查看项目状态
  python3 auto_submit.py images                        # 生成角色立绘+场景图
  python3 auto_submit.py threeway                      # 生成三视图
  python3 auto_submit.py videos [--draft] [--vip]      # 生成所有集的所有段
  python3 auto_submit.py videos --ep EP01              # 只生成指定集
  python3 auto_submit.py transitions                   # 生成转场视频
  python3 auto_submit.py assemble                      # ffmpeg拼接合集
  python3 auto_submit.py poll                          # 轮询下载
  python3 auto_submit.py check-prompt --ep EP01 [--seg 1]
"""

import os
import re
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────
# 固定参数
SEG_DURATION   = 15    # 每段视频固定15s
TRANS_DURATION = 4     # 转场固定4s
VIDEO_RATIO    = "9:16"
RESOLUTION     = "2k"

# 模型通道（--model 参数值）
# 用法：
#   python3 auto_submit.py videos            → 旗舰（默认）
#   python3 auto_submit.py videos --vip      → 旗舰VIP（提速，需高级会员）
#   python3 auto_submit.py videos --draft    → Fast（省积分）
#   python3 auto_submit.py videos --draft --vip  → FastVIP（提速+省积分）
MODEL_FLAGSHIP  = None                   # 旗舰，不传--model参数
MODEL_VIP       = "seedance2.0_vip"     # 旗舰VIP提速通道
MODEL_FAST      = "fast"                # Fast模式
MODEL_FAST_VIP  = "seedance2.0fast_vip" # FastVIP提速通道
# ──────────────────────────────────────────

ROOT = Path(__file__).parent

DIRS = {
    "角色":        ROOT / "素材" / "角色",
    "场景":        ROOT / "素材" / "场景",
    "提示词_角色": ROOT / "提示词" / "角色",
    "提示词_场景": ROOT / "提示词" / "场景",
    "提示词_视频": ROOT / "提示词" / "视频",
    "输出":        ROOT / "输出",
    "帧图像":      ROOT / "帧图像",
    "任务记录":    ROOT / "任务记录",
    "gate_results":ROOT / "gate_results",
}
for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

CONFIG_FILE      = ROOT / "project.json"
TIMELINE_FILE    = ROOT / "timeline_truth.json"
ASSET_TRUTH_FILE = ROOT / "asset_truth.json"


# ══════════════════════════════════════════
# 命名系统
# ══════════════════════════════════════════

def name_char_image(char_name, state):
    """角色-织命-立绘正常.png"""
    return f"角色-{char_name}-{state}.png"

def name_threeway(char_name):
    """角色-织命-三视图.png"""
    return f"角色-{char_name}-三视图.png"

def name_scene_image(location, time_of_day):
    """场景-村庄废墟-深夜.png"""
    return f"场景-{location}-{time_of_day}.png"

def name_seg_video(ep_num, seg_num, seg_name, draft=False):
    """
    正片：第01集01段-织命废墟觉醒.mp4
    草稿：草稿-第01集01段-织命废墟觉醒.mp4
    """
    desc = re.sub(r'[/\\:*?"<>|]', '', seg_name)[:20]
    base = f"第{ep_num:02d}集{seg_num:02d}段-{desc}.mp4"
    return f"草稿-{base}" if draft else base

def name_transition(ep_from, ep_to, scene_desc):
    """转场-EP01到EP02-针叶林入竹林-4s.mp4"""
    desc = re.sub(r'[/\\:*?"<>|]', '', scene_desc)[:15]
    return f"转场-EP{ep_from:02d}到EP{ep_to:02d}-{desc}-4s.mp4"

def seg_prompt_file(ep_id, seg_num):
    """提示词文件路径：提示词/视频/EP01_段01.txt"""
    return DIRS["提示词_视频"] / f"{ep_id}_段{seg_num:02d}.txt"


# ══════════════════════════════════════════
# 门禁检查
# ══════════════════════════════════════════

PROMPT_RULES = [
    ("R08", r"快速|迅速|飞速|高速",
     "动作含高速词，改为'慢动作'或'匀速缓慢'", True),
    ("R09", r"两人(?!.*相距)",
     "双角色未写距离，补'两人相距约X米，中间有明确空白距离'", True),
    ("R10", r'："[^"]{7,}"',
     "单段台词超6字，拆分到多个时间段", True),
    ("R11", r"手部特写|手指细节",
     "禁止手部特写", True),
    ("R14", r"叠化|溶解",
     "含溶解词，转场拼接必须用硬切", True),
    ("R15", r"\d+-\d+s：(?:(?!摆动|跳动|飘动|粒子|流动|晃动).){0,60}$",
     "时间段可能缺少动态元素", False),
]

def gate_prompt_check(prompt_text, label):
    issues, blockers = [], []
    for rule_id, pattern, msg, is_blocker in PROMPT_RULES:
        if re.search(pattern, prompt_text, re.MULTILINE):
            tag = "❌" if is_blocker else "⚠️"
            issues.append(f"{tag} [{rule_id}] {msg}")
            if is_blocker:
                blockers.append(rule_id)
    return {"label": label, "passed": not blockers,
            "issues": issues, "blockers": blockers}

def gate_timeline_check(ep_id, timeline):
    TIME_ORDER = ["深夜","夜间","凌晨","清晨","上午","白天","下午","黄昏","傍晚"]
    def rank(t):
        for i, tok in enumerate(TIME_ORDER):
            if tok in t: return i
        return -1

    keys = list(timeline.keys())
    if ep_id not in keys or keys.index(ep_id) == 0:
        return {"ep_id": ep_id, "passed": True, "issues": []}

    prev_id   = keys[keys.index(ep_id) - 1]
    prev_end  = timeline[prev_id].get("结尾时间", "")
    cur_start = timeline[ep_id].get("开场时间", "")
    issues    = []
    if rank(prev_end) != -1 and rank(cur_start) != -1 and rank(cur_start) < rank(prev_end):
        issues.append(f"❌ [R01] 时间倒退：{prev_id}结尾'{prev_end}' → {ep_id}开场'{cur_start}'")

    result = {"ep_id": ep_id, "passed": not issues, "issues": issues}
    gate_f = DIRS["gate_results"] / f"{ep_id}_gate.json"
    gate_f.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


# ══════════════════════════════════════════
# 工具
# ══════════════════════════════════════════

def load_json(path):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_config():
    if not CONFIG_FILE.exists():
        print("❌ 未找到 project.json，请先运行：python3 auto_submit.py init")
        sys.exit(1)
    return load_json(CONFIG_FILE)

DREAMINA_EXE = os.environ.get("DREAMINA_EXE", "dreamina")

def run_dreamina(cmd_args, record_key=None, dry_run=False):
    full = [DREAMINA_EXE] + [str(a) for a in cmd_args]
    print(f"\n{'[DRY-RUN] ' if dry_run else '▶ '}{' '.join(full)}")
    if dry_run:
        return "dry-run-id"

    r = subprocess.run(full, capture_output=True, text=True)
    out = r.stdout + r.stderr
    print(out[:400] if len(out) > 400 else out)

    submit_id = None
    try:
        d = json.loads(r.stdout)
        submit_id = d.get("submit_id") or d.get("data", {}).get("submit_id")
    except Exception:
        for line in out.splitlines():
            if "submit_id" in line.lower():
                parts = line.split(":")
                if len(parts) >= 2:
                    submit_id = parts[-1].strip().strip('"\'')
                    break

    if submit_id and record_key:
        f = DIRS["任务记录"] / f"{record_key}_submit_ids.txt"
        target_name = record_key if record_key.endswith(".mp4") else ""
        with open(f, "a", encoding="utf-8") as fp:
            fp.write(f"{datetime.now().isoformat()} | {submit_id} | {target_name}\n")
    return submit_id

def resolve_seg_images(config, ep_id, seg):
    """
    解析某一段需要的图片路径列表（有序）
    返回：[(路径, "@参考图N标签"), ...]
    顺序：角色图在前，场景图在后，与--images传参顺序一致
    prompt里用 @参考图1、@参考图2... 按此顺序引用
    """
    items = []
    for role_key in seg.get("角色", []):
        parts     = role_key.rsplit("_", 1)
        char_name = parts[0]
        state     = parts[1] if len(parts) > 1 else "立绘正常"
        filename  = name_char_image(char_name, state)
        items.append((DIRS["角色"] / filename, role_key))
    for scene_key in seg.get("场景", []):
        filename = config["场景"].get(scene_key, "")
        if filename:
            items.append((DIRS["场景"] / filename, scene_key))
    # 附上@参考图N编号
    labeled = [(path, key, f"@参考图{i+1}") for i, (path, key) in enumerate(items)]
    return labeled


def print_image_order(labeled_items):
    """打印素材顺序，帮助核对prompt里的@参考图N对应关系"""
    print("     素材顺序（对应prompt中@参考图N）：")
    for path, key, label in labeled_items:
        status = "✅" if path.exists() else "❌"
        print(f"       {label} → {key}  ({path.name}) {status}")


# ══════════════════════════════════════════
# 命令：初始化
# ══════════════════════════════════════════

def cmd_init():
    # project.json 模板（以段为最小单位）
    project = {
        "_说明": "段是最小生成单位，每集约6段×15s=90s。角色key格式：角色名_状态",
        "角色": {
            "织命": {
                "立绘正常": name_char_image("织命", "立绘正常"),
                "立绘受伤": name_char_image("织命", "立绘受伤"),
                "三视图":   name_threeway("织命")
            }
        },
        "场景": {
            "村庄废墟_深夜": name_scene_image("村庄废墟", "深夜"),
            "针叶林_深夜":   name_scene_image("针叶林", "深夜"),
            "竹林山道_夜间": name_scene_image("竹林山道", "夜间"),
            "竹林山道_清晨": name_scene_image("竹林山道", "清晨"),
        },
        "集数": {
            "EP01": {
                "集名": "觉醒",
                "上集": None,
                "下集": "EP02",
                "与下集同场景": False,
                "转场描述": "针叶林黑暗中织命背影消失过渡到竹林山道",
                "段": [
                    {"段号": 1, "段名": "俯瞰燃烧村庄",
                     "角色": [], "场景": ["村庄废墟_深夜"]},
                    {"段号": 2, "段名": "手伸出灰烬睁眼",
                     "角色": ["织命_立绘正常"], "场景": ["村庄废墟_深夜"]},
                    {"段号": 3, "段名": "坐起审视手背纹路",
                     "角色": ["织命_立绘正常"], "场景": ["村庄废墟_深夜"]},
                    {"段号": 4, "段名": "走向针叶林消失",
                     "角色": ["织命_立绘正常"], "场景": ["村庄废墟_深夜", "针叶林_深夜"]},
                ]
            },
            "EP02": {
                "集名": "第一猎",
                "上集": "EP01",
                "下集": None,
                "与下集同场景": False,
                "转场描述": "",
                "段": [
                    {"段号": 1, "段名": "舌鬼从树影探出",
                     "角色": [], "场景": ["竹林山道_夜间"]},
                    {"段号": 2, "段名": "织命现身冷漠对峙",
                     "角色": ["织命_立绘正常"], "场景": ["竹林山道_夜间"]},
                    {"段号": 3, "段名": "蛛丝缠绕消散清晨",
                     "角色": ["织命_立绘正常"], "场景": ["竹林山道_夜间", "竹林山道_清晨"]},
                ]
            }
        }
    }
    save_json(CONFIG_FILE, project)

    # timeline_truth.json
    timeline = {
        "EP01": {"开场时间": "深夜", "开场场景": "村庄废墟",
                 "结尾时间": "深夜", "结尾场景": "针叶林入口"},
        "EP02": {"开场时间": "夜间", "开场场景": "竹林山道",
                 "结尾时间": "清晨", "结尾场景": "竹林山道"},
    }
    save_json(TIMELINE_FILE, timeline)
    save_json(ASSET_TRUTH_FILE, {})

    for fname, content in [
        ("series_bible.md",  "# 系列圣经\n\n## 世界观\n[填写]\n\n## 主要角色\n"),
        ("book_rules.md",    "# 项目规则\n\n## 角色外形锚点\n- 织命：银白长发·红色竖瞳·黑色和服\n\n## 已使用镜头（防疲劳）\n"),
        ("current_focus.md", "# 当前焦点\n\n## 本章重点\n[填写]\n\n## 下一集方向\n[填写]\n"),
    ]:
        p = ROOT / fname
        if not p.exists():
            p.write_text(content, encoding="utf-8")

    print("✅ 项目初始化完成")
    print("   提示词文件命名规范：提示词/视频/EP01_段01.txt · EP01_段02.txt ...")
    print("   每集有几段就建几个提示词文件\n")


# ══════════════════════════════════════════
# 命令：预览命名
# ══════════════════════════════════════════

def cmd_name(ep_id=None):
    config = load_config()
    print("\n═══ 命名预览 ═══")

    print("\n【素材文件】")
    for char_name, char_data in config["角色"].items():
        for state, filename in char_data.items():
            print(f"  素材/角色/{filename}")
    for scene_key, filename in config["场景"].items():
        print(f"  素材/场景/{filename}")

    eps = {ep_id: config["集数"][ep_id]} if ep_id else config["集数"]

    print("\n【视频段文件】")
    for eid, ep_data in eps.items():
        ep_num = int(eid.replace("EP", ""))
        for seg in ep_data.get("段", []):
            seg_num  = seg["段号"]
            seg_name = seg["段名"]
            print(f"  输出/{name_seg_video(ep_num, seg_num, seg_name)}")
            print(f"  输出/{name_seg_video(ep_num, seg_num, seg_name, draft=True)}  ← 草稿")

    print("\n【转场文件】")
    for eid, ep_data in config["集数"].items():
        next_eid = ep_data.get("下集")
        if not next_eid or ep_data.get("与下集同场景", False):
            continue
        ep_num   = int(eid.replace("EP", ""))
        next_num = int(next_eid.replace("EP", ""))
        desc     = ep_data.get("转场描述", "")[:15]
        print(f"  输出/{name_transition(ep_num, next_num, desc)}")


# ══════════════════════════════════════════
# 命令：状态
# ══════════════════════════════════════════

def cmd_status():
    config   = load_config()
    timeline = load_json(TIMELINE_FILE)

    print("\n═══ 项目状态 ═══\n")

    print("【素材】")
    for char_name, char_data in config["角色"].items():
        for state, filename in char_data.items():
            p = DIRS["角色"] / filename
            print(f"  {'✅' if p.exists() else '❌'} {filename}")
    for scene_key, filename in config["场景"].items():
        p = DIRS["场景"] / filename
        print(f"  {'✅' if p.exists() else '❌'} {filename}")

    print("\n【视频段】")
    total_segs = 0
    done_segs  = 0
    for eid, ep_data in config["集数"].items():
        ep_num = int(eid.replace("EP", ""))
        segs   = ep_data.get("段", [])
        print(f"  {eid}（{ep_data.get('集名','')}）共{len(segs)}段 × 15s = {len(segs)*15}s")
        for seg in segs:
            seg_num  = seg["段号"]
            seg_name = seg["段名"]
            fname    = name_seg_video(ep_num, seg_num, seg_name)
            exists   = (DIRS["输出"] / fname).exists()
            pf_ok    = seg_prompt_file(eid, seg_num).exists()
            print(f"    {'✅' if exists else '❌'} {fname}  提示词:{'✅' if pf_ok else '❌'}")
            total_segs += 1
            done_segs  += int(exists)
    print(f"\n  进度：{done_segs}/{total_segs} 段已生成")

    print("\n【转场】")
    for eid, ep_data in config["集数"].items():
        next_eid = ep_data.get("下集")
        if not next_eid:
            continue
        if ep_data.get("与下集同场景", False):
            print(f"  ⏭  {eid}→{next_eid}：同场景，硬切")
            continue
        ep_num   = int(eid.replace("EP", ""))
        next_num = int(next_eid.replace("EP", ""))
        desc     = ep_data.get("转场描述", "")[:15]
        fname    = name_transition(ep_num, next_num, desc)
        p        = DIRS["输出"] / fname
        print(f"  {'✅' if p.exists() else '❌'} {fname}")


# ══════════════════════════════════════════
# 命令：生成角色立绘+场景图
# ══════════════════════════════════════════

def cmd_images(dry_run=False):
    config = load_config()

    print("\n═══ 角色立绘 ═══")
    for char_name, char_data in config["角色"].items():
        for state, filename in char_data.items():
            if "三视图" in state:
                continue
            pf  = DIRS["提示词_角色"] / f"{char_name}_{state}.txt"
            out = DIRS["角色"] / filename
            if out.exists():
                print(f"⏭  {filename}")
                continue
            if not pf.exists():
                print(f"⚠️  提示词不存在：{pf}")
                continue
            run_dreamina(["text2image",
                f"--prompt={pf.read_text(encoding='utf-8').strip()}",
                "--ratio=9:16", f"--resolution_type={RESOLUTION}", "--poll=60"],
                record_key="图片生成", dry_run=dry_run)
            time.sleep(1)

    print("\n═══ 场景图 ═══")
    for scene_key, filename in config["场景"].items():
        pf  = DIRS["提示词_场景"] / f"{scene_key}.txt"
        out = DIRS["场景"] / filename
        if out.exists():
            print(f"⏭  {filename}")
            continue
        if not pf.exists():
            print(f"⚠️  提示词不存在：{pf}")
            continue
        run_dreamina(["text2image",
            f"--prompt={pf.read_text(encoding='utf-8').strip()}",
            "--ratio=16:9", f"--resolution_type={RESOLUTION}", "--poll=60"],
            record_key="图片生成", dry_run=dry_run)
        time.sleep(1)


# ══════════════════════════════════════════
# 命令：生成三视图
# ══════════════════════════════════════════

def cmd_threeway(dry_run=False):
    config = load_config()
    print("\n═══ 三视图生成 ═══")
    for char_name, char_data in config["角色"].items():
        if "三视图" not in char_data:
            continue
        ref = DIRS["角色"] / char_data.get("立绘正常", "")
        out = DIRS["角色"] / char_data["三视图"]
        if out.exists():
            print(f"⏭  {char_data['三视图']}")
            continue
        if not ref.exists():
            print(f"⚠️  参考立绘不存在：{ref}")
            continue
        prompt = (
            "基于参考图生成角色设计稿，"
            "画面左侧三分之一区域：角色上半身脸部特写，突出面部细节；"
            "画面右侧三分之二区域：三个完整全身三视图横向排列——正视图·侧视图·后视图，"
            "确保发型和服饰与参考图完全一致，人物完整无遮挡，"
            "背景纯白色，整体无文字，清晰简洁，"
            "2D日漫动画风格，手绘赛璐璐质感，精细线稿，8K超高清"
        )
        run_dreamina(["image2image",
            f"--images={ref}", f"--prompt={prompt}",
            "--ratio=3:2", f"--resolution_type={RESOLUTION}", "--poll=60"],
            record_key="三视图", dry_run=dry_run)
        time.sleep(1)


# ══════════════════════════════════════════
# 命令：生成视频（按段提交）
# ══════════════════════════════════════════

def cmd_videos(draft=False, vip=False, ep_filter=None, dry_run=False):
    config   = load_config()
    timeline = load_json(TIMELINE_FILE)

    # 选择模型通道
    if draft and vip:
        model    = MODEL_FAST_VIP
        mode_tag = "草稿·FastVIP提速"
    elif draft:
        model    = MODEL_FAST
        mode_tag = "草稿·Fast"
    elif vip:
        model    = MODEL_VIP
        mode_tag = "正片·旗舰VIP提速"
    else:
        model    = MODEL_FLAGSHIP
        mode_tag = "正片·旗舰"

    print(f"\n═══ 视频生成（{mode_tag}·每段{SEG_DURATION}s） ═══")

    eps = ({ep_filter: config["集数"][ep_filter]}
           if ep_filter and ep_filter in config["集数"]
           else config["集数"])

    for eid, ep_data in eps.items():
        ep_num = int(eid.replace("EP", ""))
        segs   = ep_data.get("段", [])

        # 门禁3：时间线检查
        gate3 = gate_timeline_check(eid, timeline)
        if not gate3["passed"]:
            print(f"❌ {eid} 时间线门禁未通过，跳过整集：")
            for issue in gate3["issues"]:
                print(f"   {issue}")
            continue

        print(f"\n── {eid}（{ep_data.get('集名','')}）{len(segs)}段 ──")

        for seg in segs:
            seg_num  = seg["段号"]
            seg_name = seg["段名"]
            fname    = name_seg_video(ep_num, seg_num, seg_name, draft)
            out_path = DIRS["输出"] / fname
            pf       = seg_prompt_file(eid, seg_num)

            if out_path.exists():
                print(f"  ⏭  {fname}")
                continue
            if not pf.exists():
                print(f"  ⚠️  提示词不存在：{pf}，跳过")
                continue

            prompt_text = pf.read_text(encoding="utf-8").strip()

            # 门禁2：提示词扫描
            label = f"{eid}_段{seg_num:02d}"
            gate2 = gate_prompt_check(prompt_text, label)
            for issue in gate2["issues"]:
                print(f"  {issue}")
            if not gate2["passed"]:
                print(f"  ❌ {label} 提示词门禁未通过，跳过")
                continue

            # 解析素材路径（有序，@参考图N按此顺序对应）
            labeled = resolve_seg_images(config, eid, seg)
            missing = [path for path, key, lbl in labeled if not path.exists()]
            if missing:
                print(f"  ❌ 素材缺失：{[p.name for p in missing]}，跳过")
                continue

            print(f"\n  ▶ 段{seg_num:02d}-{seg_name} → {fname}")
            print_image_order(labeled)

            # --images 按顺序传入，空格分隔
            # prompt里 @参考图1=第1张, @参考图2=第2张, 以此类推
            img_paths = [str(path) for path, key, lbl in labeled]

            cmd_args = [
                "multimodal2video",
                "--images", *img_paths,
                f"--prompt={prompt_text}",
                f"--duration={SEG_DURATION}",
                f"--ratio={VIDEO_RATIO}",
                "--poll=180"
            ]
            if model:
                cmd_args.append(f"--model={model}")

            run_dreamina(cmd_args, record_key=fname, dry_run=dry_run)
            time.sleep(2)




# ══════════════════════════════════════════
# 命令：生成转场视频
# ══════════════════════════════════════════

def cmd_transitions(dry_run=False):
    config = load_config()
    print(f"\n═══ 转场视频（固定{TRANS_DURATION}s） ═══")

    for eid, ep_data in config["集数"].items():
        next_eid = ep_data.get("下集")
        if not next_eid:
            continue
        if ep_data.get("与下集同场景", False):
            print(f"⏭  {eid}→{next_eid}：同场景，硬切")
            continue

        ep_num   = int(eid.replace("EP", ""))
        next_num = int(next_eid.replace("EP", ""))
        desc     = ep_data.get("转场描述", f"{eid}到{next_eid}过渡")
        fname    = name_transition(ep_num, next_num, desc[:15])
        out_path = DIRS["输出"] / fname

        if out_path.exists():
            print(f"⏭  {fname}")
            continue

        last_frame  = DIRS["帧图像"] / f"{eid}_尾帧.png"
        first_frame = DIRS["帧图像"] / f"{next_eid}_首帧.png"
        missing     = [p for p in [last_frame, first_frame] if not p.exists()]
        if missing:
            print(f"❌ 帧图像缺失：{[p.name for p in missing]}")
            print(f"   运行：python3 jimeng_frames.py chapter ./输出/")
            continue

        pf     = DIRS["提示词_视频"] / f"转场_{eid}到{next_eid}.txt"
        prompt = pf.read_text(encoding="utf-8").strip() if pf.exists() else desc

        print(f"\n▶ 转场 {eid}→{next_eid} → {fname}")
        run_dreamina([
            "frames2video",
            f"--first_frame={last_frame}",
            f"--last_frame={first_frame}",
            f"--prompt={prompt}",
            f"--duration={TRANS_DURATION}",
            f"--ratio={VIDEO_RATIO}",
            "--poll=60"
        ], record_key="转场", dry_run=dry_run)
        time.sleep(1)


# ══════════════════════════════════════════
# 命令：ffmpeg拼接合集
# ══════════════════════════════════════════

def cmd_assemble():
    config   = load_config()
    out_list = []
    missing  = []

    for eid, ep_data in config["集数"].items():
        ep_num = int(eid.replace("EP", ""))
        segs   = ep_data.get("段", [])

        # 按段号顺序添加
        for seg in sorted(segs, key=lambda s: s["段号"]):
            fname = name_seg_video(ep_num, seg["段号"], seg["段名"])
            p     = DIRS["输出"] / fname
            if p.exists():
                out_list.append(str(p))
            else:
                missing.append(fname)
                print(f"⚠️  段缺失，跳过：{fname}")

        # 集后转场
        next_eid = ep_data.get("下集")
        if next_eid and not ep_data.get("与下集同场景", False):
            next_num = int(next_eid.replace("EP", ""))
            desc     = ep_data.get("转场描述", "")[:15]
            tfname   = name_transition(ep_num, next_num, desc)
            tp       = DIRS["输出"] / tfname
            if tp.exists():
                out_list.append(str(tp))
            else:
                print(f"⚠️  转场缺失，硬切：{tfname}")

    if len(out_list) < 2:
        print("❌ 可拼接片段不足")
        return

    filelist = DIRS["输出"] / "_合集列表.txt"
    filelist.write_text("\n".join(f"file '{p}'" for p in out_list), encoding="utf-8")

    out_file = DIRS["输出"] / "最终合集.mp4"
    subprocess.run([
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", str(filelist), "-c", "copy", str(out_file), "-y"
    ])
    total_secs = len([p for p in out_list if "转场" not in p]) * SEG_DURATION
    print(f"\n✅ 合集输出：{out_file}")
    print(f"   共 {len(out_list)} 个片段，视频段约 {total_secs}s")


# ══════════════════════════════════════════
# 命令：轮询下载
# ══════════════════════════════════════════

def cmd_poll():
    for rf in DIRS["任务记录"].glob("*_submit_ids.txt"):
        print(f"\n═══ {rf.name} ═══")
        for line in rf.read_text(encoding="utf-8").splitlines():
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            sid = parts[1] if len(parts) > 1 else ""
            target_name = parts[2] if len(parts) > 2 else ""
            if not sid:
                continue
            r = subprocess.run(
                ["dreamina", "query_result", f"--submit_id={sid}",
                 f"--download_dir={DIRS['输出']}"],
                capture_output=True, text=True
            )
            print(r.stdout[:200] if len(r.stdout) > 200 else r.stdout)
            # 自动改名：{submit_id}_video_1.mp4 → 目标文件名
            if target_name and target_name.endswith(".mp4"):
                raw = DIRS["输出"] / f"{sid}_video_1.mp4"
                dst = DIRS["输出"] / target_name
                if raw.exists() and not dst.exists():
                    raw.rename(dst)
                    print(f"  ✅ 已改名 → {target_name}")
            time.sleep(0.5)


# ══════════════════════════════════════════
# 命令：门禁检查
# ══════════════════════════════════════════

def cmd_check_prompt(ep_id, seg_num=None):
    if seg_num:
        pf = seg_prompt_file(ep_id, int(seg_num))
        if not pf.exists():
            print(f"❌ 提示词不存在：{pf}")
            return
        r = gate_prompt_check(pf.read_text(encoding="utf-8"), f"{ep_id}_段{int(seg_num):02d}")
        print(f"\n{'✅' if r['passed'] else '❌'} {r['label']} 提示词门禁")
        for i in r["issues"]:
            print(f"  {i}")
    else:
        # 检查整集所有段
        config = load_config()
        ep_data = config["集数"].get(ep_id, {})
        for seg in ep_data.get("段", []):
            pf = seg_prompt_file(ep_id, seg["段号"])
            if not pf.exists():
                print(f"  ⚠️  提示词不存在：{pf}")
                continue
            r = gate_prompt_check(pf.read_text(encoding="utf-8"),
                                  f"{ep_id}_段{seg['段号']:02d}")
            print(f"  {'✅' if r['passed'] else '❌'} {r['label']}")
            for i in r["issues"]:
                print(f"     {i}")


# ══════════════════════════════════════════
# 入口
# ══════════════════════════════════════════

if __name__ == "__main__":
    args    = sys.argv[1:]
    dry_run = "--dry-run" in args
    draft   = "--draft"   in args
    vip     = "--vip"     in args
    args    = [a for a in args if a not in ("--dry-run", "--draft", "--vip")]

    ep_arg  = next((args[i+1] for i, a in enumerate(args) if a == "--ep"  and i+1 < len(args)), None)
    seg_arg = next((args[i+1] for i, a in enumerate(args) if a == "--seg" and i+1 < len(args)), None)
    cmd     = args[0] if args else ""

    HELP = f"""
即梦漫剧自动化提交脚本 v3.0
每集≈1.5分钟 = 多段×{SEG_DURATION}s · 转场固定{TRANS_DURATION}s · AI自动命名

命令：
  init                              生成配置模板
  name [--ep EP01]                  预览命名结果（含@参考图N顺序）
  status                            查看项目状态
  images                            生成角色立绘+场景图
  threeway                          生成三视图
  videos [模型选项] [--ep EP01]     生成视频段
  transitions                       生成转场视频（固定{TRANS_DURATION}s）
  assemble                          ffmpeg拼接合集
  poll                              轮询下载
  check-prompt --ep EP01 [--seg 1]  提示词门禁检查

模型选项（videos命令）：
  （默认）         旗舰版 Seedance 2.0
  --vip            旗舰VIP提速通道 seedance2.0_vip
  --draft          Fast省积分 fast
  --draft --vip    FastVIP提速 seedance2.0fast_vip

素材顺序说明：
  --images 按 [角色图...] [场景图...] 顺序传入
  prompt里用 @参考图1、@参考图2... 按此顺序引用

提示词文件命名：提示词/视频/EP01_段01.txt · EP01_段02.txt ...
"""

    if   cmd == "init":           cmd_init()
    elif cmd == "name":           cmd_name(ep_arg)
    elif cmd == "status":         cmd_status()
    elif cmd == "images":         cmd_images(dry_run)
    elif cmd == "threeway":       cmd_threeway(dry_run)
    elif cmd == "videos":         cmd_videos(draft, vip, ep_arg, dry_run)
    elif cmd == "transitions":    cmd_transitions(dry_run)
    elif cmd == "assemble":       cmd_assemble()
    elif cmd == "poll":           cmd_poll()
    elif cmd == "check-prompt":   cmd_check_prompt(ep_arg or "EP01", seg_arg)
    else:                         print(HELP)
