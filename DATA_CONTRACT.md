# 数据契约

`public-data/v1/manifest.json` 是入口，声明 schema、data version、最新日终 slot、采集覆盖率和状态；`registry/` 提供校区、楼栋和房间索引；`latest/buildings/{building-id}.json` 提供楼栋房间的今日剩余电量快照；`intraday/` 保存按北京时间 23:00 采集的历史日终余额点，`daily/` 保存由相邻日终余额下降差分得到的历史用电量。所有公开 ID 都是基于规范化名称的 UUIDv5，不暴露学校内部设备或账户 ID。

余额字段始终使用 `balance_value` 与 `balance_unit`，真实单位未确认时前端显示“当前余额”。估算耗电只在时间连续、单位一致且余额下降时计算；充值疑似、缺口、缺失、异常跳变均保留质量标签并产生 null 估算。
