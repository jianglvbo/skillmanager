-- ============================================================
-- investment_kb: 投资知识库看板派生数据层
-- 架构原则: 本地 vault 为绝对基准（第一/首要/绝对），本库仅为
--           阅读 + 加工总结的派生数据；一切冲突以 vault 为准。
-- 字符集: utf8mb4 / utf8mb4_unicode_ci
-- 约定: 枚举字段一律存码值，引用 dict_* 码值表；主键自增；
--       外键保证引用完整性；每表每字段均带 COMMENT。
-- ============================================================
CREATE DATABASE IF NOT EXISTS investment_kb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE investment_kb;

-- ============ 一、码值表（字典） ============

-- 1. 归属层字典（files.layer_code / refine_targets.layer_code）
CREATE TABLE dict_layer (
  code       VARCHAR(32)  NOT NULL COMMENT '归属层码值：my/blogger/other/macro/workspace/attachment',
  name       VARCHAR(64)  NOT NULL COMMENT '归属层名称：我的/博主/其他/宏观/工作区/附件',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重，越小越靠前',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用：1启用 0停用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='归属层字典：知识库顶层分类（我的/博主/其他/宏观/工作区/附件）';

INSERT INTO dict_layer (code, name, sort_order, remark) VALUES
('my','我的',1,'个人总结/自建框架层'),
('blogger','博主',2,'博主画像及其产出层'),
('other','其他',3,'引用/外部资料层'),
('macro','宏观',4,'宏观分析层'),
('workspace','工作区',5,'工作区文件（粗制品/原始资源/控制台等）'),
('attachment','附件',6,'附件目录（图片等非条目）');

-- 2. 分类字典（files.category_code，六大分类+宏观）
CREATE TABLE dict_category (
  code       VARCHAR(32)  NOT NULL COMMENT '分类码值：analysis_framework/trading_system/investment_mentality/investment_insight/stock/industry/macro',
  name       VARCHAR(64)  NOT NULL COMMENT '分类名称：分析框架/交易体系/投资心态/投资心得/个股/行业/宏观',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重，越小越靠前',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用：1启用 0停用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分类字典：六大分类+宏观（看板分类统计/条目归类）';

INSERT INTO dict_category (code, name, sort_order, remark) VALUES
('analysis_framework','分析框架',1,'方法论/思维框架类条目'),
('trading_system','交易体系',2,'交易规则/体系类条目'),
('investment_mentality','投资心态',3,'心态/心理类条目'),
('investment_insight','投资心得',4,'心得/复盘类条目'),
('stock','个股',5,'个股分析条目'),
('industry','行业',6,'行业研究条目'),
('macro','宏观',7,'宏观分析条目');

-- 3. 文件类型字典（files.type_code）
CREATE TABLE dict_file_type (
  code       VARCHAR(32)  NOT NULL COMMENT '文件类型码值：post/article/video/video_summary/link/post_collection/other',
  name       VARCHAR(64)  NOT NULL COMMENT '类型名称：帖子/文章/视频/视频整理/链接/帖子集/其他',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件类型字典：粗制品/原始资源的来源类型';

INSERT INTO dict_file_type (code, name, sort_order, remark) VALUES
('post','帖子',1,'雪球/社区单帖'),
('article','文章',2,'长文/文章'),
('video','视频',3,'视频'),
('video_summary','视频整理',4,'视频内容整理稿'),
('link','链接',5,'链接型条目'),
('post_collection','帖子集',6,'博主多帖合集'),
('other','其他',7,'其他类型');

-- 4. 文件状态字典（files.status_code）
CREATE TABLE dict_file_status (
  code       VARCHAR(32)  NOT NULL COMMENT '状态码值：analyzing/refined/pending',
  name       VARCHAR(64)  NOT NULL COMMENT '状态名称：分析中/已提炼/待提炼',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件状态字典：wiki 条目的提炼进度';

INSERT INTO dict_file_status (code, name, sort_order, remark) VALUES
('analyzing','分析中',1,'正在分析/加工中'),
('refined','已提炼',2,'已完成提炼'),
('pending','待提炼',3,'等待提炼');

-- 5. 博主平台字典（bloggers.platform_code）
CREATE TABLE dict_platform (
  code       VARCHAR(32)  NOT NULL COMMENT '平台码值：xueqiu/douyin/xiaohongshu',
  name       VARCHAR(64)  NOT NULL COMMENT '平台名称：雪球/抖音/小红书',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='博主平台字典：博主内容来源平台';

INSERT INTO dict_platform (code, name, sort_order, remark) VALUES
('xueqiu','雪球',1,'雪球平台'),
('douyin','抖音',2,'抖音平台'),
('xiaohongshu','小红书',3,'小红书平台');

-- 6. 提炼来源类型字典（refine_records.source_type_code）
CREATE TABLE dict_source_type (
  code       VARCHAR(32)  NOT NULL COMMENT '来源类型码值：raw/coarse',
  name       VARCHAR(64)  NOT NULL COMMENT '来源类型名称：原始资源/粗制品',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提炼来源类型字典：提炼输入的原料类型';

INSERT INTO dict_source_type (code, name, sort_order, remark) VALUES
('raw','原始资源',1,'直接由原始资源提炼'),
('coarse','粗制品',2,'由粗制品提炼');

-- 7. 提炼目标类型字典（refine_targets.target_type_code）
CREATE TABLE dict_target_type (
  code       VARCHAR(32)  NOT NULL COMMENT '目标类型码值：wiki/blogger/macro',
  name       VARCHAR(64)  NOT NULL COMMENT '目标类型名称：框架条目/博主画像/宏观条目',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提炼目标类型字典：一次提炼产出的条目类型';

INSERT INTO dict_target_type (code, name, sort_order, remark) VALUES
('wiki','框架条目',1,'六大分类 wiki 框架条目'),
('blogger','博主画像',2,'博主画像/言论追踪'),
('macro','宏观条目',3,'宏观层条目');

-- 8. 提炼关系字典（refine_targets.relation_code）
CREATE TABLE dict_target_relation (
  code       VARCHAR(32)  NOT NULL COMMENT '关系码值：new/append/complement/conflict_check/other',
  name       VARCHAR(64)  NOT NULL COMMENT '关系名称：新建/追加/互补/矛盾预检/其他',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注：主关系类型，细节保留在 relation_note 原文',
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提炼关系字典：产物与库内既有条目的关系（主类型可统计，细节在 relation_note）';

INSERT INTO dict_target_relation (code, name, sort_order, remark) VALUES
('new','新建',1,'库内无同类，新建条目'),
('append','追加',2,'追加到已有条目'),
('complement','互补',3,'与已有条目互补（同主题不同角度）'),
('conflict_check','矛盾预检',4,'写前矛盾预警'),
('other','其他',5,'无法归入上述主类型');

-- 9. 审查状态字典（review_checks.status_code）
CREATE TABLE dict_check_status (
  code       VARCHAR(32)  NOT NULL COMMENT '状态码值：pass/ok/warn/fail',
  name       VARCHAR(64)  NOT NULL COMMENT '状态名称：通过/通过(旧)/警告/失败',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审查状态字典：审查检查项结论';

INSERT INTO dict_check_status (code, name, sort_order, remark) VALUES
('pass','通过',1,'检查通过'),
('ok','通过(旧)',2,'历史数据中的通过标记'),
('warn','警告',3,'存在问题需关注'),
('fail','失败',4,'检查未通过');

-- 10. 粗制品状态字典（coarse_items.status_code）
CREATE TABLE dict_coarse_status (
  code       VARCHAR(32)  NOT NULL COMMENT '状态码值：pending/scored/processed',
  name       VARCHAR(64)  NOT NULL COMMENT '状态名称：待处理/已评分/已加工',
  sort_order INT          NOT NULL DEFAULT 0 COMMENT '排序权重',
  enabled    TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
  remark     VARCHAR(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='粗制品状态字典：粗制品的处理进度';

INSERT INTO dict_coarse_status (code, name, sort_order, remark) VALUES
('pending','待处理',1,'刚入库待处理'),
('scored','已评分',2,'已完成质量评分'),
('processed','已加工',3,'已粗加工完成');

-- ============ 二、业务表 ============

-- 11. 博主画像表（vault 扫描派生，vault 为准）
CREATE TABLE bloggers (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '博主主键',
  name         VARCHAR(128)    NOT NULL COMMENT '博主名（唯一）',
  dir          VARCHAR(255)    NOT NULL COMMENT '博主在 vault 中的目录名',
  alias        VARCHAR(255)    DEFAULT NULL COMMENT '别名/曾用名',
  xueqiu_id    VARCHAR(64)     DEFAULT NULL COMMENT '雪球用户 ID（无则 NULL）',
  platform_code VARCHAR(32)    DEFAULT NULL COMMENT '平台码值，关联 dict_platform.code（雪球/抖音/小红书）',
  special      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否重点博主：1是 0否',
  summary      TEXT            DEFAULT NULL COMMENT '博主简介（画像摘要）',
  info_cutoff  VARCHAR(64)     DEFAULT NULL COMMENT '信息截止日期（画像信息更新点）',
  file_count   INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '博主产出文件数（vault 扫描统计）',
  created_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  updated_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_name (name),
  KEY idx_platform (platform_code),
  KEY idx_special (special),
  CONSTRAINT fk_bloggers_platform FOREIGN KEY (platform_code) REFERENCES dict_platform (code)
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
  layer_code    VARCHAR(32)     NOT NULL COMMENT '归属层码值，关联 dict_layer.code',
  category_code VARCHAR(32)     DEFAULT NULL COMMENT '分类码值，关联 dict_category.code',
  blogger_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '博主外键，关联 bloggers.id（博主层条目归属）',
  author        VARCHAR(128)    DEFAULT NULL COMMENT '作者名',
  type_code     VARCHAR(32)     DEFAULT NULL COMMENT '文件类型码值，关联 dict_file_type.code',
  status_code   VARCHAR(32)     DEFAULT NULL COMMENT '状态码值，关联 dict_file_status.code',
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
  CONSTRAINT fk_files_layer FOREIGN KEY (layer_code) REFERENCES dict_layer (code),
  CONSTRAINT fk_files_category FOREIGN KEY (category_code) REFERENCES dict_category (code),
  CONSTRAINT fk_files_blogger FOREIGN KEY (blogger_id) REFERENCES bloggers (id),
  CONSTRAINT fk_files_type FOREIGN KEY (type_code) REFERENCES dict_file_type (code),
  CONSTRAINT fk_files_status FOREIGN KEY (status_code) REFERENCES dict_file_status (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='wiki 文件索引表：vault 扫描派生，看板数据主源（正文不入库，读取时回源 vault）';

-- 14. 文件-标签关联表（多对多）
CREATE TABLE files_tags (
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
  source_type_code VARCHAR(32)     NOT NULL COMMENT '来源类型码值，关联 dict_source_type.code（raw/coarse）',
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
  KEY idx_at (at),
  CONSTRAINT fk_refine_source_type FOREIGN KEY (source_type_code) REFERENCES dict_source_type (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提炼记录表：一次提炼决策链路（加工历史，展示用）';

-- 16. 提炼目标子表（1 提炼记录 → N 目标）
CREATE TABLE refine_targets (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '目标主键',
  record_id        BIGINT UNSIGNED NOT NULL COMMENT '提炼记录外键，关联 refine_records.id',
  target_rel       VARCHAR(512)    NOT NULL COMMENT '目标条目相对路径（wiki/博主/宏观）',
  target_type_code VARCHAR(32)     NOT NULL COMMENT '目标类型码值，关联 dict_target_type.code',
  layer_code       VARCHAR(32)     NOT NULL COMMENT '目标归属层码值，关联 dict_layer.code',
  relation_code    VARCHAR(32)     NOT NULL DEFAULT 'other' COMMENT '关系码值，关联 dict_target_relation.code',
  relation_note    VARCHAR(1024)   DEFAULT NULL COMMENT '关系说明原文（如「新建；与…互补」细节）',
  category_code    VARCHAR(32)     DEFAULT NULL COMMENT '目标分类码值，关联 dict_category.code',
  tags             JSON            DEFAULT NULL COMMENT '目标标签数组（冗余，便于展示）',
  thinking         JSON            DEFAULT NULL COMMENT '思考链路数组（提炼时的认知过程）',
  basis            VARCHAR(1024)   DEFAULT NULL COMMENT '提炼依据（原文支撑）',
  created_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (id),
  KEY idx_record (record_id),
  KEY idx_target_type (target_type_code),
  KEY idx_layer (layer_code),
  KEY idx_relation (relation_code),
  CONSTRAINT fk_rt_record FOREIGN KEY (record_id) REFERENCES refine_records (id) ON DELETE CASCADE,
  CONSTRAINT fk_rt_target_type FOREIGN KEY (target_type_code) REFERENCES dict_target_type (code),
  CONSTRAINT fk_rt_layer FOREIGN KEY (layer_code) REFERENCES dict_layer (code),
  CONSTRAINT fk_rt_relation FOREIGN KEY (relation_code) REFERENCES dict_target_relation (code),
  CONSTRAINT fk_rt_category FOREIGN KEY (category_code) REFERENCES dict_category (code)
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
  status_code VARCHAR(32)     NOT NULL COMMENT '状态码值，关联 dict_check_status.code（pass/warn/fail）',
  created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (id),
  KEY idx_review (review_id),
  KEY idx_status (status_code),
  CONSTRAINT fk_rc_review FOREIGN KEY (review_id) REFERENCES review_records (id) ON DELETE CASCADE,
  CONSTRAINT fk_rc_status FOREIGN KEY (status_code) REFERENCES dict_check_status (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审查检查项子表：每条审查的逐项检查结论';

-- 19. 粗制品状态表（加工历史/状态）
CREATE TABLE coarse_items (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '粗制品主键',
  rel           VARCHAR(512)    NOT NULL COMMENT '粗制品相对路径（唯一业务键）',
  status_code   VARCHAR(32)     NOT NULL DEFAULT 'pending' COMMENT '状态码值，关联 dict_coarse_status.code',
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
  KEY idx_status (status_code),
  CONSTRAINT fk_coarse_status FOREIGN KEY (status_code) REFERENCES dict_coarse_status (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='粗制品状态表：粗制品的评分/加工状态（状态 + 加工历史）';

-- 20. 回收站表
CREATE TABLE trash_items (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '回收站主键',
  rel        VARCHAR(512)    NOT NULL COMMENT '被回收文件相对路径（唯一）',
  status     VARCHAR(32)     NOT NULL DEFAULT 'pending' COMMENT '回收状态：pending=待删除(冷静期) trash=已删除',
  deleted_at BIGINT          DEFAULT NULL COMMENT '回收时间戳（毫秒）',
  created_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_rel (rel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='回收站表：删除/回收的文件登记';

-- 21. 同步元数据表（vault 扫描版本控制）
CREATE TABLE sync_meta (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  sync_key   VARCHAR(64)     NOT NULL COMMENT '同步键（如 last_scan_mtime）',
  sync_value VARCHAR(512)    NOT NULL COMMENT '同步值',
  updated_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_key (sync_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同步元数据表：vault 增量扫描的版本/游标控制';
