# 数据字典（起步版）

CSV 使用带 BOM 的 UTF-8，便于在 Excel 中阅读。固定编号是关联依据，不能随排序或更名改变。空白不等于否定。

## films

`id` 为固定影片编号；`title` 初始为原表完整片名；`year` 初始为原表年份文本，暂不认定年份类型。`company_text`、`director_text`、`writer_text`、`cinematography_text`、`art_text`、`cast_text`、`other_text`、`notes` 分别承接原表出品公司、编导／导演、编剧、摄影、美工、主演、其他主创和备注。它们是可修订的当前展示值，原始值保存在来源快照中。

`status` 为整体条目核对状态，不代表每个字段已单独建立证据。`source_id` 连接来源，`source_row` 是 Excel 原行号，`source_page` 是需补充的文献页码。

`assistant_notes` 为后续检查补充的疑点与说明，网页显示为“补充备注 · 待确认”。与原表 `notes` 分开，不能将推测直接写成修订后的史实。当前版本获用户确认不自动等同于每个字段已据原书独立核实。

## people / companies

`id` 为固定候选编号，`name` 为名称，`status` 为核对状态，`notes` 记录消歧限制或说明。相同字面名称暂归在同一候选，不能视为已确认同一实体。不同名称暂不合并。

## relations

`from_id` 是起点（人物或机构），`to_id` 是终点（当前为影片），`type` 是关系类型；`character` 预留演员所饰角色，初始为空。`source_id`、`source_row`、`source_column`、`source_page` 追踪这条关系的具体出处。`status` 独立于影片与候选条目的状态。

当前关系类型为“出品（原表）”“编导／导演（原表）”“编剧（原表）”“摄影（原表）”“美工（原表）”。改为明确职务前需核对来源。

## sources

`id` 为来源编号，`filename`、`sheet` 为来源文件位置，`sha256` 为原文件校验值，`bibliography`、`edition` 为待填书目与版本，`notes` 为来源限制。新增外部文献需独立编号，不能借用原文件来源编号。

## review_queue

`film_id` 为相关影片，`field` 为字段，`reason` 为核对原因，`original_value` 为发现问题时的内容。`status` 为事项状态，`resolution` 写核对依据及处理说明，`source_id`、`source_row` 指向原表位置。处理后保留事项及说明，不直接删除核对记录。

## 状态

- 待核对：尚未完成核实，不代表错误。
- 已核对：维护者根据注明的依据完成当前事项、条目或关系核实。
- 有争议：存在冲突或身份、含义仍有分歧，应保留各方依据。

状态不会在表之间自动传播。下一阶段加入逐字段、多来源证据结构，避免用一条整体状态代替各字段的证据。
