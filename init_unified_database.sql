-- 统一医疗报告数据库初始化脚本
-- 使用方法: psql -U postgres -f init_unified_database.sql

-- 创建数据库（如果不存在）
CREATE DATABASE patient_info;

-- 连接到医疗报告数据库
\c patient_info;

-- 删除旧的报告表（如果存在）
DROP TABLE IF EXISTS routine_lab_reports CASCADE;
DROP TABLE IF EXISTS microbiology_reports CASCADE;
DROP TABLE IF EXISTS examination_reports CASCADE;
DROP TABLE IF EXISTS pathology_reports CASCADE;

-- 创建统一的医疗报告表
CREATE TABLE IF NOT EXISTS medical_reports_rt_yl (
    id SERIAL PRIMARY KEY,
    card_no VARCHAR(50) NOT NULL,
    patient_no VARCHAR(50),
    report_type VARCHAR(50) NOT NULL,
    report_date VARCHAR(50) NOT NULL,
    report_data JSONB NOT NULL,
    dept_code VARCHAR(50),
    dept_name VARCHAR(100),
    doctor_code VARCHAR(50),
    diagnosis_code VARCHAR(50),
    diagnosis_name VARCHAR(200),
    ai_analysis TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE medical_reports_rt_yl IS '统一医疗报告表';
COMMENT ON COLUMN medical_reports_rt_yl.id IS '主键ID';
COMMENT ON COLUMN medical_reports_rt_yl.card_no IS '患者卡号';
COMMENT ON COLUMN medical_reports_rt_yl.patient_no IS '住院号';
COMMENT ON COLUMN medical_reports_rt_yl.report_type IS '报告类型：routine_lab, microbiology, examination, pathology';
COMMENT ON COLUMN medical_reports_rt_yl.report_date IS '报告日期';
COMMENT ON COLUMN medical_reports_rt_yl.report_data IS '报告数据JSON格式';
COMMENT ON COLUMN medical_reports_rt_yl.dept_code IS '科室编码';
COMMENT ON COLUMN medical_reports_rt_yl.dept_name IS '科室名称';
COMMENT ON COLUMN medical_reports_rt_yl.doctor_code IS '医生编码';
COMMENT ON COLUMN medical_reports_rt_yl.diagnosis_code IS '诊断编码';
COMMENT ON COLUMN medical_reports_rt_yl.diagnosis_name IS '诊断名称';
COMMENT ON COLUMN medical_reports_rt_yl.ai_analysis IS 'AI分析结果';
COMMENT ON COLUMN medical_reports_rt_yl.processed_at IS '处理时间';
COMMENT ON COLUMN medical_reports_rt_yl.created_at IS '创建时间';
COMMENT ON COLUMN medical_reports_rt_yl.updated_at IS '更新时间';

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_medical_reports_card_no ON medical_reports_rt_yl(card_no);
CREATE INDEX IF NOT EXISTS idx_medical_reports_report_type ON medical_reports_rt_yl(report_type);
CREATE INDEX IF NOT EXISTS idx_medical_reports_report_date ON medical_reports_rt_yl(report_date);
CREATE INDEX IF NOT EXISTS idx_medical_reports_created_at ON medical_reports_rt_yl(created_at);
CREATE INDEX IF NOT EXISTS idx_medical_reports_card_type ON medical_reports_rt_yl(card_no, report_type);

-- 创建患者信息表（如果不存在）
CREATE TABLE IF NOT EXISTS patient_info (
    id SERIAL PRIMARY KEY,
    card_no VARCHAR(50) NOT NULL,
    clinic_code VARCHAR(50),
    patient_name VARCHAR(100),
    sex_code VARCHAR(10),
    dept_code VARCHAR(50),
    dept_name VARCHAR(100),
    reg_date TIMESTAMP,
    doctor_code VARCHAR(50),
    allergy_history TEXT,
    discharge_summary TEXT,
    discharge_info TEXT,
    lis_result_detail TEXT,
    ai_report TEXT,
    pathology_reports TEXT,
    pacs_reports TEXT,
    microbiological_reports TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(card_no, reg_date)
);

-- 添加patient_info表的注释
COMMENT ON TABLE patient_info IS '患者信息表';
COMMENT ON COLUMN patient_info.card_no IS '患者卡号';
COMMENT ON COLUMN patient_info.lis_result_detail IS '检验结果详情';
COMMENT ON COLUMN patient_info.pathology_reports IS '病理报告';
COMMENT ON COLUMN patient_info.pacs_reports IS 'PACS检查报告';
COMMENT ON COLUMN patient_info.microbiological_reports IS '微生物报告';

-- 创建patient_info表的索引
CREATE INDEX IF NOT EXISTS idx_patient_info_card_no ON patient_info(card_no);
CREATE INDEX IF NOT EXISTS idx_patient_info_reg_date ON patient_info(reg_date);

-- 创建报告对比分析结果表
CREATE TABLE IF NOT EXISTS report_comparison_analysis (
    id SERIAL PRIMARY KEY,
    card_no VARCHAR(50) NOT NULL,
    patient_no VARCHAR(50),
    report_type VARCHAR(50) NOT NULL,
    current_report_id INTEGER NOT NULL,
    current_report_date VARCHAR(50) NOT NULL,
    current_report_data JSONB NOT NULL,
    historical_reports_count INTEGER DEFAULT 0,
    historical_reports_data JSONB,
    comparison_period VARCHAR(50),
    langchain_analysis TEXT,
    key_changes JSONB,
    trend_analysis TEXT,
    risk_assessment TEXT,
    recommendations TEXT,
    analysis_model VARCHAR(100),
    analysis_confidence VARCHAR(20),
    analysis_tokens_used INTEGER,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加报告对比分析表的注释和索引
COMMENT ON TABLE report_comparison_analysis IS '报告对比分析结果表';
CREATE INDEX IF NOT EXISTS idx_comparison_analysis_card_no ON report_comparison_analysis(card_no);
CREATE INDEX IF NOT EXISTS idx_comparison_analysis_report_type ON report_comparison_analysis(report_type);

-- 创建触发器函数，用于自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有表创建触发器
DROP TRIGGER IF EXISTS update_medical_reports_updated_at ON medical_reports;
CREATE TRIGGER update_medical_reports_updated_at
    BEFORE UPDATE ON medical_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_patient_info_updated_at ON patient_info;
CREATE TRIGGER update_patient_info_updated_at
    BEFORE UPDATE ON patient_info
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_comparison_analysis_updated_at ON report_comparison_analysis;
CREATE TRIGGER update_comparison_analysis_updated_at
    BEFORE UPDATE ON report_comparison_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入示例数据
INSERT INTO patient_info (
    card_no, clinic_code, patient_name, sex_code, dept_code, dept_name,
    reg_date, doctor_code, allergy_history, discharge_summary,
    discharge_info, lis_result_detail, ai_report
) VALUES (
    '7000217139', 'ZY010101599931', '贾先生', '1', '心脏科', '心脏科',
    '2025-04-20 10:00:00', '李医生', '无已知过敏史', 
    '患者因胸痛入院，经检查诊断为心绞痛，经治疗后病情稳定',
    '病情稳定，可以出院，注意休息，定期复查', 
    '血常规检查报告:
白细胞计数: 6.5 × 10^9/L (参考值: 3.5-9.5)
红细胞计数: 4.8 × 10^12/L (参考值: 4.3-5.8)
血红蛋白: 145 g/L (参考值: 130-175)
血小板计数: 280 × 10^9/L (参考值: 125-350)

生化检查报告:
血糖: 5.8 mmol/L (参考值: 3.9-6.1)
总胆固醇: 4.2 mmol/L (参考值: 2.8-5.17)
甘油三酯: 1.8 mmol/L (参考值: 0.56-1.70)

检查日期: 2025-04-20
报告状态: 已完成', 
    'AI分析: 患者心绞痛症状已缓解，建议定期随访，注意饮食和运动'
) ON CONFLICT (card_no, reg_date) DO NOTHING;

-- 插入示例医疗报告数据
INSERT INTO medical_reports_rt_yl (
    card_no, report_type, report_date, report_data, ai_analysis
) VALUES (
    '7000217139', 'routine_lab', '2025-04-20', 
    '{"white_blood_cell": "6.5", "red_blood_cell": "4.8", "hemoglobin": "145", "platelet": "280", "glucose": "5.8", "cholesterol": "4.2"}',
    '血常规指标正常，生化检查结果在正常范围内，建议定期复查'
) ON CONFLICT DO NOTHING;

-- 显示表结构
\d medical_reports_rt_yl;
\d patient_info;
\d report_comparison_analysis;

-- 显示插入的数据
SELECT 'medical_reports表数据:' as info;
SELECT * FROM medical_reports_rt_yl ;

SELECT 'patient_info表数据:' as info;
SELECT * FROM patient_info;

PRINT '数据库初始化完成！';
PRINT '统一医疗报告表已创建，支持以下报告类型：';
PRINT '- routine_lab: 常规检验报告';
PRINT '- microbiology: 微生物检验报告';
PRINT '- examination: 检查报告';
PRINT '- pathology: 病理报告'; 