---
name: bazi-daily
version: 2.2.0
description: 面向“今日运势/今天适合做X吗/今日宜忌”类咨询的八字日运解读技能。使用场景：用户询问当日运势、某事项是否适合今天做、今日吉凶与建议时触发。技能会自动读取当前日期，查询当日对应的流年、流月、流日，并结合用户的八字四柱进行分析；若用户为首次使用且无个人四柱记忆，先引导用户提供四柱并写入长期记忆，后续复用无需重复询问。
---

# Bazi Daily

## Version & Changelog

- **v2.2.0**（2026-08-31）
  - B《渊海子平》、C《穷通宝鉴》由节选版升级为**完整版**（B：通行七卷本 304 章约 25 万字；C：通行六卷本、十天干分月喜忌与命例齐全），补齐历史“格局论核心章节缺失”与“调候章节缺失”两大缺口。
  - 新增经典文本检索脚本 `scripts/query_classics.py`（关键词定位章节 + 按章精读），并规定 B/C 大文件必须先检索后精读、禁止整篇读入上下文。
  - `references/classics/README.md` 重写：覆盖状态更新为“已补全”，新增“检索方式（Retrieval Guide）”章节。
- **v2.1.0**（2026-08-31）
  - 清理 OpenClaw 工程残留：移除 `agents/`（OpenClaw agent 配置）与 `references/heartbeat-contract.md`。
  - 档案读写改为通用记忆契约 `references/bazi-profile-contract.md`（记忆服务优先，本地 `MEMORY.md` 回退），不再绑定 heartbeat。
  - 日历数据接入路径去 OpenClaw 化：删除 `<OPENCLAW_DB_EXEC>` / “OpenClaw 内置表” / `openclaw.db` 表述，补充本地查询方式。
  - 强制日志字段 `heartbeat_get_status` / `heartbeat_upsert_status` 更名为 `memory_get_status` / `memory_upsert_status`。
- **v2.0.0**（2026-08-31）
  - 新增 `output_style` 输出风格开关（`structured` / `narrative`），支持“结论先行 + 叙事取象”。
  - 新增 Flow Luck Consumption（强制）：闭合 `flow_year/flow_month/flow_day` 的消费链路，不再“只查不用”。
  - 四柱校验规则单点化至契约文档 `references/bazi-profile-contract.md`，升级为“六十甲子表匹配”，拒绝 `甲丑` 类非法组合。
  - 新增“涉及缺失”判定规则与缺失章节清单（见 `references/classics/README.md`），未命中清单不再全量警告。
  - 强制日志字段新增落地位置 `logs/bazi_daily_YYYY-MM-DD.json`。
- **v1.0.0**（2026-03-03）：初始版本。

## Knowledge Source Architecture (Mandatory)

将经典分为三个独立知识源，禁止混成单一“综合库”：

- A.《滴天髓》库（原则层）：用于“为什么”和方向性判断（气机、取用总纲、论命哲学）。
- B.《渊海子平》库（结构层）：用于格局判定、十神结构、用神框架（先定结构再谈细节）。
- C.《穷通宝鉴》库（调候层）：用于月令气候、寒暖燥湿与调候药方（对结构结论做气候校正）。

固定来源文件（仅使用本地 txt）：
- `A.滴天髓`：`references/classics/A_滴天髓.txt`（节选）
- `B.渊海子平`：`references/classics/B_渊海子平.txt`（完整版：通行七卷本 304 章，约 25 万字）
- `C.穷通宝鉴`：`references/classics/C_穷通宝鉴.txt`（完整版：通行六卷本，十天干分月喜忌与命例齐全，约 3.3 万字）

若 txt 文件不可读，直接报错"经典文本文件缺失，无法完成分析"，不得尝试其他路径。

> **经典文本覆盖状态（v2.2.0 已补全）**：B/C 已由节选版升级为完整版，历史“格局论核心章节缺失”“调候章节缺失”缺口已全部补齐，不再存在“涉及缺失”回退。仅 `A_滴天髓.txt` 为节选（暂无已知缺口）。

调用顺序必须是：`B 结构 -> C 调候 -> A 解释`。
路由细则见 [references/classic-sources-routing.md](references/classic-sources-routing.md)。

## Classic Text Retrieval (Mandatory)

B 完整版约 25 万字、C 约 3.3 万字，**禁止整篇读入上下文**。Step2/3/4 引用经典原文前，必须先用检索定位章节，再按需精读：

1. 用检索脚本定位（先 `--section-only` 看命中章节，再决定是否精读）：
   - B 结构检索：`python3 scripts/query_classics.py --book B --kw <格局/十神/用神关键词>`
   - C 调候检索：`python3 scripts/query_classics.py --book C --kw <日主天干> --kw <月份>`
   - A 原理检索：`python3 scripts/query_classics.py --book A --kw <气机关键词>`
2. 需要完整条文时按章提取：`python3 scripts/query_classics.py --book B --chapter <章名>`
   （章名可通过 `--list` 或 `--section-only` 获取；C 书月份章节名如 `正月丙火`、`十一月癸水`）
3. 脚本不可用时回退 `grep -n` 定位行号再 `sed` 精读。
4. 引用原文须带出处（书 + 卷章 + 行号），便于溯源。

检索脚本完整用法与规则见 [references/classics/README.md](references/classics/README.md)。

## Workflow

1. 识别触发意图。
2. 确定用户时区：优先取会话上下文提供的时区；缺失时回退 `Asia/Shanghai` 并记录 `timezone_fallback=true`。
3. 以用户时区自动计算 `today_local`（`YYYY-MM-DD`）。
4. 读取用户四柱档案：优先调记忆服务读取；记忆服务不可用或未命中时，回退本地 `MEMORY.md` 档案。
5. 若未命中四柱档案，请用户补充四柱并按 `references/bazi-profile-contract.md` 的校验规则写入记忆。
6. 根据 `today_local` 查询当日流运数据（查询方式见 `references/bazi-calendar-schema.md` 与 `references/import-command-template.md`）。
7. 按“五步编排”完成分析并输出结论、依据和建议。

默认年度数据源文件：`assets/bazi_daily_calendar_2026.sql`。
导入脚本：`scripts/import_bazi_calendar.py`。
经典文本检索脚本：`scripts/query_classics.py`（Step2/3/4 引用经典原文前使用，见 “Classic Text Retrieval”）。
经典文本预处理脚本：`scripts/extract_classics_text.py`（历史用，B/C 完整版已内置，一般不再执行）。

## Five-Step Orchestration (Mandatory)

在通过日期与流运查询闸门后，必须按以下步骤执行：

1. `step1 解析命盘`
   - 提取四柱、十神分布、日主强弱初判、月令、格局候选（可多候选）。
2. `step2 结构优先（渊海子平）`
   - 先用检索脚本在 B 库定位格局/十神条文（`--book B --kw <关键词>`），再按需精读，判结构与格局成立条件，给出主格/兼格与用神框架。
3. `step3 调候校正（穷通宝鉴）`
   - 先用检索脚本在 C 库按「日主天干 + 流月/命局月令」定位分月调候条文（如 `--book C --kw 丙火 --kw 正月`），再对寒暖燥湿做修正，必要时覆盖或微调 step2 的用神次序。
4. `step4 气机解释（滴天髓）`
   - 用 A 库解释最终结论背后的气机逻辑，使结论成体系、可说明。
5. `step5 输出`
   - 输出“结论 + 依据 + 建议”，并标明依据来自 A/B/C 哪一类规则；其中“当日流运影响”必须体现 Flow Luck Consumption 的消费结果（见下）。

## Flow Luck Consumption (Mandatory)

查询到的 `flow_year` / `flow_month` / `flow_day` **必须实际参与分析**，禁止“只查不用”：

1. `flow_day`（流日）：以“日主 × 流日干支”推算十神关系，判定当日主题倾向；若流日与命盘日柱同柱为“伏吟”、相冲为“反吟”，须显式提示。
2. `flow_month`（流月）：作为调候步骤的月令气候补充输入，纳入 step3 的 C 库校正（流月与命局月令的寒暖燥湿叠加判断）。
3. `flow_year`（流年）：从岁运视角评估对用神/忌神的生扶或制克方向，影响“宜/忌”建议的力度。

上述影响必须体现在输出“当日流运影响”段（见 Response Template），不得只列干支不出结论。

## Mandatory Pre-Analysis Gates

每次输出运势分析前，必须先完成以下两个步骤：
1. 获取当前日期：基于 `user_timezone` 计算 `today_local`（`YYYY-MM-DD`）。
2. 查询数据表：使用 `today_local` 查询 `bazi_daily_calendar` 以获取 `flow_year`、`flow_month`、`flow_day`。

未完成以上两个步骤时，禁止进入“运势结论/宜忌建议”输出。

## Trigger Phrases

将下列表达视为高优先级触发：
- “今日运势”
- “今天适合 xxx 吗？”
- “今天宜做什么/忌做什么？”
- “我今天的运气怎么样？”
- “帮我看今天的八字运势”

若用户没有显式说“八字”，但语义是“今天是否适合某事”，默认按本技能流程处理。

## First-Time Onboarding

当找不到用户四柱记忆时：
1. 明确告知需要四柱后才能进行个性化日运分析。
2. 请用户直接提供四柱，格式优先：`年柱/月柱/日柱/时柱`。
3. 若用户不清楚四柱，建议前往“万年历”查询：<https://wannianrili.bmcx.com/>，输入生日后获取四柱再回传。
4. 校验四柱完整性与格式：按 [references/bazi-profile-contract.md](references/bazi-profile-contract.md) 的 Validation Rule 执行（完整性 + 六十甲子表匹配）；格式不合法时要求用户重新输入，不得写入。
5. 按 [references/bazi-profile-contract.md](references/bazi-profile-contract.md) 将结构化结果写入长期记忆（记忆服务不可用时写入本地 `MEMORY.md`）。
6. 写入成功后继续本次分析，不要求用户重新提问。

长期记忆建议键：
- `bazi_profile.pillars.year`
- `bazi_profile.pillars.month`
- `bazi_profile.pillars.day`
- `bazi_profile.pillars.hour`
- `bazi_profile.source`（如 `user_provided`）
- `bazi_profile.updated_at`（UTC 时间，格式 `YYYY-MM-DDTHH:mm:ssZ`）

若用户后续主动更正四柱，以最新输入覆盖旧值。

档案结构与读写适配见 [references/bazi-profile-contract.md](references/bazi-profile-contract.md)。

## Date And Lookup Rules

1. 自动读取当前日期，禁止要求用户手动输入日期。
2. 优先使用会话上下文中的 `user_timezone` 计算当日日期。
3. 若 `user_timezone` 缺失，回退 `Asia/Shanghai` 并记录 `timezone_fallback=true`。
4. 查询数据表时使用标准日期键（`YYYY-MM-DD`），即 `today_local`。
5. 期望查得字段：`flow_year`、`flow_month`、`flow_day`。
6. 若当天无记录，明确告知“缺少当日流运数据”，并仅给出有限建议，不伪造结果。
7. 每次运势分析请求都必须执行一次日期计算与一次数据表查询，不得跳过。

8. 当前内置日历数据为 `assets/bazi_daily_calendar_2026.sql`，从 `2026-03-03` 起覆盖至 2026 年末。年度结束或数据缺口期间，除”缺少当日流运数据”提示外，额外提示”请联系管理员更新年度日历数据”。
9. 年度日历更新流程：准备新年度 xlsx → 运行 `scripts/import_bazi_calendar.py` 生成 SQL → 按 `references/import-command-template.md` 的数据接入方式使用（详见该文件）。新数据应至少在年度切换前 30 天就绪。

数据表字段约定见 [references/bazi-calendar-schema.md](references/bazi-calendar-schema.md)。
数据文件导入规范见 [references/bazi-calendar-schema.md](references/bazi-calendar-schema.md) 中的 “Data Source File” 与 “Import Mapping”。
导入命令模板见 [references/import-command-template.md](references/import-command-template.md)。

## Analysis Rules

1. 结构判定优先级高于主观经验；先判“是否成格/破格”，再谈强弱喜忌。
2. 调候可修正结构结论，但不可跳过结构直接给药方。
3. 解释层必须回扣气机，不得只给“吉/凶”标签。
4. 明确区分三类依据：
- 结构依据（B《渊海子平》）
- 调候依据（C《穷通宝鉴》）
- 原理依据（A《滴天髓》）
5. 先给“今日总体倾向”，再回答用户具体问题，再给“宜/忌”。
6. 输出“宜”与“忌”各 2-4 条，保持可执行。
7. 避免绝对化、宿命化表达；用“倾向/建议”措辞。

## Evidence Tagging Rules

每条关键结论至少绑定一个来源标签：

- `[B-结构]`：格局、十神结构、用神框架判断。
- `[C-调候]`：寒暖燥湿、月令气候修正。
- `[A-原理]`：气机方向、总纲解释。

若三源结论冲突，按优先级处理并显式说明：
1. 先保留 `B` 的结构边界；
2. 再用 `C` 做季节性校正；
3. 最后用 `A` 解释“为何这样取舍”。

## Failure Handling

1. 档案读取失败（记忆服务不可用）时，按“未知档案”处理并进入首次引导；同时提示“记忆服务暂不可用，本次可先临时分析”。
   若用户不清楚四柱，补充推荐“万年历”：<https://wannianrili.bmcx.com/>。
2. 档案写入失败时，继续使用用户本次输入完成分析；同时提示“本次已解读，但暂未保存，下次可能需要再次提供”。
3. 当日流运缺失时，明确告知“缺少当日流运数据，仅基于四柱给出有限建议”；该提示必须建立在“已执行当日查询且未命中”之上。

## Output Style

通过会话配置 `output_style` 控制输出顺序（默认 `structured`）：

- `structured`（默认）：严格按下方 Response Template 十段式顺序输出。
- `narrative`：结论先行 + 叙事/取象风格——先给“今日总体倾向”与“宜/忌”直接结论，再用叙事语言解释命盘与流运（保留 `[B-结构]/[C-调候]/[A-原理]` 证据标签），最后给一句风险提示。

未配置时按 `structured` 执行；用户明确表达偏好（如“结论先行”“讲人话”“说重点”）时以 `narrative` 执行。

## Response Template

（`output_style=structured` 时）按以下顺序组织回答：
1. 今日日期（`YYYY-MM-DD`）
2. 当日流运（流年/流月/流日）
3. 命盘摘要（十神/强弱初判/月令/格局候选）
4. 结构结论（`[B-结构]`）
5. 调候校正（`[C-调候]`）
6. 气机解释（`[A-原理]`）
7. 对用户提问的直接结论
8. 今日“宜”列表（2-4 条）
9. 今日“忌”列表（2-4 条）
10. 一句风险提示（非决定性，仅供参考）

## Guardrails

- 不编造缺失的四柱与流运数据。
- 不编造经典原文；如记忆不确定，改用“原则性转述”并标注“意译”。
- 不输出医疗、法律、投资等确定性结论。
- 用户未提供时柱时，不自动推断；要求补全。
- 禁止跳过 `B->C->A` 顺序直接下结论。

## Mandatory Logging Fields

每次请求**必须**记录以下字段，用于排障与 UAT 复盘：
- `user_id`
- `user_timezone`
- `today_local`
- `timezone_fallback`
- `memory_hit`
- `calendar_hit`
- `memory_get_status`
- `memory_upsert_status`
- `structure_source_hit`（B）
- `climate_source_hit`（C）
- `principle_source_hit`（A）
- `final_yongshen_framework`
- `climate_adjustment_applied`

上述字段不得省略；若某字段在当次请求中不适用（如首次引导无 `memory_upsert_status`），记录为 `null`。

**落地位置（强制）**：每次请求写入 `logs/bazi_daily_YYYY-MM-DD.json`（按 UTC 日期分文件），单条记录为一个 JSON 对象，字段与上述一致；运行环境无文件系统时降级为会话内日志并注明 `logging_fallback=true`。

## UAT Cases

1. 首次用户输入“今日运势”，期望：要求四柱 -> 档案写入成功 -> 返回完整解读。
2. 同一用户再次输入“今天适合谈合作吗？”，期望：不再询问四柱，直接返回结论与宜忌。
3. 用户时区为 `Asia/Shanghai`，在 00:05 与 23:55 测试，期望：`today_local` 与用户本地日期一致。
4. 构造当日无流运记录，期望：输出缺失提示，不编造流年流月流日。
5. 模拟档案写入失败，期望：本次照常解读，附“未保存”提示。
6. 模拟档案读取失败，期望：进入首次引导，流程不断。
7. 构造“结构与调候结论不一致”案例，期望：输出中明确展示 `B->C->A` 取舍链路。
8. 检查回答文本，期望：关键结论至少各含一个 `[B-结构]/[C-调候]/[A-原理]` 标签。
9. 构造需引用经典原文的分析（如判正官格、查某月调候），期望：先调用 `scripts/query_classics.py` 定位（`--section-only`）并只精读相关章节，引用带出处（书+卷章+行号）；不得整篇读入 B/C 大文件。
