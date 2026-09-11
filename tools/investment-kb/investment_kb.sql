-- ============================================================
-- investment_kb: 投资知识库看板派生数据层
-- 架构原则: 本地 vault 为绝对基准（第一/首要/绝对），本库仅为
--           阅读 + 加工总结的派生数据；一切冲突以 vault 为准。
-- 2026-09-03 与线上库对齐：bloggers 补 avatar；prediction_subjects 补 market/hk_connect；新增 blogger_statements/todos/quotes 三表；dict 补 platform=wechat。
-- 字符集: utf8mb4 / utf8mb4_unicode_ci
-- 约定: 枚举字段一律存码值，逻辑关联统一 dict 码值表（type+code）；主键自增；
--       枚举字段不设外键（dict 为逻辑字典，由应用层/迁移脚本维护）；每表每字段均带 COMMENT。
-- ============================================================
CREATE DATABASE IF NOT EXISTS investment_kb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE investment_kb;

-- ============ 一、码值表（统一字典） ============

-- 1. 统一字典表（合并原 14 张 dict_* 枚举表，主键 (type, code)）
CREATE TABLE dict (
  `type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '字典类型（原 dict_ 表名后缀）',
  `code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '字典项编码',
  `name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '显示名',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序',
  `enabled` tinyint NOT NULL DEFAULT '1' COMMENT '是否启用 1/0',
  `remark` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`type`,`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一字典表：合并原 14 张 dict_* 枚举表，主键(type,code)';

INSERT INTO dict (type, code, name, sort_order, remark) VALUES
('category','analysis_framework','分析框架',1,'方法论/思维框架类条目'),
('category','trading_system','交易体系',2,'交易规则/体系类条目'),
('category','investment_mentality','投资心态',3,'心态/心理类条目'),
('category','investment_insight','投资心得',4,'心得/复盘类条目'),
('category','stock','个股',5,'个股分析条目'),
('category','industry','行业',6,'行业研究条目'),
('category','macro','宏观',7,'宏观分析条目'),
('check_status','pass','通过',1,'检查通过'),
('check_status','ok','通过(旧)',2,'历史数据中的通过标记'),
('check_status','warn','警告',3,'存在问题需关注'),
('check_status','fail','失败',4,'检查未通过'),
('coarse_status','pending','待处理',1,'刚入库待处理'),
('coarse_status','scored','已评分',2,'已完成质量评分'),
('coarse_status','processed','已加工',3,'已粗加工完成'),
('console_type','stock','个股',1,'具体股票+代码'),
('console_type','industry','行业',2,'申万最下级/自定义板块'),
('console_type','market','市场',3,'A股/港股/美股大盘'),
('file_status','analyzing','分析中',1,'正在分析/加工中'),
('file_status','refined','已提炼',2,'已完成提炼'),
('file_status','pending','待提炼',3,'等待提炼'),
('file_type','post','帖子',1,'雪球/社区单帖'),
('file_type','article','文章',2,'长文/文章'),
('file_type','video','视频',3,'视频'),
('file_type','video_summary','视频整理',4,'视频内容整理稿'),
('file_type','link','链接',5,'链接型条目'),
('file_type','post_collection','帖子集',6,'博主多帖合集'),
('file_type','other','其他',7,'其他类型'),
('layer','my','我的',1,'个人总结/自建框架层'),
('layer','blogger','博主',2,'博主画像及其产出层'),
('layer','other','其他',3,'引用/外部资料层'),
('layer','macro','宏观',4,'宏观分析层'),
('layer','workspace','工作区',5,'工作区文件（粗制品/原始资源/控制台等）'),
('layer','attachment','附件',6,'附件目录（图片等非条目）'),
('platform','xueqiu','雪球',1,'雪球平台'),
('platform','douyin','抖音',2,'抖音平台'),
('platform','xiaohongshu','小红书',3,'小红书平台'),
('platform','wechat','公众号',4,'微信公众号平台'),
('prediction_status','pending','待验证',1,'尚未到验证时点'),
('prediction_status','verifying','验证中',2,'已有部分验证证据'),
('prediction_status','verified_correct','已验证(正确)',3,'方向正确（数值偏差进验证备注）'),
('prediction_status','verified_wrong','已验证(错误)',4,'方向相反/关键数值未兑现'),
('prediction_status','revoked','已撤销',5,'博主撤回或判断失效'),
('source_type','raw','原始资源',1,'直接由原始资源提炼'),
('source_type','coarse','粗制品',2,'由粗制品提炼'),
('target_relation','new','新建',1,'库内无同类，新建条目'),
('target_relation','append','追加',2,'追加到已有条目'),
('target_relation','complement','互补',3,'与已有条目互补（同主题不同角度）'),
('target_relation','conflict_check','矛盾预检',4,'写前矛盾预警'),
('target_relation','other','其他',5,'无法归入上述主类型'),
('target_type','wiki','框架条目',1,'六大分类 wiki 框架条目'),
('target_type','blogger','博主画像',2,'博主画像/言论追踪'),
('target_type','macro','宏观条目',3,'宏观层条目'),
('track_direction','enhance','增强',1,'支持该预测的新证据'),
('track_direction','refute','反驳',2,'反驳该预测的新证据'),
('track_direction','neutral','中性',3,'中性补充'),
('verify_result','correct','正确',1,'方向正确即正确'),
('verify_result','wrong','错误',2,'方向相反/关键数值未兑现'),
('verify_result','revoked','已撤销',3,'撤销验证'),
-- 2026-09-11 补：言论分型与信号字典（此前遗漏未入文件）
('stmt_content_type','research','研究',1,'研究/分析类言论'),
('stmt_content_type','predict','预测记录',2,'可验证的未来判断'),
('stmt_content_type','view','观点',3,'当下判断/认知'),
('stmt_content_type','insight','心得总结',4,'方法论/纪律/复盘'),
('stmt_content_type','chat','闲聊',5,'社交/情绪/画像素材'),
('stmt_content_type','trade','买卖记录',6,'当期买卖动作/仓位状态'),
('trade_op','buy','买入',1,'建仓买入'),
('trade_op','add','加仓',2,'加仓'),
('trade_op','reduce','减仓',3,'减仓'),
('trade_op','sell','卖出',4,'卖出'),
('trade_op','clear','清仓',5,'清空该标的仓位'),
('stance','bullish','看多',1,'不限时间的方向'),
('stance','bearish','看空',2,'不限时间的方向'),
('stance','short_bullish','短期看多',3,'明确短期（数日~数周）'),
('stance','short_bearish','短期看空',4,'明确短期'),
('stance','long_bullish','长期看多',5,'明确长期（数季~数年）'),
('stance','long_bearish','长期看空',6,'明确长期'),
('stance','neutral','中性',7,'明确不偏多空的立场（兼容历史值）')
;

-- ============ 二、业务表 ============

-- 11. 博主画像表（vault 扫描派生，vault 为准）
CREATE TABLE bloggers (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '博主主键',
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名（唯一）',
  `dir` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主在 vault 中的目录名',
  `alias` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '别名/曾用名',
  `xueqiu_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '雪球用户 ID（无则 NULL）',
  `platform_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '平台码值，关联 dict_platform.code（雪球/抖音/小红书）',
  `special` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否重点博主：1是 0否',
  `summary` text COLLATE utf8mb4_unicode_ci COMMENT '博主简介（画像摘要）',
  `strengths` text COLLATE utf8mb4_unicode_ci COMMENT '擅长领域',
  `limitations` text COLLATE utf8mb4_unicode_ci COMMENT '盲区/局限',
  `info_cutoff` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信息截止日期（画像信息更新点）',
  `file_count` int unsigned NOT NULL DEFAULT '0' COMMENT '博主产出文件数（vault 扫描统计）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  `avatar` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像 URL（雪球/小红书 CDN）',
  `deleted_at` datetime DEFAULT NULL COMMENT '软删除时间；NULL=正常',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  KEY `idx_platform` (`platform_code`),
  KEY `idx_special` (`special`)
) ENGINE=InnoDB AUTO_INCREMENT=56384 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主画像表：vault 博主目录扫描派生，冲突以 vault 为准';

-- 12. 标签字典表
CREATE TABLE tags (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '标签主键',
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '标签名（唯一，如 行业/传媒/广告营销）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=68115 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签字典表：全库标签去重';

-- 13. wiki 文件索引表（vault 扫描派生，vault 为准）
CREATE TABLE files (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `rel` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'vault 相对路径（唯一业务键）',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '条目标题',
  `layer_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '归属层码值，关联 dict_layer.code',
  `category_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分类码值，关联 dict_category.code',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '博主外键，关联 bloggers.id（博主层条目归属）',
  `author` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作者名',
  `type_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文件类型码值，关联 dict_file_type.code',
  `status_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '状态码值，关联 dict_file_status.code',
  `star` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否关注：1是 0否（我的关注列表）',
  `size_bytes` int unsigned NOT NULL DEFAULT '0' COMMENT '文件大小（字节）',
  `mtime` bigint NOT NULL DEFAULT '0' COMMENT '文件修改时间戳（毫秒，vault 增量同步依据）',
  `create_date` date DEFAULT NULL COMMENT '创建日期（frontmatter 解析）',
  `update_date` date DEFAULT NULL COMMENT '更新日期（frontmatter 解析）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rel` (`rel`),
  KEY `idx_layer` (`layer_code`),
  KEY `idx_category` (`category_code`),
  KEY `idx_blogger` (`blogger_id`),
  KEY `idx_star` (`star`),
  KEY `idx_mtime` (`mtime`),
  KEY `idx_type` (`type_code`),
  KEY `idx_status` (`status_code`),
  CONSTRAINT `fk_files_blogger` FOREIGN KEY (`blogger_id`) REFERENCES `bloggers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=678832 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='wiki 文件索引表：vault 扫描派生，看板数据主源（正文不入库，读取时回源 vault）';

-- 14. 文件-标签关联表（多对多，关系表统一 _rel 后缀）
CREATE TABLE file_tag_rel (
  `file_id` bigint unsigned NOT NULL COMMENT '文件外键，关联 files.id',
  `tag_id` bigint unsigned NOT NULL COMMENT '标签外键，关联 tags.id',
  PRIMARY KEY (`file_id`,`tag_id`),
  KEY `idx_tag` (`tag_id`),
  CONSTRAINT `fk_ft_file` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ft_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件-标签关联表：多对多映射';

-- 15. 提炼记录表（加工历史，vault 无对应物，独立存储）
CREATE TABLE refine_records (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '提炼记录主键',
  `source_url` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源链接（原始帖子 URL）',
  `source_type_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '来源类型码值，关联 dict_source_type.code（raw/coarse）',
  `from_rel` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '来源文件相对路径（粗制品/原始资源）',
  `blogger_name` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '涉及博主名',
  `blogger_updated` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否同步更新博主画像：1是 0否',
  `reason` text COLLATE utf8mb4_unicode_ci COMMENT '提炼理由（决策依据，含矛盾预警等）',
  `steps` json DEFAULT NULL COMMENT '提炼步骤数组（读取原文/识别/…）',
  `verify_ok` tinyint(1) DEFAULT NULL COMMENT '验证是否通过：1通过 0失败 NULL未验证',
  `verify_detail` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '验证详情（如 verify-format.py 结果）',
  `verification_hints` json DEFAULT NULL COMMENT '验证提示数组',
  `at` bigint NOT NULL DEFAULT '0' COMMENT '提炼时间戳（毫秒）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_source_type` (`source_type_code`),
  KEY `idx_from` (`from_rel`),
  KEY `idx_at` (`at`)
) ENGINE=InnoDB AUTO_INCREMENT=254 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提炼记录表：一次提炼决策链路（加工历史，展示用）';

-- 16. 提炼目标子表（1 提炼记录 → N 目标）
CREATE TABLE refine_targets (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '目标主键',
  `record_id` bigint unsigned NOT NULL COMMENT '提炼记录外键，关联 refine_records.id',
  `target_rel` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标条目相对路径（wiki/博主/宏观）',
  `target_type_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标类型码值，关联 dict_target_type.code',
  `layer_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标归属层码值，关联 dict_layer.code',
  `relation_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'other' COMMENT '关系码值，关联 dict_target_relation.code',
  `relation_note` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关系说明原文（如「新建；与…互补」细节）',
  `category_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标分类码值，关联 dict_category.code',
  `tags` json DEFAULT NULL COMMENT '目标标签数组（冗余，便于展示）',
  `thinking` json DEFAULT NULL COMMENT '思考链路数组（提炼时的认知过程）',
  `basis` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '提炼依据（原文支撑）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_record` (`record_id`),
  KEY `idx_target_type` (`target_type_code`),
  KEY `idx_layer` (`layer_code`),
  KEY `idx_relation` (`relation_code`),
  KEY `idx_category` (`category_code`),
  CONSTRAINT `fk_rt_record` FOREIGN KEY (`record_id`) REFERENCES `refine_records` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=427 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提炼目标子表：一次提炼的每个产出目标及其关系';

-- 17. 审查记录表（加工历史）
CREATE TABLE review_records (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '审查记录主键',
  `review_date` date NOT NULL COMMENT '审查日期',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '审查标题',
  `method` text COLLATE utf8mb4_unicode_ci COMMENT '审查方法（vault_review.py 指标等）',
  `meta` json DEFAULT NULL COMMENT '审查元信息（范围/文件数/工具/对比基线/原则）',
  `main_problems` json DEFAULT NULL COMMENT '主要问题数组',
  `groups` json DEFAULT NULL COMMENT '审查分组（s_groups + c_groups 合并，通用分组）',
  `summary` text COLLATE utf8mb4_unicode_ci COMMENT '审查总结',
  `recycle` json DEFAULT NULL COMMENT '待回收处置（done/cooling/doneHist/rows）',
  `actions` json DEFAULT NULL COMMENT '建议动作表（num/text/status）',
  `saved_at` bigint NOT NULL DEFAULT '0' COMMENT '落库时间戳（毫秒）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_date` (`review_date`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审查记录表：一次全库审查报告（加工历史，展示用）';

-- 18. 审查检查项子表（1 审查 → N 检查项）
CREATE TABLE review_checks (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '检查项主键',
  `review_id` bigint unsigned NOT NULL COMMENT '审查记录外键，关联 review_records.id',
  `item_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '检查项名称（如 frontmatter 缺失）',
  `result` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '检查结果值（数值或文本）',
  `compare` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '对比基准值',
  `status_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态码值，关联 dict_check_status.code（pass/warn/fail）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_review` (`review_id`),
  KEY `idx_status` (`status_code`),
  CONSTRAINT `fk_rc_review` FOREIGN KEY (`review_id`) REFERENCES `review_records` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审查检查项子表：每条审查的逐项检查结论';

-- 19. 粗制品状态表（加工历史/状态）
CREATE TABLE coarse_records (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '粗制品主键',
  `rel` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '粗制品相对路径（唯一业务键）',
  `status_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '状态码值，关联 dict_coarse_status.code',
  `score` int DEFAULT NULL COMMENT '质量评分（0-100，已评分才有）',
  `score_reason` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '评分理由',
  `scored_at` bigint DEFAULT NULL COMMENT '评分时间戳（毫秒）',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '加工后标题',
  `processed_at` bigint DEFAULT NULL COMMENT '加工时间戳（毫秒）',
  `processed_to` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '加工产物路径（原始资源）',
  `output_preview` text COLLATE utf8mb4_unicode_ci COMMENT '加工输出预览（前 600 字）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rel` (`rel`),
  KEY `idx_status` (`status_code`)
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='粗制品状态表：粗制品的评分/加工状态（状态 + 加工历史）';

-- 20. 回收站表
CREATE TABLE trash_records (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '回收站主键',
  `rel` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '被回收文件相对路径（唯一）',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '回收状态：pending=待删除(冷静期) trash=已删除',
  `deleted_at` bigint DEFAULT NULL COMMENT '回收时间戳（毫秒）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rel` (`rel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='回收站表：删除/回收的文件登记';

-- 21. 同步元数据表（vault 扫描版本控制）
CREATE TABLE sync_state (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `sync_key` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '同步键（如 last_scan_mtime）',
  `sync_value` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '同步值',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_key` (`sync_key`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同步元数据表：vault 增量扫描的版本/游标控制';

-- 22. 预测主题表（预测段落：个股/行业/市场）
CREATE TABLE prediction_subjects (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主题主键',
  `console_type_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '控制台类型码值，关联 dict_console_type.code',
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '主题名（贵州茅台/白酒/A股）',
  `code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '个股代码（600519/00700/MU；行业市场为 NULL）',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '段落顺序',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `market` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '市场码值 sh/sz/hk/kr/us（2026-09-01 迁移新增）',
  `hk_connect` tinyint(1) DEFAULT NULL COMMENT '是否港股通标的 1是0否NULL非港股/未知',
  `enabled` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否在控制台列表显示：0=停用隐藏（认知类误建主题用此项下架，不删行，可回退）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_console_name` (`console_type_code`,`name`)
) ENGINE=InnoDB AUTO_INCREMENT=429 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预测主题：预测段落（个股/行业/市场）';

-- 23. 预测记录表（每个主题下的预测条目）
CREATE TABLE prediction_records (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '预测主键',
  `subject_id` bigint unsigned NOT NULL COMMENT '主题外键，关联 prediction_subjects.id',
  `predict_date` date NOT NULL COMMENT '预测日期（原始判断日；月级精度存当月 1 日）',
  `date_precision` enum('day','month') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'day' COMMENT '日期精度：day=精确到日 / month=仅到月（展示还原为 yyyy-MM）',
  `predictor` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '预测人（博主名或自己）',
  `ref_price` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '当前价/参考价（保留原文表述，如 ¥1341.99 / 上证3804.69）',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '预测内容（保留原文关键表述）',
  `target_price` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标价（无则 NULL）',
  `target_date` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标日期（允许区间，如 2023~2027+）',
  `source_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '原文链接',
  `status_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态码值，关联 dict_prediction_status.code',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `origin_kind` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'manual' COMMENT '来源：manual=手工录入 statement=言论 trade=买卖记录',
  `origin_id` bigint unsigned DEFAULT NULL COMMENT 'origin_kind 对应的源记录 id（blogger_statements.id / blogger_trades.id）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`subject_id`,`predict_date`,`predictor`,`content`(64)),
  KEY `idx_subject` (`subject_id`),
  KEY `idx_status` (`status_code`),
  KEY `idx_origin` (`origin_kind`,`origin_id`),
  CONSTRAINT `fk_p_subject` FOREIGN KEY (`subject_id`) REFERENCES `prediction_subjects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预测记录：每个主题下的预测条目';

-- 24. 言论跟踪表（段落级增强/反驳/中性言论）
CREATE TABLE prediction_tracks (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '言论主键',
  `subject_id` bigint unsigned NOT NULL COMMENT '主题外键，关联 prediction_subjects.id',
  `track_date` date DEFAULT NULL COMMENT '言论日期',
  `source` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源（博主名或自己）',
  `content` text COLLATE utf8mb4_unicode_ci COMMENT '观点/事件',
  `direction_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '方向码值，关联 dict_track_direction.code',
  `source_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '原文链接',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `migrated_to_statement_id` bigint unsigned DEFAULT NULL COMMENT '已迁回 blogger_statements 的行 id；非空即视为 legacy 已归位，控制台不再展示（不删行，可回退）',
  `migrated_at` datetime DEFAULT NULL COMMENT '迁回时间，供回退与审计',
  PRIMARY KEY (`id`),
  KEY `idx_subject` (`subject_id`),
  KEY `idx_direction` (`direction_code`),
  CONSTRAINT `fk_pt_subject` FOREIGN KEY (`subject_id`) REFERENCES `prediction_subjects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=845 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='言论跟踪：段落级增强/反驳/中性言论';

-- 25. 预测验证记录表（一条预测至多一条验证结论）
CREATE TABLE prediction_verifications (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '验证主键',
  `prediction_id` bigint unsigned NOT NULL COMMENT '预测外键，关联 predictions.id',
  `verify_date` date DEFAULT NULL COMMENT '验证日期',
  `verifier` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '验证人（自己/数据来源）',
  `basis` text COLLATE utf8mb4_unicode_ci COMMENT '验证依据（量化证据：实际数据/价格走势/同期对比）',
  `result_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '结果码值，关联 dict_verify_result.code',
  `note` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注（方向与幅度偏差说明）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_prediction` (`prediction_id`),
  KEY `idx_result` (`result_code`),
  CONSTRAINT `fk_pv_prediction` FOREIGN KEY (`prediction_id`) REFERENCES `prediction_records` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预测验证记录：一条预测至多一条验证结论';

-- ============ 三、看板首页与言论追踪（2026-09 新增） ============

-- 26. 博主言论分表（2026-09-08 按类型拆分 / 2026-09-10 分型改造新增专属列）
-- 分类权威 = content_type 六分法；blogger_statements 为只读 UNION ALL 视图（38 列，非本类型列补 NULL）
-- 分型专属列：trade→op/price/market_cap/trade_date；predict→ref_price/target_price/target_date/date_precision/verify_status/verify_date/verify_result
--             research→data_refs；insight→transferable；**wiki_ref 六表统一**（2026-09-11：标记已具象化到哪个框架条目，卡片显示「已具象化：[[…]]」）；**reply_to 六表统一**（2026-09-11：回应的对方原话/话题独立成字段，正文只放博主自己的话）；全类型共有 form（帖子形态：回复/短文/长文/专栏）
-- 旧 kind 字段（concrete/view/signal/interaction 四类落位）已于 2026-09-10 退役，仅保留历史值

CREATE TABLE stmt_view (
  `id` bigint unsigned NOT NULL COMMENT '言论全局 id（由 stmt_id_seq 发号，跨六张 stmt_* 表唯一；改类型=跨表搬行 id 不变）',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名（冗余自 bloggers.name，免 join）',
  `kind` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '【已退役 2026-09-10】旧四类落位（concrete/view/signal/interaction）；分类权威=content_type',
  `stmt_date` date DEFAULT NULL COMMENT '记录日期（历史列；排序/展示请用 COALESCE(view_date, post_date)）',
  `post_date` date DEFAULT NULL COMMENT '发帖时间（帖子上屏日期）',
  `view_date` date DEFAULT NULL COMMENT '观点时间（该判断成立时点；默认等于 post_date）',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted=同发帖 / explicit=原文自述 / derived=推算',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间为推算值(derived)时的原文依据',
  `stance` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号/方向：bullish看多/bearish看空/short_bullish短期看多/short_bearish短期看空/long_bullish长期看多/long_bearish长期看空/neutral中性（2026-09-11 扩展；所有类型均可填，无则不显示）',
  `target` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '标的/行业（名称(代码)，如 长城汽车(02333)）',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文＝博主言论提炼（只写博主自己的话；回应另存 reply_to，不含流程性标记）',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容＝具体结论（≤25 字，不带方向词前缀；与 stance 合成「方向 · 内容」）',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源（雪球 / 雪球回复 / 微信 等）',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接（规则 #35：必填且可回溯到原帖）',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '→ bloggers.id（博主；不传则该条不进博主维度统计）',
  `subject_id` bigint unsigned DEFAULT NULL COMMENT '→ prediction_subjects.id（言论追踪控制台主题；主题删除后悬空值会被置空）',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源粗制品/原始资源文件相对路径（vault 内）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否标记待复核：1=是 0=否',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键 md5(blogger_id|post_date|正文)，防同帖重复落库',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
  `form` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏（采集侧判定，refine 零解析读取）',
  `wiki_ref` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目名（2026-09-11 六表统一）',
  `reply_to` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '回应的对方原话/话题（2026-09-11 字段化：不再内嵌在正文里）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_subject` (`subject_id`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主言论·观点（六分法分表；blogger_statements 为只读 UNION 视图）';

CREATE TABLE stmt_research (
  `id` bigint unsigned NOT NULL COMMENT '言论全局 id（由 stmt_id_seq 发号，跨六张 stmt_* 表唯一；改类型=跨表搬行 id 不变）',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名（冗余自 bloggers.name，免 join）',
  `kind` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '【已退役 2026-09-10】旧四类落位（concrete/view/signal/interaction）；分类权威=content_type',
  `stmt_date` date DEFAULT NULL COMMENT '记录日期（历史列；排序/展示请用 COALESCE(view_date, post_date)）',
  `post_date` date DEFAULT NULL COMMENT '发帖时间（帖子上屏日期）',
  `view_date` date DEFAULT NULL COMMENT '观点时间（该判断成立时点；默认等于 post_date）',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted=同发帖 / explicit=原文自述 / derived=推算',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间为推算值(derived)时的原文依据',
  `stance` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号/方向：bullish看多/bearish看空/short_bullish短期看多/short_bearish短期看空/long_bullish长期看多/long_bearish长期看空/neutral中性（2026-09-11 扩展；所有类型均可填，无则不显示）',
  `target` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '标的/行业（名称(代码)，如 长城汽车(02333)）',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文＝博主言论提炼（只写博主自己的话；回应另存 reply_to，不含流程性标记）',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容＝具体结论（≤25 字，不带方向词前缀；与 stance 合成「方向 · 内容」）',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源（雪球 / 雪球回复 / 微信 等）',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接（规则 #35：必填且可回溯到原帖）',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '→ bloggers.id（博主；不传则该条不进博主维度统计）',
  `subject_id` bigint unsigned DEFAULT NULL COMMENT '→ prediction_subjects.id（言论追踪控制台主题；主题删除后悬空值会被置空）',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源粗制品/原始资源文件相对路径（vault 内）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否标记待复核：1=是 0=否',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键 md5(blogger_id|post_date|正文)，防同帖重复落库',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
  `form` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏（采集侧判定，refine 零解析读取）',
  `data_refs` text COLLATE utf8mb4_unicode_ci COMMENT '研究数据来源（公告/财报/调研等）',
  `wiki_ref` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目名（可空）',
  `reply_to` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '回应的对方原话/话题（2026-09-11 字段化：不再内嵌在正文里）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_subject` (`subject_id`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主言论·研究（六分法分表）';

CREATE TABLE stmt_predict (
  `id` bigint unsigned NOT NULL COMMENT '言论全局 id（由 stmt_id_seq 发号，跨六张 stmt_* 表唯一；改类型=跨表搬行 id 不变）',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名（冗余自 bloggers.name，免 join）',
  `kind` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '【已退役 2026-09-10】旧四类落位（concrete/view/signal/interaction）；分类权威=content_type',
  `stmt_date` date DEFAULT NULL COMMENT '记录日期（历史列；排序/展示请用 COALESCE(view_date, post_date)）',
  `post_date` date DEFAULT NULL COMMENT '发帖时间（帖子上屏日期）',
  `view_date` date DEFAULT NULL COMMENT '观点时间（该判断成立时点；默认等于 post_date）',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted=同发帖 / explicit=原文自述 / derived=推算',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间为推算值(derived)时的原文依据',
  `stance` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号/方向：bullish看多/bearish看空/short_bullish短期看多/short_bearish短期看空/long_bullish长期看多/long_bearish长期看空/neutral中性（2026-09-11 扩展；所有类型均可填，无则不显示）',
  `target` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '标的/行业（名称(代码)，如 长城汽车(02333)）',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文＝博主言论提炼（只写博主自己的话；回应另存 reply_to，不含流程性标记）',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容＝具体结论（≤25 字，不带方向词前缀；与 stance 合成「方向 · 内容」）',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源（雪球 / 雪球回复 / 微信 等）',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接（规则 #35：必填且可回溯到原帖）',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '→ bloggers.id（博主；不传则该条不进博主维度统计）',
  `subject_id` bigint unsigned DEFAULT NULL COMMENT '→ prediction_subjects.id（言论追踪控制台主题；主题删除后悬空值会被置空）',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源粗制品/原始资源文件相对路径（vault 内）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否标记待复核：1=是 0=否',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键 md5(blogger_id|post_date|正文)，防同帖重复落库',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
  `form` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏（采集侧判定，refine 零解析读取）',
  `ref_price` decimal(16,4) DEFAULT NULL COMMENT '判断时参考价',
  `target_price` decimal(16,4) DEFAULT NULL COMMENT '目标价',
  `target_date` date DEFAULT NULL COMMENT '目标时间',
  `date_precision` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '时间精度：day/month/year',
  `verify_status` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '验证状态：pending/verified/revoked',
  `verify_date` date DEFAULT NULL COMMENT '验证日期',
  `verify_result` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '验证结果：hit/miss/partial',
  `wiki_ref` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目名（2026-09-11 六表统一）',
  `reply_to` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '回应的对方原话/话题（2026-09-11 字段化：不再内嵌在正文里）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_subject` (`subject_id`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主言论·预测记录（六分法分表；验证闭环字段 ref_price/target_price/verify_* 仅本表有）';

CREATE TABLE stmt_trade_src (
  `id` bigint unsigned NOT NULL COMMENT '言论全局 id（由 stmt_id_seq 发号，跨六张 stmt_* 表唯一；改类型=跨表搬行 id 不变）',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名（冗余自 bloggers.name，免 join）',
  `kind` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '【已退役 2026-09-10】旧四类落位（concrete/view/signal/interaction）；分类权威=content_type',
  `stmt_date` date DEFAULT NULL COMMENT '记录日期（历史列；排序/展示请用 COALESCE(view_date, post_date)）',
  `post_date` date DEFAULT NULL COMMENT '发帖时间（帖子上屏日期）',
  `view_date` date DEFAULT NULL COMMENT '观点时间（该判断成立时点；默认等于 post_date）',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted=同发帖 / explicit=原文自述 / derived=推算',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间为推算值(derived)时的原文依据',
  `stance` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号/方向：bullish看多/bearish看空/short_bullish短期看多/short_bearish短期看空/long_bullish长期看多/long_bearish长期看空/neutral中性（2026-09-11 扩展；所有类型均可填，无则不显示）',
  `target` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '标的/行业（名称(代码)，如 长城汽车(02333)）',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文＝博主言论提炼（只写博主自己的话；回应另存 reply_to，不含流程性标记）',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容＝具体结论（≤25 字，不带方向词前缀；与 stance 合成「方向 · 内容」）',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源（雪球 / 雪球回复 / 微信 等）',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接（规则 #35：必填且可回溯到原帖）',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '→ bloggers.id（博主；不传则该条不进博主维度统计）',
  `subject_id` bigint unsigned DEFAULT NULL COMMENT '→ prediction_subjects.id（言论追踪控制台主题；主题删除后悬空值会被置空）',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源粗制品/原始资源文件相对路径（vault 内）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否标记待复核：1=是 0=否',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键 md5(blogger_id|post_date|正文)，防同帖重复落库',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
  `form` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏（采集侧判定，refine 零解析读取）',
  `op` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作：buy/sell/add/reduce',
  `price` decimal(16,4) DEFAULT NULL COMMENT '成交价（博主自述价）',
  `market_cap` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '提及市值（原文表述）',
  `trade_date` date DEFAULT NULL COMMENT '操作日期',
  `wiki_ref` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目名（2026-09-11 六表统一）',
  `reply_to` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '回应的对方原话/话题（2026-09-11 字段化：不再内嵌在正文里）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_subject` (`subject_id`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主言论·买卖记录来源言论（六分法分表；结构化交易另见 blogger_trades）';

CREATE TABLE stmt_insight (
  `id` bigint unsigned NOT NULL COMMENT '言论全局 id（由 stmt_id_seq 发号，跨六张 stmt_* 表唯一；改类型=跨表搬行 id 不变）',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名（冗余自 bloggers.name，免 join）',
  `kind` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '【已退役 2026-09-10】旧四类落位（concrete/view/signal/interaction）；分类权威=content_type',
  `stmt_date` date DEFAULT NULL COMMENT '记录日期（历史列；排序/展示请用 COALESCE(view_date, post_date)）',
  `post_date` date DEFAULT NULL COMMENT '发帖时间（帖子上屏日期）',
  `view_date` date DEFAULT NULL COMMENT '观点时间（该判断成立时点；默认等于 post_date）',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted=同发帖 / explicit=原文自述 / derived=推算',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间为推算值(derived)时的原文依据',
  `stance` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号/方向：bullish看多/bearish看空/short_bullish短期看多/short_bearish短期看空/long_bullish长期看多/long_bearish长期看空/neutral中性（2026-09-11 扩展；所有类型均可填，无则不显示）',
  `target` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '标的/行业（名称(代码)，如 长城汽车(02333)）',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文＝博主言论提炼（只写博主自己的话；回应另存 reply_to，不含流程性标记）',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容＝具体结论（≤25 字，不带方向词前缀；与 stance 合成「方向 · 内容」）',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源（雪球 / 雪球回复 / 微信 等）',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接（规则 #35：必填且可回溯到原帖）',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '→ bloggers.id（博主；不传则该条不进博主维度统计）',
  `subject_id` bigint unsigned DEFAULT NULL COMMENT '→ prediction_subjects.id（言论追踪控制台主题；主题删除后悬空值会被置空）',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源粗制品/原始资源文件相对路径（vault 内）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否标记待复核：1=是 0=否',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键 md5(blogger_id|post_date|正文)，防同帖重复落库',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
  `form` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏（采集侧判定，refine 零解析读取）',
  `transferable` tinyint(1) DEFAULT NULL COMMENT '是否具可迁移性（1=可复用方法论）',
  `wiki_ref` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目名（可空）',
  `reply_to` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '回应的对方原话/话题（2026-09-11 字段化：不再内嵌在正文里）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_subject` (`subject_id`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主言论·心得总结（六分法分表；transferable 可迁移性仅本表有）';

CREATE TABLE stmt_chat (
  `id` bigint unsigned NOT NULL COMMENT '言论全局 id（由 stmt_id_seq 发号，跨六张 stmt_* 表唯一；改类型=跨表搬行 id 不变）',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名（冗余自 bloggers.name，免 join）',
  `kind` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '【已退役 2026-09-10】旧四类落位（concrete/view/signal/interaction）；分类权威=content_type',
  `stmt_date` date DEFAULT NULL COMMENT '记录日期（历史列；排序/展示请用 COALESCE(view_date, post_date)）',
  `post_date` date DEFAULT NULL COMMENT '发帖时间（帖子上屏日期）',
  `view_date` date DEFAULT NULL COMMENT '观点时间（该判断成立时点；默认等于 post_date）',
  `view_date_source` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间来源：as_posted=同发帖 / explicit=原文自述 / derived=推算',
  `view_date_precision` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间精度：day/month/year',
  `view_date_basis` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '观点时间为推算值(derived)时的原文依据',
  `stance` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信号/方向：bullish看多/bearish看空/short_bullish短期看多/short_bearish短期看空/long_bullish长期看多/long_bearish长期看空/neutral中性（2026-09-11 扩展；所有类型均可填，无则不显示）',
  `target` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '标的/行业（名称(代码)，如 长城汽车(02333)）',
  `view_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '正文＝博主言论提炼（只写博主自己的话；回应另存 reply_to，不含流程性标记）',
  `signal_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '信号内容＝具体结论（≤25 字，不带方向词前缀；与 stance 合成「方向 · 内容」）',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源（雪球 / 雪球回复 / 微信 等）',
  `source_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接（规则 #35：必填且可回溯到原帖）',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '→ bloggers.id（博主；不传则该条不进博主维度统计）',
  `subject_id` bigint unsigned DEFAULT NULL COMMENT '→ prediction_subjects.id（言论追踪控制台主题；主题删除后悬空值会被置空）',
  `src_rel` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源粗制品/原始资源文件相对路径（vault 内）',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否标记待复核：1=是 0=否',
  `dedup_key` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '去重键 md5(blogger_id|post_date|正文)，防同帖重复落库',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
  `form` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏（采集侧判定，refine 零解析读取）',
  `wiki_ref` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已具象化的框架条目名（2026-09-11 六表统一）',
  `reply_to` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '回应的对方原话/话题（2026-09-11 字段化：不再内嵌在正文里）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_date` (`blogger`,`view_date`),
  KEY `idx_subject` (`subject_id`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主言论·闲聊（六分法分表）';

-- 27. 博主言论统一视图（只读 UNION ALL，承接全部查询；写操作按类型路由到上表）
CREATE ALGORITHM=UNDEFINED DEFINER=`jianglb`@`%` SQL SECURITY DEFINER VIEW `blogger_statements` AS select `stmt_research`.`id` AS `id`,`stmt_research`.`blogger` AS `blogger`,`stmt_research`.`kind` AS `kind`,`stmt_research`.`stmt_date` AS `stmt_date`,`stmt_research`.`post_date` AS `post_date`,`stmt_research`.`view_date` AS `view_date`,`stmt_research`.`view_date_source` AS `view_date_source`,`stmt_research`.`view_date_precision` AS `view_date_precision`,`stmt_research`.`view_date_basis` AS `view_date_basis`,`stmt_research`.`stance` AS `stance`,`stmt_research`.`target` AS `target`,`stmt_research`.`view_text` AS `view_text`,`stmt_research`.`signal_text` AS `signal_text`,`stmt_research`.`source` AS `source`,`stmt_research`.`source_url` AS `source_url`,`stmt_research`.`blogger_id` AS `blogger_id`,`stmt_research`.`subject_id` AS `subject_id`,`stmt_research`.`src_rel` AS `src_rel`,`stmt_research`.`review_required` AS `review_required`,`stmt_research`.`dedup_key` AS `dedup_key`,`stmt_research`.`created_at` AS `created_at`,`stmt_research`.`updated_at` AS `updated_at`,`stmt_research`.`form` AS `form`,NULL AS `op`,NULL AS `price`,NULL AS `market_cap`,NULL AS `trade_date`,NULL AS `ref_price`,NULL AS `target_price`,NULL AS `target_date`,NULL AS `date_precision`,NULL AS `verify_status`,NULL AS `verify_date`,NULL AS `verify_result`,`stmt_research`.`data_refs` AS `data_refs`,`stmt_research`.`wiki_ref` AS `wiki_ref`,`stmt_research`.`reply_to` AS `reply_to`,NULL AS `transferable`,'research' AS `content_type` from `stmt_research` union all select `stmt_predict`.`id` AS `id`,`stmt_predict`.`blogger` AS `blogger`,`stmt_predict`.`kind` AS `kind`,`stmt_predict`.`stmt_date` AS `stmt_date`,`stmt_predict`.`post_date` AS `post_date`,`stmt_predict`.`view_date` AS `view_date`,`stmt_predict`.`view_date_source` AS `view_date_source`,`stmt_predict`.`view_date_precision` AS `view_date_precision`,`stmt_predict`.`view_date_basis` AS `view_date_basis`,`stmt_predict`.`stance` AS `stance`,`stmt_predict`.`target` AS `target`,`stmt_predict`.`view_text` AS `view_text`,`stmt_predict`.`signal_text` AS `signal_text`,`stmt_predict`.`source` AS `source`,`stmt_predict`.`source_url` AS `source_url`,`stmt_predict`.`blogger_id` AS `blogger_id`,`stmt_predict`.`subject_id` AS `subject_id`,`stmt_predict`.`src_rel` AS `src_rel`,`stmt_predict`.`review_required` AS `review_required`,`stmt_predict`.`dedup_key` AS `dedup_key`,`stmt_predict`.`created_at` AS `created_at`,`stmt_predict`.`updated_at` AS `updated_at`,`stmt_predict`.`form` AS `form`,NULL AS `op`,NULL AS `price`,NULL AS `market_cap`,NULL AS `trade_date`,`stmt_predict`.`ref_price` AS `ref_price`,`stmt_predict`.`target_price` AS `target_price`,`stmt_predict`.`target_date` AS `target_date`,`stmt_predict`.`date_precision` AS `date_precision`,`stmt_predict`.`verify_status` AS `verify_status`,`stmt_predict`.`verify_date` AS `verify_date`,`stmt_predict`.`verify_result` AS `verify_result`,NULL AS `data_refs`,`stmt_predict`.`wiki_ref` AS `wiki_ref`,`stmt_predict`.`reply_to` AS `reply_to`,NULL AS `transferable`,'predict' AS `content_type` from `stmt_predict` union all select `stmt_view`.`id` AS `id`,`stmt_view`.`blogger` AS `blogger`,`stmt_view`.`kind` AS `kind`,`stmt_view`.`stmt_date` AS `stmt_date`,`stmt_view`.`post_date` AS `post_date`,`stmt_view`.`view_date` AS `view_date`,`stmt_view`.`view_date_source` AS `view_date_source`,`stmt_view`.`view_date_precision` AS `view_date_precision`,`stmt_view`.`view_date_basis` AS `view_date_basis`,`stmt_view`.`stance` AS `stance`,`stmt_view`.`target` AS `target`,`stmt_view`.`view_text` AS `view_text`,`stmt_view`.`signal_text` AS `signal_text`,`stmt_view`.`source` AS `source`,`stmt_view`.`source_url` AS `source_url`,`stmt_view`.`blogger_id` AS `blogger_id`,`stmt_view`.`subject_id` AS `subject_id`,`stmt_view`.`src_rel` AS `src_rel`,`stmt_view`.`review_required` AS `review_required`,`stmt_view`.`dedup_key` AS `dedup_key`,`stmt_view`.`created_at` AS `created_at`,`stmt_view`.`updated_at` AS `updated_at`,`stmt_view`.`form` AS `form`,NULL AS `op`,NULL AS `price`,NULL AS `market_cap`,NULL AS `trade_date`,NULL AS `ref_price`,NULL AS `target_price`,NULL AS `target_date`,NULL AS `date_precision`,NULL AS `verify_status`,NULL AS `verify_date`,NULL AS `verify_result`,NULL AS `data_refs`,`stmt_view`.`wiki_ref` AS `wiki_ref`,`stmt_view`.`reply_to` AS `reply_to`,NULL AS `transferable`,'view' AS `content_type` from `stmt_view` union all select `stmt_insight`.`id` AS `id`,`stmt_insight`.`blogger` AS `blogger`,`stmt_insight`.`kind` AS `kind`,`stmt_insight`.`stmt_date` AS `stmt_date`,`stmt_insight`.`post_date` AS `post_date`,`stmt_insight`.`view_date` AS `view_date`,`stmt_insight`.`view_date_source` AS `view_date_source`,`stmt_insight`.`view_date_precision` AS `view_date_precision`,`stmt_insight`.`view_date_basis` AS `view_date_basis`,`stmt_insight`.`stance` AS `stance`,`stmt_insight`.`target` AS `target`,`stmt_insight`.`view_text` AS `view_text`,`stmt_insight`.`signal_text` AS `signal_text`,`stmt_insight`.`source` AS `source`,`stmt_insight`.`source_url` AS `source_url`,`stmt_insight`.`blogger_id` AS `blogger_id`,`stmt_insight`.`subject_id` AS `subject_id`,`stmt_insight`.`src_rel` AS `src_rel`,`stmt_insight`.`review_required` AS `review_required`,`stmt_insight`.`dedup_key` AS `dedup_key`,`stmt_insight`.`created_at` AS `created_at`,`stmt_insight`.`updated_at` AS `updated_at`,`stmt_insight`.`form` AS `form`,NULL AS `op`,NULL AS `price`,NULL AS `market_cap`,NULL AS `trade_date`,NULL AS `ref_price`,NULL AS `target_price`,NULL AS `target_date`,NULL AS `date_precision`,NULL AS `verify_status`,NULL AS `verify_date`,NULL AS `verify_result`,NULL AS `data_refs`,`stmt_insight`.`wiki_ref` AS `wiki_ref`,`stmt_insight`.`reply_to` AS `reply_to`,`stmt_insight`.`transferable` AS `transferable`,'insight' AS `content_type` from `stmt_insight` union all select `stmt_chat`.`id` AS `id`,`stmt_chat`.`blogger` AS `blogger`,`stmt_chat`.`kind` AS `kind`,`stmt_chat`.`stmt_date` AS `stmt_date`,`stmt_chat`.`post_date` AS `post_date`,`stmt_chat`.`view_date` AS `view_date`,`stmt_chat`.`view_date_source` AS `view_date_source`,`stmt_chat`.`view_date_precision` AS `view_date_precision`,`stmt_chat`.`view_date_basis` AS `view_date_basis`,`stmt_chat`.`stance` AS `stance`,`stmt_chat`.`target` AS `target`,`stmt_chat`.`view_text` AS `view_text`,`stmt_chat`.`signal_text` AS `signal_text`,`stmt_chat`.`source` AS `source`,`stmt_chat`.`source_url` AS `source_url`,`stmt_chat`.`blogger_id` AS `blogger_id`,`stmt_chat`.`subject_id` AS `subject_id`,`stmt_chat`.`src_rel` AS `src_rel`,`stmt_chat`.`review_required` AS `review_required`,`stmt_chat`.`dedup_key` AS `dedup_key`,`stmt_chat`.`created_at` AS `created_at`,`stmt_chat`.`updated_at` AS `updated_at`,`stmt_chat`.`form` AS `form`,NULL AS `op`,NULL AS `price`,NULL AS `market_cap`,NULL AS `trade_date`,NULL AS `ref_price`,NULL AS `target_price`,NULL AS `target_date`,NULL AS `date_precision`,NULL AS `verify_status`,NULL AS `verify_date`,NULL AS `verify_result`,NULL AS `data_refs`,`stmt_chat`.`wiki_ref` AS `wiki_ref`,`stmt_chat`.`reply_to` AS `reply_to`,NULL AS `transferable`,'chat' AS `content_type` from `stmt_chat` union all select `stmt_trade_src`.`id` AS `id`,`stmt_trade_src`.`blogger` AS `blogger`,`stmt_trade_src`.`kind` AS `kind`,`stmt_trade_src`.`stmt_date` AS `stmt_date`,`stmt_trade_src`.`post_date` AS `post_date`,`stmt_trade_src`.`view_date` AS `view_date`,`stmt_trade_src`.`view_date_source` AS `view_date_source`,`stmt_trade_src`.`view_date_precision` AS `view_date_precision`,`stmt_trade_src`.`view_date_basis` AS `view_date_basis`,`stmt_trade_src`.`stance` AS `stance`,`stmt_trade_src`.`target` AS `target`,`stmt_trade_src`.`view_text` AS `view_text`,`stmt_trade_src`.`signal_text` AS `signal_text`,`stmt_trade_src`.`source` AS `source`,`stmt_trade_src`.`source_url` AS `source_url`,`stmt_trade_src`.`blogger_id` AS `blogger_id`,`stmt_trade_src`.`subject_id` AS `subject_id`,`stmt_trade_src`.`src_rel` AS `src_rel`,`stmt_trade_src`.`review_required` AS `review_required`,`stmt_trade_src`.`dedup_key` AS `dedup_key`,`stmt_trade_src`.`created_at` AS `created_at`,`stmt_trade_src`.`updated_at` AS `updated_at`,`stmt_trade_src`.`form` AS `form`,`stmt_trade_src`.`op` AS `op`,`stmt_trade_src`.`price` AS `price`,`stmt_trade_src`.`market_cap` AS `market_cap`,`stmt_trade_src`.`trade_date` AS `trade_date`,NULL AS `ref_price`,NULL AS `target_price`,NULL AS `target_date`,NULL AS `date_precision`,NULL AS `verify_status`,NULL AS `verify_date`,NULL AS `verify_result`,NULL AS `data_refs`,`stmt_trade_src`.`wiki_ref` AS `wiki_ref`,`stmt_trade_src`.`reply_to` AS `reply_to`,NULL AS `transferable`,'trade' AS `content_type` from `stmt_trade_src`;

-- 28. 首页待办表
CREATE TABLE todos (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `content` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '待办内容',
  `due_date` date DEFAULT NULL COMMENT '计划完成日期（纯日期），NULL 表示未定；2026-09-04 由 due_time DATETIME 改制',
  `done` tinyint NOT NULL DEFAULT '0' COMMENT '完成标记：0=未完成，1=已完成',
  `done_at` datetime DEFAULT NULL COMMENT '完成时间，未完成为 NULL',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '手工排序序号，越小越靠前',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='首页待办表：看板首页 todo 清单（录入/勾选/排序）';

-- 29. 首页语录表
CREATE TABLE quotes (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `seq` int NOT NULL COMMENT '语录序号，决定展示顺序',
  `text` varchar(300) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '语录正文',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `seq` (`seq`)
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='首页语录表：轮播展示的激励语录，初始化时一次性灌入';

-- ── 帖子原文库（2026-09-11 用户决策：单表 + blogger_id 识别博主；唯一用途=避免重采）──
CREATE TABLE post_history (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `blogger_id` bigint unsigned NOT NULL COMMENT '博主 id（分博主识别字段）→ bloggers.id',
  `blogger` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名（冗余，免 join）',
  `platform_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '平台码 dict.platform（xueqiu/xiaohongshu/douyin）',
  `platform_post_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '平台内帖子 id（雪球为 URL 末段）',
  `source_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '原文链接',
  `url_hash` char(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'md5(source_url)：唯一键（varchar(500) 整列做唯一键过重）',
  `title` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '标题（专栏/长文；短文为空）',
  `raw_text` mediumtext COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '采集到的原文全文（提炼前，保留 //@ 等原始结构）',
  `raw_text_len` int unsigned NOT NULL DEFAULT '0' COMMENT '原文字符数',
  `form` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '帖子形态：回复/短文/长文/专栏',
  `posted_at` datetime NOT NULL COMMENT '发帖时间',
  `edited_at` datetime DEFAULT NULL COMMENT '平台侧最后编辑时间（有值=原文被改过）',
  `fetched_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
  `content_hash` char(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'md5(raw_text)：内容指纹，重采时比对是否变过',
  `reply_count` int unsigned DEFAULT NULL COMMENT '采集时评论数',
  `retweet_count` int unsigned DEFAULT NULL COMMENT '采集时转发数',
  `like_count` int unsigned DEFAULT NULL COMMENT '采集时点赞数',
  `fetch_method` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'timeline/show_json/detail_page/manual',
  `src_rel` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源批次文件 rel（工作区/粗制品/…）',
  `collector` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '采集工具与版本',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_url` (`url_hash`),
  UNIQUE KEY `uk_blogger_post` (`blogger_id`,`platform_post_id`),
  KEY `idx_blogger_time` (`blogger_id`,`posted_at`),
  KEY `idx_posted` (`posted_at`),
  KEY `idx_platform` (`platform_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主帖子原文库（采集留档：避免重采 / 可按原文重新提炼）';

-- ============ 四、补录（2026-09-11：以下 4 张表此前未入文件，现按实库补齐） ============

-- blogger_trades
CREATE TABLE blogger_trades (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `blogger_id` bigint unsigned NOT NULL COMMENT '关联 bloggers.id',
  `statement_id` bigint unsigned DEFAULT NULL COMMENT '来源言论行 id（blogger_statements.id），同一事实双向可追',
  `trade_date` date NOT NULL COMMENT '操作日期（观点时间口径，非发帖日期）',
  `post_date` date DEFAULT NULL COMMENT '发帖时间（该买卖陈述所在帖的发布日）',
  `op` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作：buy=买入 add=加仓 reduce=减仓 sell=卖出 clear=清仓',
  `target_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '标的名称，代称已还原（寒王→寒武纪、赵姨→兆易创新）',
  `target_alias` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '博主原文使用的代称/简写，留痕备查',
  `subject_id` bigint unsigned DEFAULT NULL COMMENT '关联 prediction_subjects.id（展示用；是否生成预测见方案 D2 判定）',
  `price` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '当时价格，口径为开盘竞价位（最贴近开仓成本）',
  `market_cap` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '当时市值',
  `stance` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '方向：bullish=看多 bearish=看空 neutral=中性（规则要求必填识别）',
  `note` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '备注：只记操作理由，不记盘后现象与感受',
  `source_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接',
  `src_rel` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源批次文件 vault 相对路径',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '需人工复核：1=价格/方向/标的存疑',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `blogger` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '博主名（冗余列，与 blogger_statements 同构：画像回写与按名分组以此为键）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_trade` (`blogger_id`,`trade_date`,`op`,`target_name`,`price`),
  KEY `idx_blogger_date` (`blogger_id`,`trade_date`),
  KEY `idx_subject` (`subject_id`),
  KEY `idx_statement` (`statement_id`),
  KEY `idx_blogger_name_date` (`blogger`,`trade_date`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主个股买卖记录：画像「个股买卖记录」表格的结构化落库（MySQL 权威，写库后回写画像段）';

-- statement_reviews
CREATE TABLE statement_reviews (
  `id` int unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `statement_id` int unsigned NOT NULL COMMENT '→ 言论 id（stmt_* 全局 id）；一条言论只保留一条复核建议',
  `blogger` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '博主名（留痕，便于按人筛）',
  `suggestion` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '复核建议正文（用户自然语言，如「这条应是观点·看多，不是预测」）',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'open' COMMENT '处理状态：open=未处理 / applied=已处理',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_stmt` (`statement_id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='言论复核建议（用户在看板「言论追踪」写入，按 statement_id 唯一）';

-- stmt_id_seq
CREATE TABLE stmt_id_seq (
  `name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '序列名（言论 id 发号器标识）',
  `id` bigint unsigned NOT NULL COMMENT '当前已发放到的 id',
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='言论 id 全局发号序列（跨六张 stmt_* 表唯一，改类型搬行仍复用同一 id）';

-- blogger_statements_legacy
CREATE TABLE blogger_statements_legacy (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `blogger` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '博主名，对应 vault 博主目录名',
  `kind` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '言论类型：concrete=具象化，view=观点，signal=信号，interaction=互动',
  `stmt_date` date DEFAULT NULL COMMENT '言论发布日期，原文未标注则为 NULL',
  `target` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '言论涉及标的（个股/行业），无关标的为空串',
  `view_text` text COLLATE utf8mb4_unicode_ci COMMENT '观点原文表述',
  `signal_text` text COLLATE utf8mb4_unicode_ci COMMENT '信号描述（买卖/仓位等可执行信号）',
  `source` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '来源名称（雪球/公众号/小红书等）',
  `source_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '原文链接，无则空串',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `content_type` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '内容六分：research=研究 predict=预测记录（未来走势可验证判断：方向+时间窗/事件条件+目标位） view=观点（当下判断） insight=心得总结 chat=闲聊；trade=买卖记录走 blogger_trades。由提炼环节赋值，2026-09-04 增 predict',
  `post_date` date DEFAULT NULL COMMENT '发帖时间（雪球详情页绝对发布时间，采集环节赋值）',
  `view_date` date DEFAULT NULL COMMENT '观点时间，默认等于 post_date；正文含相对表述时按表述推算',
  `view_date_source` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT 'as_posted' COMMENT '观点时间来源：as_posted=默认同发帖／explicit=原文写明日期／derived=按相对表述推算',
  `view_date_precision` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT 'day' COMMENT '观点时间粒度：day／month／year，取决于表述精度，不假装精确到日',
  `view_date_basis` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '推算依据原文短句（如「三年前我就说过」），供人工回查',
  `stance` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '方向立场：bullish=看多 bearish=看空 neutral=中性（绝对方向，≠tracks 的增强/反驳）',
  `subject_id` bigint unsigned DEFAULT NULL COMMENT '关联 prediction_subjects.id（个股/行业/市场主题），无标的为 NULL',
  `blogger_id` bigint unsigned DEFAULT NULL COMMENT '关联 bloggers.id，取代按博主名文本匹配',
  `src_rel` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '来源批次文件的 vault 相对路径（files.rel/coarse_records.rel），固存字符串防源文件删除后断链',
  `review_required` tinyint(1) NOT NULL DEFAULT '0' COMMENT '需人工复核：1=分类或观点时间存疑',
  `dedup_key` char(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '幂等键 md5(blogger_id|post_date|正文哈希)；仅用采集期字段，保证重复提炼不产生新行',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dedup` (`dedup_key`),
  KEY `idx_blogger_kind` (`blogger`,`kind`,`stmt_date`),
  KEY `idx_blogger_type_date` (`blogger_id`,`content_type`,`view_date`),
  KEY `idx_subject` (`subject_id`),
  KEY `idx_review` (`review_required`)
) ENGINE=InnoDB AUTO_INCREMENT=1480 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主言论表：博主画像「言论追踪」表格的结构化落库（MySQL 权威，写库后回写画像段）';
