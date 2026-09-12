-- ============================================================
-- investment_kb: 投资知识库看板派生数据层
-- 架构原则: 本地 vault 为绝对基准（第一/首要/绝对），本库仅为
--           阅读 + 加工总结的派生数据；一切冲突以 vault 为准。
-- 字符集: utf8mb4 / utf8mb4_unicode_ci
-- 约定: ① 枚举字段一律存码值，逻辑关联统一 dict 码值表（type+code）；主键自增；
--       ② **业务逻辑关联一律不设外键**（dict 码值、言论↔实体 post_entity_rel、言论↔言论 post_rel、
--          验证留痕 post_verify_sub、复核建议 post_review_sub 全由应用层维护）——弃用表改名后残留外键曾把
--          写入卡死（prediction_verifications → post_verify_sub 事件）。**例外**：refine_target_sub/review_check_sub
--          及 _del 留档表保留建表期继承的物理外键（纯记录用，不参与业务写入）。
--       ③ 每表每字段均带 COMMENT；
--       ④ **一条帖子只落一张表**：post_trade/post_predict/post_research/post_view/post_insight/post_chat
--          六张之一（唯一例外 post_history 原文表），不得落在第二张表；博主/个股/行业/市场四维度全靠 post_entity_rel；
--       ⑤ **命名**：帖子一律用 post，不用 stmt/statement；子表 _sub 后缀、关联表 _rel 后缀；
--       ⑥ **可枚举的值表进 dict**（标签、方向、状态等一律 dict，字段注释里写 dict.type 名）；
--       ⑦ **注释写法**：表注释只写「XX表 / XX子表」，字段注释平实直述，不带括号补充说明。
--
-- 变更日志（只记与当前结构有关的口径；历史改名过程见仓库 git 记录）:
--   2026-09-12 终版结构（用户拍板）:
--     ① 分层命名：**采集层叫「帖子」→ post_*；提炼后叫「言论」→ statement_***
--        —— 六张言论表 statement_trade/predict/research/view/insight/chat + 只读 UNION 视图 `statements`
--        + 序列 statement_id_seq + 子表 statement_verify_sub/statement_review_sub（_sub）＋关联表 _rel；
--        `post_history` 属帖子层，表名与列名（posted_at/platform_post_id）保持 post_ 前缀不变；
--        **post_history 只存帖子必要信息**（2026-09-12 用户拍板）：它是采集落点 + 提炼前原文，
--        不存提炼产物（原来的 content_type/stance/signal_text/entities_json/post_id/refined_at 六列已删，
--        「这帖提炼了吗」用 statements.source_url 反查）。
--     ② 实体三表取代 prediction_subjects：`stocks`（个股：name/code/market_code/aliases/hk_connect）、
--        `industries`（行业）、`markets`（市场：A股/港股/美股/韩股…）；宏观/认知/策略类概念不是实体。
--     ③ 关联六表（全部 _rel）：statement_blogger_rel（言论必挂博主）/ statement_stock_rel /
--        statement_industry_rel / statement_market_rel / stock_industry_rel（个股必挂行业，可多行业）/
--        stock_market_rel；原多态表已删除。
--     ④ 一条帖子只落一张言论表（优先级命中即止），正文完整保留帖子含义；买卖记录**不含操作字段**。
--     ⑤ 回指方向（2026-09-12 用户纠正）：**六张言论表 → post_history**（各表带 `post_history_id`），
--        不由 post_history 指出去；`post_history` 只存帖子必要信息，且**只保留 30 天**（滚动窗口，
--        `scripts/purge-post-history.js` 清理；言论行的 post_history_id 允许悬空）。
--     ⑤ 弃用对象一律**删前备份、然后 DROP**，不留 _del 残表；派生索引（vault 文件/标签）不落库，内存扫描。
--     ⑥ 表注释只写「XX表/XX子表」，字段注释平实直述，码值字段标注 `dict.type`。
-- ============================================================
CREATE DATABASE IF NOT EXISTS investment_kb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE investment_kb;

-- ============ 一、码值表（统一字典） ============
CREATE TABLE dict (
  `type` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '字典类型',
  `code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '码值',
  `name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '显示名',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序',
  `enabled` tinyint NOT NULL DEFAULT '1' COMMENT '是否启用',
  `remark` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`type`,`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字典表';

-- dict 内容快照（125 行；type 分组）
INSERT INTO dict (type, code, name, sort_order, enabled, remark) VALUES
  ('ambiguous_word', '小米', '小米', 0, 1, '与常用词同形的个股别名：命中后须过上下文判定'),
  ('ambiguous_word', '美的', '美的', 0, 1, '与常用词同形的个股别名：命中后须过上下文判定'),
  ('category', 'analysis_framework', '分析框架', 1, 1, '方法论/思维框架类条目'),
  ('category', 'trading_system', '交易体系', 2, 1, '交易规则/体系类条目'),
  ('category', 'investment_mentality', '投资心态', 3, 1, '心态/心理类条目'),
  ('category', 'investment_insight', '投资心得', 4, 1, '心得/复盘类条目'),
  ('category', 'stock', '个股', 5, 1, '个股分析条目'),
  ('category', 'industry', '行业', 6, 1, '行业研究条目'),
  ('category', 'macro', '宏观', 7, 1, '宏观分析条目'),
  ('check_status', 'pass', '通过', 1, 1, '检查通过'),
  ('check_status', 'ok', '通过(旧)', 2, 1, '历史数据中的通过标记'),
  ('check_status', 'warn', '警告', 3, 1, '存在问题需关注'),
  ('check_status', 'fail', '失败', 4, 1, '检查未通过'),
  ('console_type', 'stock', '个股', 1, 1, '具体股票+代码'),
  ('console_type', 'industry', '行业', 2, 1, '申万最下级/自定义板块'),
  ('console_type', 'market', '市场', 3, 1, 'A股/港股/美股大盘'),
  ('entity_type', 'blogger', '博主', 1, 1, NULL),
  ('entity_type', 'stock', '个股', 2, 1, NULL),
  ('entity_type', 'industry', '行业', 3, 1, NULL),
  ('entity_type', 'market', '市场', 4, 1, NULL),
  ('food_homonym', '小米', '小米', 0, 1, '与食物/日用品同名的股名：需证券语境词或产品词才判 link，仅动作词判 doubt'),
  ('food_homonym', '苹果', '苹果', 0, 1, '与食物/日用品同名的股名：需证券语境词或产品词才判 link，仅动作词判 doubt'),
  ('layer', 'my', '我的', 1, 1, '个人总结/自建框架层'),
  ('layer', 'blogger', '博主', 2, 1, '博主画像及其产出层'),
  ('layer', 'other', '其他', 3, 1, '引用/外部资料层'),
  ('layer', 'macro', '宏观', 4, 1, '宏观分析层'),
  ('layer', 'workspace', '工作区', 5, 1, '工作区文件（粗制品/原始资源/控制台等）'),
  ('layer', 'attachment', '附件', 6, 1, '附件目录（图片等非条目）'),
  ('platform', 'xueqiu', '雪球', 1, 1, '雪球平台'),
  ('platform', 'douyin', '抖音', 2, 1, '抖音平台'),
  ('platform', 'xiaohongshu', '小红书', 3, 1, '小红书平台'),
  ('post_content_type', 'research', '研究', 1, 1, '含数据/估值/行业结构的可复用分析；已沉淀框架文件则观点列写见 [[分类/文件名]]'),
  ('post_content_type', 'predict', '预测记录', 2, 1, '对未来走势的可验证判断，三要素：明确方向＋未来指向（时间窗或事件条件）＋可判对错（目标位/幅度/点位进信号列）。2026-09-04 用户补漏'),
  ('post_content_type', 'view', '观点', 3, 1, '对个股/行业/市场/政策的当下判断（无未来指向），须带方向'),
  ('post_content_type', 'insight', '心得总结', 4, 1, '投资心得、方法论、复盘框架'),
  ('post_content_type', 'chat', '闲聊', 5, 1, '仅当能刻画「擅长与局限/投资心态」时留存，否则舍弃'),
  ('post_content_type', 'trade', '买卖记录', 6, 1, '明确买卖动作；权威存 blogger_trades，本表仅作历史遗留标记（新数据走 blogger_trade）'),
  ('prediction_status', 'pending', '待验证', 1, 1, '尚未到验证时点'),
  ('prediction_status', 'verifying', '验证中', 2, 1, '已有部分验证证据'),
  ('prediction_status', 'verified_correct', '已验证(正确)', 3, 1, '方向正确（数值偏差进验证备注）'),
  ('prediction_status', 'verified_wrong', '已验证(错误)', 4, 1, '方向相反/关键数值未兑现'),
  ('prediction_status', 'revoked', '已撤销', 5, 1, '博主撤回或判断失效'),
  ('source_type', 'raw', '原始资源', 1, 1, '直接由原始资源提炼'),
  ('source_type', 'coarse', '粗制品', 2, 1, '由粗制品提炼'),
  ('stance', 'bullish', '看多', 1, 1, '方向：看多/看好/认为便宜'),
  ('stance', 'bearish', '看空', 2, 1, '方向：看空/认为高估/规避'),
  ('stance', 'neutral', '中性', 3, 1, '方向：中性/观望/仅陈述条件'),
  ('stance', 'short_bullish', '短期看多', 4, 1, NULL),
  ('stance', 'short_bearish', '短期看空', 5, 1, NULL),
  ('stance', 'long_bullish', '长期看多', 6, 1, NULL),
  ('stance', 'long_bearish', '长期看空', 7, 1, NULL),
  ('tag', '个股/医药生物', '个股/医药生物', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '交易体系/仓位管理', '交易体系/仓位管理', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '交易体系/价值投资', '交易体系/价值投资', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '交易体系/止损止盈', '交易体系/止损止盈', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '交易体系/风险控制', '交易体系/风险控制', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '分析框架/估值', '分析框架/估值', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '分析框架/估值方法', '分析框架/估值方法', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '分析框架/商业模式', '分析框架/商业模式', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '分析框架/方法论', '分析框架/方法论', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '分析框架/行业分析', '分析框架/行业分析', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '市场/A股', '市场/A股', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '市场/加密货币', '市场/加密货币', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '市场/港股', '市场/港股', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '市场/美股', '市场/美股', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心得/买卖决策', '投资心得/买卖决策', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心得/市场规律', '投资心得/市场规律', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心得/市场规律/周期特征', '投资心得/市场规律/周期特征', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心得/投资理念', '投资心得/投资理念', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心得/投资理念/回撤控制', '投资心得/投资理念/回撤控制', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心得/教训复盘', '投资心得/教训复盘', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心态修炼/情绪管理', '投资心态/心态修炼/情绪管理', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心态修炼/独立思考', '投资心态/心态修炼/独立思考', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心态修炼/知行合一', '投资心态/心态修炼/知行合一', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心态修炼/空仓心态', '投资心态/心态修炼/空仓心态', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心态修炼/纪律', '投资心态/心态修炼/纪律', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心态修炼/耐心', '投资心态/心态修炼/耐心', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心态修炼/逆向思维', '投资心态/心态修炼/逆向思维', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心态修炼/风险意识', '投资心态/心态修炼/风险意识', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/FOMO', '投资心态/心理偏误/FOMO', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/叙事谬误', '投资心态/心理偏误/叙事谬误', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/后视偏差', '投资心态/心理偏误/后视偏差', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/幸存者偏差', '投资心态/心理偏误/幸存者偏差', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/心理账户', '投资心态/心理偏误/心理账户', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/损失厌恶', '投资心态/心理偏误/损失厌恶', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/沉没成本', '投资心态/心理偏误/沉没成本', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/确认偏误', '投资心态/心理偏误/确认偏误', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/路径依赖', '投资心态/心理偏误/路径依赖', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/过度自信', '投资心态/心理偏误/过度自信', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理偏误/锚定效应', '投资心态/心理偏误/锚定效应', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/心理陷阱', '投资心态/心理陷阱', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/自我认知', '投资心态/自我认知', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '投资心态/预期管理', '投资心态/预期管理', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/AI与算力', '行业/AI与算力', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/AI与算力/AI应用', '行业/AI与算力/AI应用', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/AI与算力/算力基础设施', '行业/AI与算力/算力基础设施', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/互联网', '行业/互联网', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/传媒/广告营销', '行业/传媒/广告营销', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/农林牧渔/养殖业', '行业/农林牧渔/养殖业', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/医药生物/创新药', '行业/医药生物/创新药', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/基础化工/农药', '行业/基础化工/农药', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/基础化工/化学原料', '行业/基础化工/化学原料', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/建筑材料/水泥', '行业/建筑材料/水泥', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/房地产/房地产服务', '行业/房地产/房地产服务', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/有色金属/工业金属', '行业/有色金属/工业金属', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/汽车', '行业/汽车', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/电力设备/电池', '行业/电力设备/电池', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/电子/半导体', '行业/电子/半导体', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/纺织服饰/饰品', '行业/纺织服饰/饰品', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/美容护理/个护用品', '行业/美容护理/个护用品', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/能源金属/锂', '行业/能源金属/锂', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/轻工制造/文娱用品', '行业/轻工制造/文娱用品', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/食品饮料', '行业/食品饮料', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('tag', '行业/食品饮料/饮料乳品', '行业/食品饮料/饮料乳品', 0, 1, '标签（原 tags 表迁入，2026-09-12）'),
  ('target_relation', 'new', '新建', 1, 1, '库内无同类，新建条目'),
  ('target_relation', 'append', '追加', 2, 1, '追加到已有条目'),
  ('target_relation', 'complement', '互补', 3, 1, '与已有条目互补（同主题不同角度）'),
  ('target_relation', 'conflict_check', '矛盾预检', 4, 1, '写前矛盾预警'),
  ('target_relation', 'other', '其他', 5, 1, '无法归入上述主类型'),
  ('target_type', 'wiki', '框架条目', 1, 1, '六大分类 wiki 框架条目'),
  ('target_type', 'blogger', '博主画像', 2, 1, '博主画像/言论追踪'),
  ('target_type', 'macro', '宏观条目', 3, 1, '宏观层条目'),
  ('verify_result', 'correct', '正确', 1, 1, '方向正确即正确'),
  ('verify_result', 'wrong', '错误', 2, 1, '方向相反/关键数值未兑现'),
  ('verify_result', 'revoked', '已撤销', 3, 1, '撤销验证');

-- ============ 二、博主与业务表 ============
CREATE TABLE bloggers (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名',
  `dir` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'vault 目录',
  `alias` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '别名',
  `xueqiu_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '雪球用户 id',
  `platform_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '平台，字典项 dict.type=platform',
  `special` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否特别关注',
  `summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '博主简介',
  `strengths` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '优势',
  `limitations` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '局限',
  `info_cutoff` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信息截止日期',
  `file_count` int unsigned NOT NULL DEFAULT '0' COMMENT '产出文件数',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `avatar` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像地址',
  `deleted_at` datetime DEFAULT NULL COMMENT '软删时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  KEY `idx_platform` (`platform_code`),
  KEY `idx_special` (`special`)
) ENGINE=InnoDB AUTO_INCREMENT=69316 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主表';

CREATE TABLE post_history (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `blogger_id` bigint unsigned NOT NULL COMMENT '博主 id，指向博主表',
  `blogger` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名',
  `platform_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '平台，字典项 dict.type=platform',
  `platform_post_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '平台内帖子 id',
  `source_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '原文链接',
  `url_hash` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '原文链接的 md5，唯一键',
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '标题',
  `raw_text` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '采集到的原文全文',
  `raw_text_len` int unsigned NOT NULL DEFAULT '0' COMMENT '原文长度',
  `form` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态',
  `posted_at` datetime NOT NULL COMMENT '发帖时间',
  `edited_at` datetime DEFAULT NULL COMMENT '平台侧最后编辑时间',
  `fetched_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
  `content_hash` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '原文内容的 md5，重采时比对',
  `reply_count` int unsigned DEFAULT NULL COMMENT '回复数',
  `retweet_count` int unsigned DEFAULT NULL COMMENT '转发数',
  `like_count` int unsigned DEFAULT NULL COMMENT '点赞数',
  `fetch_method` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '采集方式',
  `src_rel` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源批次文件路径（历史批次专用；2026-09-12 起采集直接落库，新行不写）',
  `collector` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '采集者',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_url` (`url_hash`),
  UNIQUE KEY `uk_blogger_post` (`blogger_id`,`platform_post_id`),
  KEY `idx_blogger_time` (`blogger_id`,`posted_at`),
  KEY `idx_posted` (`posted_at`),
  KEY `idx_platform` (`platform_code`)
) ENGINE=InnoDB AUTO_INCREMENT=1115 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='帖子原文表（采集落点 + 提炼前原文；只存帖子必要信息，且只保留 30 天）';

CREATE TABLE quotes (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `seq` int NOT NULL COMMENT '轮播顺序',
  `text` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '语录内容',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `seq` (`seq`)
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='首页语录表';

CREATE TABLE todos (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `content` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '待办内容',
  `due_date` date DEFAULT NULL COMMENT '截止日期',
  `done` tinyint NOT NULL DEFAULT '0' COMMENT '是否完成',
  `done_at` datetime DEFAULT NULL COMMENT '完成时间',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='首页待办表';

-- ============ 三、流水与流程记录 ============
CREATE TABLE refine_records (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `source_url` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源链接',
  `source_type_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '来源类型，字典项 dict.type=source_type',
  `from_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '来源文件路径',
  `blogger_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '博主名',
  `blogger_updated` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否更新博主条目',
  `reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '提炼理由',
  `steps` json DEFAULT NULL COMMENT '推理步骤',
  `verify_ok` tinyint(1) DEFAULT NULL COMMENT '是否通过校验',
  `verify_detail` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '校验详情',
  `verification_hints` json DEFAULT NULL COMMENT '待验证提示',
  `at` bigint NOT NULL DEFAULT '0' COMMENT '提炼时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_source_type` (`source_type_code`),
  KEY `idx_from` (`from_rel`),
  KEY `idx_at` (`at`)
) ENGINE=InnoDB AUTO_INCREMENT=254 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提炼记录表';

CREATE TABLE refine_target_sub (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `record_id` bigint unsigned NOT NULL COMMENT '提炼记录 id，指向提炼记录表',
  `target_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '产出文件路径',
  `target_type_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标类型，字典项 dict.type=target_type',
  `layer_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '归属层，字典项 dict.type=layer',
  `relation_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'other' COMMENT '与已有条目的关系，字典项 dict.type=target_relation',
  `relation_note` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关系说明',
  `category_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分类，字典项 dict.type=category',
  `tags` json DEFAULT NULL COMMENT '标签',
  `thinking` json DEFAULT NULL COMMENT '思考链路',
  `basis` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '依据',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_record` (`record_id`),
  KEY `idx_target_type` (`target_type_code`),
  KEY `idx_layer` (`layer_code`),
  KEY `idx_relation` (`relation_code`),
  KEY `idx_category` (`category_code`),
  CONSTRAINT `fk_rt_record` FOREIGN KEY (`record_id`) REFERENCES `refine_records` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=427 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提炼目标子表';

CREATE TABLE review_records (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `review_date` date NOT NULL COMMENT '审查日期',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '审查标题',
  `method` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '审查方式',
  `meta` json DEFAULT NULL COMMENT '元信息',
  `main_problems` json DEFAULT NULL COMMENT '主要问题',
  `groups` json DEFAULT NULL COMMENT '分组结果',
  `summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '审查小结',
  `recycle` json DEFAULT NULL COMMENT '回收项',
  `actions` json DEFAULT NULL COMMENT '后续动作',
  `saved_at` bigint NOT NULL DEFAULT '0' COMMENT '保存时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_date` (`review_date`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审查记录表';

CREATE TABLE review_check_sub (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `review_id` bigint unsigned NOT NULL COMMENT '审查记录 id，指向审查记录表',
  `item_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '检查项',
  `result` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '检查结果',
  `compare` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '对比说明',
  `status_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '检查状态，字典项 dict.type=check_status',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_review` (`review_id`),
  KEY `idx_status` (`status_code`),
  CONSTRAINT `fk_rc_review` FOREIGN KEY (`review_id`) REFERENCES `review_records` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审查检查项子表';

CREATE TABLE statement_id_seq (
  `name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '序列名',
  `id` bigint unsigned NOT NULL COMMENT '已发放的最大帖子 id',
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='帖子 id 序列表';

CREATE TABLE mention_case (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `sentence` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '待判定的原文片段（一句/一小句）',
  `alias` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '句中出现的称呼/产品词',
  `stock_id` bigint unsigned DEFAULT NULL COMMENT '正确归属的个股 id，指向个股表',
  `stock_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '个股名快照',
  `verdict` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '正确判定：link=应建关联 / doubt=存疑 / skip=不是个股',
  `reason` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '判定理由（命中/否决了哪条规则）',
  `source` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'refine' COMMENT '来源：refine 提炼 / review 审查 / user 用户复核 / seed 初始',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_alias` (`alias`),
  KEY `idx_verdict` (`verdict`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提及判定案例表';

-- ============ 四、言论六表（一条帖子只落其中一张） ============
CREATE TABLE statement_trade (
  `id` bigint unsigned NOT NULL COMMENT '帖子 id，六张帖子表全局唯一',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名，冗余自博主表',
  `statement_date` date DEFAULT NULL COMMENT '言论时间，该言论的发布日',
  `view_date` date DEFAULT NULL COMMENT '观点时间，判断成立时点',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted/explicit/derived',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间推算依据，原文摘录',
  `stance` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号方向，字典项 dict.type=stance',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容，简短判断',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源批次或平台',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '博主 id，指向博主表',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源批次文件路径',
  `post_history_id` bigint unsigned DEFAULT NULL COMMENT '指向 post_history.id（帖子层原文留档；留档仅保留 30 天，过期后该 id 查不到对应行属正常）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否待复核',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `form` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏',
  `price` decimal(16,4) DEFAULT NULL COMMENT '成交价',
  `market_cap` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '当时市值',
  `trade_date` date DEFAULT NULL COMMENT '操作日期',
  `trade_note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '操作理由',
  `wiki_ref` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目文件路径',
  `reply_to` text COLLATE utf8mb4_unicode_ci COMMENT '被回应者的原话（原样照抄，不提炼）',
  `fetched_at` datetime DEFAULT NULL COMMENT '采集时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='买卖记录帖子表';

CREATE TABLE statement_predict (
  `id` bigint unsigned NOT NULL COMMENT '帖子 id，六张帖子表全局唯一',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名，冗余自博主表',
  `statement_date` date DEFAULT NULL COMMENT '言论时间，该言论的发布日',
  `view_date` date DEFAULT NULL COMMENT '观点时间，判断成立时点',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted/explicit/derived',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间推算依据，原文摘录',
  `stance` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号方向，字典项 dict.type=stance',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容，简短判断',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源批次或平台',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '博主 id，指向博主表',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源批次文件路径',
  `post_history_id` bigint unsigned DEFAULT NULL COMMENT '指向 post_history.id（帖子层原文留档；留档仅保留 30 天，过期后该 id 查不到对应行属正常）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否待复核',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `form` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏',
  `ref_price` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '判断时参考价',
  `target_price` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标价',
  `target_date` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标时间',
  `date_precision` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标时间精度：day/month/year',
  `verify_date` date DEFAULT NULL COMMENT '最近验证日期',
  `verify_result` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '最近验证结果，字典项 dict.type=verify_result',
  `wiki_ref` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目文件路径',
  `reply_to` text COLLATE utf8mb4_unicode_ci COMMENT '被回应者的原话（原样照抄，不提炼）',
  `fetched_at` datetime DEFAULT NULL COMMENT '采集时间',
  `status_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '预测状态，字典项 dict.type=prediction_status',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预测记录帖子表';

CREATE TABLE statement_research (
  `id` bigint unsigned NOT NULL COMMENT '帖子 id，六张帖子表全局唯一',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名，冗余自博主表',
  `statement_date` date DEFAULT NULL COMMENT '言论时间，该言论的发布日',
  `view_date` date DEFAULT NULL COMMENT '观点时间，判断成立时点',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted/explicit/derived',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间推算依据，原文摘录',
  `stance` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号方向，字典项 dict.type=stance',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容，简短判断',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源批次或平台',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '博主 id，指向博主表',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源批次文件路径',
  `post_history_id` bigint unsigned DEFAULT NULL COMMENT '指向 post_history.id（帖子层原文留档；留档仅保留 30 天，过期后该 id 查不到对应行属正常）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否待复核',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `form` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏',
  `data_refs` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据来源',
  `wiki_ref` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目文件路径',
  `reply_to` text COLLATE utf8mb4_unicode_ci COMMENT '被回应者的原话（原样照抄，不提炼）',
  `fetched_at` datetime DEFAULT NULL COMMENT '采集时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='研究帖子表';

CREATE TABLE statement_view (
  `id` bigint unsigned NOT NULL COMMENT '帖子 id，六张帖子表全局唯一',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名，冗余自博主表',
  `statement_date` date DEFAULT NULL COMMENT '言论时间，该言论的发布日',
  `view_date` date DEFAULT NULL COMMENT '观点时间，判断成立时点',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted/explicit/derived',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间推算依据，原文摘录',
  `stance` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号方向，字典项 dict.type=stance',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容，简短判断',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源批次或平台',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '博主 id，指向博主表',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源批次文件路径',
  `post_history_id` bigint unsigned DEFAULT NULL COMMENT '指向 post_history.id（帖子层原文留档；留档仅保留 30 天，过期后该 id 查不到对应行属正常）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否待复核',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `form` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏',
  `wiki_ref` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目文件路径',
  `reply_to` text COLLATE utf8mb4_unicode_ci COMMENT '被回应者的原话（原样照抄，不提炼）',
  `fetched_at` datetime DEFAULT NULL COMMENT '采集时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='观点帖子表';

CREATE TABLE statement_insight (
  `id` bigint unsigned NOT NULL COMMENT '帖子 id，六张帖子表全局唯一',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名，冗余自博主表',
  `statement_date` date DEFAULT NULL COMMENT '言论时间，该言论的发布日',
  `view_date` date DEFAULT NULL COMMENT '观点时间，判断成立时点',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted/explicit/derived',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间推算依据，原文摘录',
  `stance` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号方向，字典项 dict.type=stance',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容，简短判断',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源批次或平台',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '博主 id，指向博主表',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源批次文件路径',
  `post_history_id` bigint unsigned DEFAULT NULL COMMENT '指向 post_history.id（帖子层原文留档；留档仅保留 30 天，过期后该 id 查不到对应行属正常）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否待复核',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `form` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏',
  `wiki_ref` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目文件路径',
  `reply_to` text COLLATE utf8mb4_unicode_ci COMMENT '被回应者的原话（原样照抄，不提炼）',
  `fetched_at` datetime DEFAULT NULL COMMENT '采集时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='心得总结帖子表';

CREATE TABLE statement_chat (
  `id` bigint unsigned NOT NULL COMMENT '帖子 id，六张帖子表全局唯一',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名，冗余自博主表',
  `statement_date` date DEFAULT NULL COMMENT '言论时间，该言论的发布日',
  `view_date` date DEFAULT NULL COMMENT '观点时间，判断成立时点',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted/explicit/derived',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间推算依据，原文摘录',
  `stance` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号方向，字典项 dict.type=stance',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容，简短判断',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源批次或平台',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '博主 id，指向博主表',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源批次文件路径',
  `post_history_id` bigint unsigned DEFAULT NULL COMMENT '指向 post_history.id（帖子层原文留档；留档仅保留 30 天，过期后该 id 查不到对应行属正常）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否待复核',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `form` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏',
  `wiki_ref` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目文件路径',
  `reply_to` text COLLATE utf8mb4_unicode_ci COMMENT '被回应者的原话（原样照抄，不提炼）',
  `fetched_at` datetime DEFAULT NULL COMMENT '采集时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='闲聊帖子表';

-- ============ 五、实体三表（个股 / 行业 / 市场） ============
CREATE TABLE stocks (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '个股名称',
  `code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '股票代码',
  `market_code` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '主市场码，字典项 markets.code',
  `aliases` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '别名，逗号分隔，如 寒王,寒武纪-U',
  `keywords` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '主营/产品关键词，逗号分隔，用于判定「文中该产品词是否指这只股」（F7 同句共现）；通用词只放这里，不放 aliases',
  `hk_connect` tinyint(1) DEFAULT NULL COMMENT '是否港股通',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序',
  `enabled` tinyint NOT NULL DEFAULT '1' COMMENT '是否启用',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_name` (`name`),
  KEY `idx_code` (`code`),
  KEY `idx_market` (`market_code`)
) ENGINE=InnoDB AUTO_INCREMENT=311 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='个股表';

CREATE TABLE industries (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '行业名称',
  `code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '行业代码',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序',
  `enabled` tinyint NOT NULL DEFAULT '1' COMMENT '是否启用',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_name` (`name`),
  KEY `idx_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=281 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='行业表';

CREATE TABLE markets (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `code` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '市场码：a/hk/us/kr…',
  `name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '市场名称：A股/港股/美股/韩股',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序',
  `enabled` tinyint NOT NULL DEFAULT '1' COMMENT '是否启用',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_code` (`code`),
  UNIQUE KEY `uq_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='市场表';

-- ============ 六、关联表与子表 ============
CREATE TABLE statement_blogger_rel (
  `statement_id` bigint unsigned NOT NULL COMMENT '言论 id，指向六张言论表之一',
  `blogger_id` bigint unsigned NOT NULL COMMENT '博主 id，指向博主表',
  `blogger_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名快照',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`statement_id`,`blogger_id`),
  KEY `idx_blogger` (`blogger_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='言论博主关联表';

CREATE TABLE statement_stock_rel (
  `statement_id` bigint unsigned NOT NULL COMMENT '言论 id，指向六张言论表之一',
  `stock_id` bigint unsigned NOT NULL COMMENT '个股 id，指向个股表',
  `role_code` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'subject' COMMENT '角色：subject 主体，mention 文中提及',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`statement_id`,`stock_id`),
  KEY `idx_stock` (`stock_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='言论个股关联表';

CREATE TABLE statement_industry_rel (
  `statement_id` bigint unsigned NOT NULL COMMENT '言论 id，指向六张言论表之一',
  `industry_id` bigint unsigned NOT NULL COMMENT '行业 id，指向行业表',
  `role_code` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'subject' COMMENT '角色：subject 主体，mention 文中提及',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`statement_id`,`industry_id`),
  KEY `idx_industry` (`industry_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='言论行业关联表';

CREATE TABLE statement_market_rel (
  `statement_id` bigint unsigned NOT NULL COMMENT '言论 id，指向六张言论表之一',
  `market_id` bigint unsigned NOT NULL COMMENT '市场 id，指向市场表',
  `role_code` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'subject' COMMENT '角色：subject 主体，mention 文中提及',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`statement_id`,`market_id`),
  KEY `idx_market` (`market_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='言论市场关联表';

CREATE TABLE stock_industry_rel (
  `stock_id` bigint unsigned NOT NULL COMMENT '个股 id，指向个股表',
  `industry_id` bigint unsigned NOT NULL COMMENT '行业 id，指向行业表',
  `role_code` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'primary' COMMENT '角色：primary 主行业，secondary 次要行业，derived 由言论共现推导',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`stock_id`,`industry_id`),
  KEY `idx_industry` (`industry_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='个股行业关联表';

CREATE TABLE stock_market_rel (
  `stock_id` bigint unsigned NOT NULL COMMENT '个股 id，指向个股表',
  `market_id` bigint unsigned NOT NULL COMMENT '市场 id，指向市场表',
  `role_code` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'primary' COMMENT '角色：primary 主市场，secondary 次市场',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`stock_id`,`market_id`),
  KEY `idx_market` (`market_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='个股市场关联表';

CREATE TABLE statement_verify_sub (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `statement_id` bigint unsigned NOT NULL COMMENT '言论 id，指向六张言论表之一',
  `verify_date` date DEFAULT NULL COMMENT '验证日期',
  `verifier` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '验证人',
  `basis` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '验证依据',
  `result_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '验证结果，字典项 dict.type=verify_result',
  `note` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_prediction` (`statement_id`),
  KEY `idx_result` (`result_code`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预测验证子表';

CREATE TABLE statement_review_sub (
  `id` int unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `statement_id` bigint unsigned NOT NULL COMMENT '言论 id，指向六张言论表之一',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '博主名',
  `suggestion` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '复核建议内容',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'open' COMMENT '处理状态：open/applied',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_stmt` (`statement_id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='帖子复核建议子表';

-- ============ 六、只读视图（言论六表 UNION ALL，36 列） ============
-- 分类权威 = content_type 六分法；非本类型列补 NULL；预测/交易专属列直取本表（帖子唯一落点，无需关联表）
CREATE ALGORITHM=UNDEFINED DEFINER=`jianglb`@`%` SQL SECURITY DEFINER VIEW statements AS select `statement_research`.`id` AS `id`,`statement_research`.`blogger` AS `blogger`,`statement_research`.`statement_date` AS `statement_date`,`statement_research`.`view_date` AS `view_date`,`statement_research`.`view_date_source` AS `view_date_source`,`statement_research`.`view_date_precision` AS `view_date_precision`,`statement_research`.`view_date_basis` AS `view_date_basis`,`statement_research`.`stance` AS `stance`,`statement_research`.`view_text` AS `view_text`,`statement_research`.`signal_text` AS `signal_text`,`statement_research`.`source` AS `source`,`statement_research`.`source_url` AS `source_url`,`statement_research`.`blogger_id` AS `blogger_id`,`statement_research`.`src_rel` AS `src_rel`,`statement_research`.`post_history_id` AS `post_history_id`,`statement_research`.`review_required` AS `review_required`,`statement_research`.`dedup_key` AS `dedup_key`,`statement_research`.`created_at` AS `created_at`,`statement_research`.`updated_at` AS `updated_at`,`statement_research`.`form` AS `form`,NULL AS `price`,NULL AS `market_cap`,NULL AS `trade_date`,NULL AS `trade_note`,NULL AS `ref_price`,NULL AS `target_price`,NULL AS `target_date`,NULL AS `date_precision`,NULL AS `verify_date`,NULL AS `verify_result`,`statement_research`.`data_refs` AS `data_refs`,`statement_research`.`wiki_ref` AS `wiki_ref`,`statement_research`.`reply_to` AS `reply_to`,`statement_research`.`fetched_at` AS `fetched_at`,NULL AS `transferable`,'research' AS `content_type`,NULL AS `status_code` from `statement_research` union all select `statement_predict`.`id` AS `id`,`statement_predict`.`blogger` AS `blogger`,`statement_predict`.`statement_date` AS `statement_date`,`statement_predict`.`view_date` AS `view_date`,`statement_predict`.`view_date_source` AS `view_date_source`,`statement_predict`.`view_date_precision` AS `view_date_precision`,`statement_predict`.`view_date_basis` AS `view_date_basis`,`statement_predict`.`stance` AS `stance`,`statement_predict`.`view_text` AS `view_text`,`statement_predict`.`signal_text` AS `signal_text`,`statement_predict`.`source` AS `source`,`statement_predict`.`source_url` AS `source_url`,`statement_predict`.`blogger_id` AS `blogger_id`,`statement_predict`.`src_rel` AS `src_rel`,`statement_predict`.`post_history_id` AS `post_history_id`,`statement_predict`.`review_required` AS `review_required`,`statement_predict`.`dedup_key` AS `dedup_key`,`statement_predict`.`created_at` AS `created_at`,`statement_predict`.`updated_at` AS `updated_at`,`statement_predict`.`form` AS `form`,NULL AS `price`,NULL AS `market_cap`,NULL AS `trade_date`,NULL AS `trade_note`,`statement_predict`.`ref_price` AS `ref_price`,`statement_predict`.`target_price` AS `target_price`,`statement_predict`.`target_date` AS `target_date`,`statement_predict`.`date_precision` AS `date_precision`,`statement_predict`.`verify_date` AS `verify_date`,`statement_predict`.`verify_result` AS `verify_result`,NULL AS `data_refs`,`statement_predict`.`wiki_ref` AS `wiki_ref`,`statement_predict`.`reply_to` AS `reply_to`,`statement_predict`.`fetched_at` AS `fetched_at`,NULL AS `transferable`,'predict' AS `content_type`,`statement_predict`.`status_code` AS `status_code` from `statement_predict` union all select `statement_view`.`id` AS `id`,`statement_view`.`blogger` AS `blogger`,`statement_view`.`statement_date` AS `statement_date`,`statement_view`.`view_date` AS `view_date`,`statement_view`.`view_date_source` AS `view_date_source`,`statement_view`.`view_date_precision` AS `view_date_precision`,`statement_view`.`view_date_basis` AS `view_date_basis`,`statement_view`.`stance` AS `stance`,`statement_view`.`view_text` AS `view_text`,`statement_view`.`signal_text` AS `signal_text`,`statement_view`.`source` AS `source`,`statement_view`.`source_url` AS `source_url`,`statement_view`.`blogger_id` AS `blogger_id`,`statement_view`.`src_rel` AS `src_rel`,`statement_view`.`post_history_id` AS `post_history_id`,`statement_view`.`review_required` AS `review_required`,`statement_view`.`dedup_key` AS `dedup_key`,`statement_view`.`created_at` AS `created_at`,`statement_view`.`updated_at` AS `updated_at`,`statement_view`.`form` AS `form`,NULL AS `price`,NULL AS `market_cap`,NULL AS `trade_date`,NULL AS `trade_note`,NULL AS `ref_price`,NULL AS `target_price`,NULL AS `target_date`,NULL AS `date_precision`,NULL AS `verify_date`,NULL AS `verify_result`,NULL AS `data_refs`,`statement_view`.`wiki_ref` AS `wiki_ref`,`statement_view`.`reply_to` AS `reply_to`,`statement_view`.`fetched_at` AS `fetched_at`,NULL AS `transferable`,'view' AS `content_type`,NULL AS `status_code` from `statement_view` union all select `statement_insight`.`id` AS `id`,`statement_insight`.`blogger` AS `blogger`,`statement_insight`.`statement_date` AS `statement_date`,`statement_insight`.`view_date` AS `view_date`,`statement_insight`.`view_date_source` AS `view_date_source`,`statement_insight`.`view_date_precision` AS `view_date_precision`,`statement_insight`.`view_date_basis` AS `view_date_basis`,`statement_insight`.`stance` AS `stance`,`statement_insight`.`view_text` AS `view_text`,`statement_insight`.`signal_text` AS `signal_text`,`statement_insight`.`source` AS `source`,`statement_insight`.`source_url` AS `source_url`,`statement_insight`.`blogger_id` AS `blogger_id`,`statement_insight`.`src_rel` AS `src_rel`,`statement_insight`.`post_history_id` AS `post_history_id`,`statement_insight`.`review_required` AS `review_required`,`statement_insight`.`dedup_key` AS `dedup_key`,`statement_insight`.`created_at` AS `created_at`,`statement_insight`.`updated_at` AS `updated_at`,`statement_insight`.`form` AS `form`,NULL AS `price`,NULL AS `market_cap`,NULL AS `trade_date`,NULL AS `trade_note`,NULL AS `ref_price`,NULL AS `target_price`,NULL AS `target_date`,NULL AS `date_precision`,NULL AS `verify_date`,NULL AS `verify_result`,NULL AS `data_refs`,`statement_insight`.`wiki_ref` AS `wiki_ref`,`statement_insight`.`reply_to` AS `reply_to`,`statement_insight`.`fetched_at` AS `fetched_at`,NULL AS `transferable`,'insight' AS `content_type`,NULL AS `status_code` from `statement_insight` union all select `statement_chat`.`id` AS `id`,`statement_chat`.`blogger` AS `blogger`,`statement_chat`.`statement_date` AS `statement_date`,`statement_chat`.`view_date` AS `view_date`,`statement_chat`.`view_date_source` AS `view_date_source`,`statement_chat`.`view_date_precision` AS `view_date_precision`,`statement_chat`.`view_date_basis` AS `view_date_basis`,`statement_chat`.`stance` AS `stance`,`statement_chat`.`view_text` AS `view_text`,`statement_chat`.`signal_text` AS `signal_text`,`statement_chat`.`source` AS `source`,`statement_chat`.`source_url` AS `source_url`,`statement_chat`.`blogger_id` AS `blogger_id`,`statement_chat`.`src_rel` AS `src_rel`,`statement_chat`.`post_history_id` AS `post_history_id`,`statement_chat`.`review_required` AS `review_required`,`statement_chat`.`dedup_key` AS `dedup_key`,`statement_chat`.`created_at` AS `created_at`,`statement_chat`.`updated_at` AS `updated_at`,`statement_chat`.`form` AS `form`,NULL AS `price`,NULL AS `market_cap`,NULL AS `trade_date`,NULL AS `trade_note`,NULL AS `ref_price`,NULL AS `target_price`,NULL AS `target_date`,NULL AS `date_precision`,NULL AS `verify_date`,NULL AS `verify_result`,NULL AS `data_refs`,`statement_chat`.`wiki_ref` AS `wiki_ref`,`statement_chat`.`reply_to` AS `reply_to`,`statement_chat`.`fetched_at` AS `fetched_at`,NULL AS `transferable`,'chat' AS `content_type`,NULL AS `status_code` from `statement_chat` union all select `statement_trade`.`id` AS `id`,`statement_trade`.`blogger` AS `blogger`,`statement_trade`.`statement_date` AS `statement_date`,`statement_trade`.`view_date` AS `view_date`,`statement_trade`.`view_date_source` AS `view_date_source`,`statement_trade`.`view_date_precision` AS `view_date_precision`,`statement_trade`.`view_date_basis` AS `view_date_basis`,`statement_trade`.`stance` AS `stance`,`statement_trade`.`view_text` AS `view_text`,`statement_trade`.`signal_text` AS `signal_text`,`statement_trade`.`source` AS `source`,`statement_trade`.`source_url` AS `source_url`,`statement_trade`.`blogger_id` AS `blogger_id`,`statement_trade`.`src_rel` AS `src_rel`,`statement_trade`.`post_history_id` AS `post_history_id`,`statement_trade`.`review_required` AS `review_required`,`statement_trade`.`dedup_key` AS `dedup_key`,`statement_trade`.`created_at` AS `created_at`,`statement_trade`.`updated_at` AS `updated_at`,`statement_trade`.`form` AS `form`,`statement_trade`.`price` AS `price`,`statement_trade`.`market_cap` AS `market_cap`,`statement_trade`.`trade_date` AS `trade_date`,`statement_trade`.`trade_note` AS `trade_note`,NULL AS `ref_price`,NULL AS `target_price`,NULL AS `target_date`,NULL AS `date_precision`,NULL AS `verify_date`,NULL AS `verify_result`,NULL AS `data_refs`,`statement_trade`.`wiki_ref` AS `wiki_ref`,`statement_trade`.`reply_to` AS `reply_to`,`statement_trade`.`fetched_at` AS `fetched_at`,NULL AS `transferable`,'trade' AS `content_type`,NULL AS `status_code` from `statement_trade`;
