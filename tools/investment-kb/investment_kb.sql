-- ============================================================
-- investment_kb: 投资知识库看板派生数据层
-- 架构原则: 本地 vault 为绝对基准（第一/首要/绝对），本库仅为
--           阅读 + 加工总结的派生数据；一切冲突以 vault 为准。
-- 字符集: utf8mb4 / utf8mb4_unicode_ci
-- 约定: 枚举字段一律存码值，逻辑关联统一 dict 码值表（type+code）；主键自增；
--       枚举字段不设外键（dict 为逻辑字典，由应用层/迁移脚本维护）；每表每字段均带 COMMENT。
-- ============================================================
CREATE DATABASE IF NOT EXISTS investment_kb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE investment_kb;

-- ============ 一、码值表（统一字典） ============

-- 1. 统一字典表（合并原 14 张 dict_* 枚举表，主键 (type, code)）
CREATE TABLE dict (
  type       VARCHAR(32)  NOT NULL COMMENT '字典类型：category/check_status/coarse_status/console_type/file_status/file_type/layer/platform/prediction_status/source_type/target_relation/target_type/track_direction/verify_result',
  code       VARCHAR(32)  NOT NULL COMMENT '字典项编码（同 type 内唯一）',
  name       VARCHAR(64)  NOT NULL COMMENT '显示名',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重，越小越靠前',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用：1启用 0停用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (type, code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一字典表：合并原 14 张 dict_* 枚举表（业务表 *_code 逻辑关联，无外键约束）';

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
('verify_result','revoked','已撤销',3,'撤销验证');

-- ============ 二、业务表 ============

-- 11. 博主画像表（vault 扫描派生，vault 为准）
CREATE TABLE bloggers (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '博主主键',
  name         VARCHAR(128)    NOT NULL COMMENT '博主名（唯一）',
  dir          VARCHAR(255)    NOT NULL COMMENT '博主在 vault 中的目录名',
  alias        VARCHAR(255)    DEFAULT NULL COMMENT '别名/曾用名',
  xueqiu_id    VARCHAR(64)     DEFAULT NULL COMMENT '雪球用户 ID（无则 NULL）',
  platform_code VARCHAR(32)    DEFAULT NULL COMMENT '平台码值，关联 dict(type=platform).code（雪球/抖音/小红书）',
  special      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否重点博主：1是 0否',
  summary      TEXT            DEFAULT NULL COMMENT '博主简介（画像摘要）',
  info_cutoff  VARCHAR(64)     DEFAULT NULL COMMENT '信息截止日期（画像信息更新点）',
  file_count   INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '博主产出文件数（vault 扫描统计）',
  created_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  updated_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_name (name),
  KEY idx_platform (platform_code),
  KEY idx_special (special)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主画像表：vault 博主目录扫描派生，冲突以 vault 为准';

-- 12. 标签字典表
CREATE TABLE tags (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '标签主键',
  name       VARCHAR(128)    NOT NULL COMMENT '标签名（唯一，如 行业/传媒/广告营销）',
  created_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签字典表：全库标签去重';

-- 13. wiki 文件索引表（vault 扫描派生，vault 为准）
CREATE TABLE files (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  rel           VARCHAR(512)    NOT NULL COMMENT 'vault 相对路径（唯一业务键）',
  title         VARCHAR(255)    NOT NULL COMMENT '条目标题',
  layer_code    VARCHAR(32)     NOT NULL COMMENT '归属层码值，关联 dict(type=layer).code',
  category_code VARCHAR(32)     DEFAULT NULL COMMENT '分类码值，关联 dict(type=category).code',
  blogger_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '博主外键，关联 bloggers.id（博主层条目归属）',
  author        VARCHAR(128)    DEFAULT NULL COMMENT '作者名',
  type_code     VARCHAR(32)     DEFAULT NULL COMMENT '文件类型码值，关联 dict(type=file_type).code',
  status_code   VARCHAR(32)     DEFAULT NULL COMMENT '状态码值，关联 dict(type=file_status).code',
  star          TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否关注：1是 0否（我的关注列表）',
  size_bytes    INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '文件大小（字节）',
  mtime         BIGINT          NOT NULL DEFAULT 0 COMMENT '文件修改时间戳（毫秒，vault 增量同步依据）',
  create_date   DATE            DEFAULT NULL COMMENT '创建日期（frontmatter 解析）',
  update_date   DATE            DEFAULT NULL COMMENT '更新日期（frontmatter 解析）',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_rel (rel),
  KEY idx_layer (layer_code),
  KEY idx_category (category_code),
  KEY idx_blogger (blogger_id),
  KEY idx_star (star),
  KEY idx_mtime (mtime),
  CONSTRAINT fk_files_blogger FOREIGN KEY (blogger_id) REFERENCES bloggers (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='wiki 文件索引表：vault 扫描派生，看板数据主源（正文不入库，读取时回源 vault）';

-- 14. 文件-标签关联表（多对多，关系表统一 _rel 后缀）
CREATE TABLE file_tag_rel (
  file_id    BIGINT UNSIGNED NOT NULL COMMENT '文件外键，关联 files.id',
  tag_id     BIGINT UNSIGNED NOT NULL COMMENT '标签外键，关联 tags.id',
  PRIMARY KEY (file_id, tag_id),
  KEY idx_tag (tag_id),
  CONSTRAINT fk_ft_file FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE,
  CONSTRAINT fk_ft_tag FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件-标签关联表：多对多映射';

-- 15. 提炼记录表（加工历史，vault 无对应物，独立存储）
CREATE TABLE refine_records (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '提炼记录主键',
  source_url       VARCHAR(1024)   DEFAULT NULL COMMENT '来源链接（原始帖子 URL）',
  source_type_code VARCHAR(32)     NOT NULL COMMENT '来源类型码值，关联 dict(type=source_type).code（raw/coarse）',
  from_rel         VARCHAR(512)    NOT NULL COMMENT '来源文件相对路径（粗制品/原始资源）',
  blogger_name     VARCHAR(128)    DEFAULT NULL COMMENT '涉及博主名',
  blogger_updated  TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否同步更新博主画像：1是 0否',
  reason           TEXT            DEFAULT NULL COMMENT '提炼理由（决策依据，含矛盾预警等）',
  steps            JSON            DEFAULT NULL COMMENT '提炼步骤数组（读取原文/识别/…）',
  verify_ok        TINYINT(1)      DEFAULT NULL COMMENT '验证是否通过：1通过 0失败 NULL未验证',
  verify_detail    VARCHAR(512)    DEFAULT NULL COMMENT '验证详情（如 verify-format.py 结果）',
  verification_hints JSON          DEFAULT NULL COMMENT '验证提示数组',
  at               BIGINT          NOT NULL DEFAULT 0 COMMENT '提炼时间戳（毫秒）',
  created_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (id),
  KEY idx_source_type (source_type_code),
  KEY idx_from (from_rel),
  KEY idx_at (at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提炼记录表：一次提炼决策链路（加工历史，展示用）';

-- 16. 提炼目标子表（1 提炼记录 → N 目标）
CREATE TABLE refine_targets (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '目标主键',
  record_id        BIGINT UNSIGNED NOT NULL COMMENT '提炼记录外键，关联 refine_records.id',
  target_rel       VARCHAR(512)    NOT NULL COMMENT '目标条目相对路径（wiki/博主/宏观）',
  target_type_code VARCHAR(32)     NOT NULL COMMENT '目标类型码值，关联 dict(type=target_type).code',
  layer_code       VARCHAR(32)     NOT NULL COMMENT '目标归属层码值，关联 dict(type=layer).code',
  relation_code    VARCHAR(32)     NOT NULL DEFAULT 'other' COMMENT '关系码值，关联 dict(type=target_relation).code',
  relation_note    VARCHAR(1024)   DEFAULT NULL COMMENT '关系说明原文（如「新建；与…互补」细节）',
  category_code    VARCHAR(32)     DEFAULT NULL COMMENT '目标分类码值，关联 dict(type=category).code',
  tags             JSON            DEFAULT NULL COMMENT '目标标签数组（冗余，便于展示）',
  thinking         JSON            DEFAULT NULL COMMENT '思考链路数组（提炼时的认知过程）',
  basis            VARCHAR(1024)   DEFAULT NULL COMMENT '提炼依据（原文支撑）',
  created_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (id),
  KEY idx_record (record_id),
  KEY idx_target_type (target_type_code),
  KEY idx_layer (layer_code),
  KEY idx_relation (relation_code),
  CONSTRAINT fk_rt_record FOREIGN KEY (record_id) REFERENCES refine_records (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提炼目标子表：一次提炼的每个产出目标及其关系';

-- 17. 审查记录表（加工历史）
CREATE TABLE review_records (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '审查记录主键',
  review_date   DATE            NOT NULL COMMENT '审查日期',
  title         VARCHAR(255)    NOT NULL COMMENT '审查标题',
  method        TEXT            DEFAULT NULL COMMENT '审查方法（vault_review.py 指标等）',
  main_problems JSON            DEFAULT NULL COMMENT '主要问题数组',
  summary       TEXT            DEFAULT NULL COMMENT '审查总结',
  saved_at      BIGINT          NOT NULL DEFAULT 0 COMMENT '落库时间戳（毫秒）',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (id),
  KEY idx_date (review_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审查记录表：一次全库审查报告（加工历史，展示用）';

-- 18. 审查检查项子表（1 审查 → N 检查项）
CREATE TABLE review_checks (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '检查项主键',
  review_id   BIGINT UNSIGNED NOT NULL COMMENT '审查记录外键，关联 review_records.id',
  item_name   VARCHAR(255)    NOT NULL COMMENT '检查项名称（如 frontmatter 缺失）',
  result      VARCHAR(64)     DEFAULT NULL COMMENT '检查结果值（数值或文本）',
  compare     VARCHAR(64)     DEFAULT NULL COMMENT '对比基准值',
  status_code VARCHAR(32)     NOT NULL COMMENT '状态码值，关联 dict(type=check_status).code（pass/warn/fail）',
  created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (id),
  KEY idx_review (review_id),
  KEY idx_status (status_code),
  CONSTRAINT fk_rc_review FOREIGN KEY (review_id) REFERENCES review_records (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审查检查项子表：每条审查的逐项检查结论';

-- 19. 粗制品状态表（加工历史/状态）
CREATE TABLE coarse_records (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '粗制品主键',
  rel           VARCHAR(512)    NOT NULL COMMENT '粗制品相对路径（唯一业务键）',
  status_code   VARCHAR(32)     NOT NULL DEFAULT 'pending' COMMENT '状态码值，关联 dict(type=coarse_status).code',
  score         INT             DEFAULT NULL COMMENT '质量评分（0-100，已评分才有）',
  score_reason  VARCHAR(1024)   DEFAULT NULL COMMENT '评分理由',
  scored_at     BIGINT          DEFAULT NULL COMMENT '评分时间戳（毫秒）',
  title         VARCHAR(255)    DEFAULT NULL COMMENT '加工后标题',
  processed_at  BIGINT          DEFAULT NULL COMMENT '加工时间戳（毫秒）',
  processed_to  VARCHAR(512)    DEFAULT NULL COMMENT '加工产物路径（原始资源）',
  output_preview TEXT           DEFAULT NULL COMMENT '加工输出预览（前 600 字）',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_rel (rel),
  KEY idx_status (status_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='粗制品状态表：粗制品的评分/加工状态（状态 + 加工历史）';

-- 20. 回收站表
CREATE TABLE trash_records (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '回收站主键',
  rel        VARCHAR(512)    NOT NULL COMMENT '被回收文件相对路径（唯一）',
  status     VARCHAR(32)     NOT NULL DEFAULT 'pending' COMMENT '回收状态：pending=待删除(冷静期) trash=已删除',
  deleted_at BIGINT          DEFAULT NULL COMMENT '回收时间戳（毫秒）',
  created_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_rel (rel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='回收站表：删除/回收的文件登记';

-- 21. 同步元数据表（vault 扫描版本控制）
CREATE TABLE sync_state (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  sync_key   VARCHAR(64)     NOT NULL COMMENT '同步键（如 last_scan_mtime）',
  sync_value VARCHAR(512)    NOT NULL COMMENT '同步值',
  updated_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_key (sync_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同步元数据表：vault 增量扫描的版本/游标控制';
