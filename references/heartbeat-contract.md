# Heartbeat Contract For Bazi Profile

本文件定义 `bazi-daily` Skill 与 OpenClaw heartbeat 的读写契约。

## Events

- `bazi_profile_get`
- `bazi_profile_upsert`

## Scope And Idempotency

- scope：`user`
- 主键：`user_id`
- upsert 语义：同一 `user_id` 重复写入覆盖旧值。

## bazi_profile_get

请求：

```json
{
  "event": "bazi_profile_get",
  "scope": "user",
  "user_id": "u_123"
}
```

成功响应（命中）：

```json
{
  "ok": true,
  "data": {
    "pillars": {
      "year": "甲子",
      "month": "丙寅",
      "day": "辛亥",
      "hour": "壬辰"
    },
    "source": "user_provided",
    "updated_at": "2026-03-03T03:00:00Z"
  }
}
```

成功响应（未命中）：

```json
{
  "ok": true,
  "data": {}
}
```

## bazi_profile_upsert

请求：

```json
{
  "event": "bazi_profile_upsert",
  "scope": "user",
  "user_id": "u_123",
  "payload": {
    "pillars": {
      "year": "甲子",
      "month": "丙寅",
      "day": "辛亥",
      "hour": "壬辰"
    },
    "source": "user_provided",
    "updated_at": "2026-03-03T03:00:00Z"
  }
}
```

成功响应：

```json
{
  "ok": true
}
```

## Error Codes

- `HB_TIMEOUT`：heartbeat 服务超时（瞬时错误，可重试一次）
- `HB_UNAVAILABLE`：heartbeat 服务不可用（瞬时错误，可重试一次）
- `HB_INVALID_PAYLOAD`：入参不合法（非瞬时错误，不重试）
- `HB_UNAUTHORIZED`：无权限（非瞬时错误，不重试）

## Retry Rule

- 仅对瞬时错误重试一次：`HB_TIMEOUT`、`HB_UNAVAILABLE`
- 重试仍失败时：
  - get：进入首次引导并提示“记忆服务暂不可用，本次可先临时分析”
  - upsert：继续本次分析并提示“本次已解读，但暂未保存”

## Validation Rule

写入前必须依次校验：

1. **完整性**：`year/month/day/hour` 四项都存在且非空。
2. **六十甲子匹配**：每柱必须命中下方六十甲子表（天干地支序号同奇偶：阳干配阳支、阴干配阴支）。仅校验“第 1 字为天干 + 第 2 字为地支”而不核对组合（如 `甲丑` 这类非六十甲子组合）视为非法。不满足时返回 `HB_INVALID_PAYLOAD`，不得写入。

```text
甲子 乙丑 丙寅 丁卯 戊辰 己巳 庚午 辛未 壬申 癸酉
甲戌 乙亥 丙子 丁丑 戊寅 己卯 庚辰 辛巳 壬午 癸未
甲申 乙酉 丙戌 丁亥 戊子 己丑 庚寅 辛卯 壬辰 癸巳
甲午 乙未 丙申 丁酉 戊戌 己亥 庚子 辛丑 壬寅 癸卯
甲辰 乙巳 丙午 丁未 戊申 己酉 庚戌 辛亥 壬子 癸丑
甲寅 乙卯 丙辰 丁巳 戊午 己未 庚申 辛酉 壬戌 癸亥
```

- 合法示例：`甲子`、`丙寅`、`戊辰`、`辛亥`、`壬辰`、`乙巳`。
- 非法示例（应拒绝）：`甲丑`（阳干配阴支）、`乙子`、`丙亥`、`丁戌`、`戊酉`、`己申`、`庚未`、`辛午`、`壬巳`、`癸辰`。

实现建议：将上表预置为合法组合集合，按“干支二字 ∈ 集合”校验；或按“天干序号与地支序号同奇偶”规则校验后再与上表核对。

## Timestamp Convention

- `updated_at` 字段**必须使用 UTC 时间**，格式为带 `Z` 后缀的 ISO 8601：`YYYY-MM-DDTHH:mm:ssZ`。
- 示例：`"2026-03-03T03:00:00Z"`（即北京时间 11:00 对应的 UTC）。
- 禁止写入带本地时区偏移（如 `+08:00`）的时间戳，以避免跨用户存储语义不一致。
