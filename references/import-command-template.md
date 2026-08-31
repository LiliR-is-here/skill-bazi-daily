# Import Command Template

如果你手上有新的 xlsx，先在 skill 根目录生成 SQL：

```bash
python scripts/import_bazi_calendar.py \
  --input /path/to/bazi_daily_calendar_2026.xlsx \
  --output assets/bazi_daily_calendar_2026.sql \
  --table bazi_daily_calendar
```

如果不需要重生，直接使用包内已有文件：

`assets/bazi_daily_calendar_2026.sql`

## 数据接入方式

当前运行环境不保证提供可执行 SQL 的数据库。按以下顺序接入当日流运数据：

1. **优先**：若运行环境提供日历数据查询能力（记忆服务 / 数据表等），按 `references/bazi-calendar-schema.md` 的 Query Contract 查询（`WHERE date = today_local`）。
2. **本地回退**：直接读取 `assets/bazi_daily_calendar_2026.sql`，按 `date = today_local` 定位对应行的 `flow_year/flow_month/flow_day`（用 grep 或脚本匹配），未命中走“缺少当日流运数据”分支。
3. **SQLite 验数（可选）**：若本机装有 sqlite3，可本地验数与抽样抽查：

```bash
sqlite3 /tmp/bazi_calendar.db < assets/bazi_daily_calendar_2026.sql
sqlite3 /tmp/bazi_calendar.db \
  "SELECT COUNT(*) FROM bazi_daily_calendar; \
   SELECT MIN(date), MAX(date) FROM bazi_daily_calendar;"
```

## 上线后抽样校验

```sql
SELECT date, flow_year, flow_month, flow_day
FROM bazi_daily_calendar
WHERE date IN ('2026-03-03', '2026-06-01', '2026-12-31');
```
