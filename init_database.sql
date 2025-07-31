-- 创建患者信息数据库初始化脚本
-- 使用方法: psql -U postgres -f init_database.sql
-- 读取的数据库
-- 创建数据库（如果不存在）
CREATE DATABASE patient_info;

-- 连接到患者信息数据库
\c patient_info;

-- 创建患者信息表
CREATE TABLE IF NOT EXISTS patient_info (
    id SERIAL PRIMARY KEY COMMENT '主键ID',
    card_no VARCHAR(50) NOT NULL COMMENT '患者卡号',
    clinic_code VARCHAR(50) COMMENT '就诊代码',
    patient_name VARCHAR(100) COMMENT '患者姓名',
    sex_code VARCHAR(10) COMMENT '性别代码（1-男，2-女）',
    dept_code VARCHAR(50) COMMENT '科室代码',
    dept_name VARCHAR(100) COMMENT '科室名称',
    reg_date TIMESTAMP COMMENT '就诊登记日期',
    doctor_code VARCHAR(50) COMMENT '医生代码',
    allergy_history TEXT COMMENT '过敏史',
    discharge_summary TEXT COMMENT '出院小结',
    discharge_info TEXT COMMENT '出院信息',
    lis_result_detail TEXT COMMENT '检验结果详情',
    ai_report TEXT COMMENT 'AI分析报告',
    pathology_reports TEXT COMMENT '病理报告',
    pacs_reports TEXT COMMENT 'PACS检查报告',
    microbiological_reports TEXT COMMENT '微生物报告',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录更新时间',
    UNIQUE(card_no, reg_date)
);


-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_patient_card_no ON patient_info(card_no);
CREATE INDEX IF NOT EXISTS idx_patient_reg_date ON patient_info(reg_date);
CREATE INDEX IF NOT EXISTS idx_patient_dept_code ON patient_info(dept_code);
CREATE INDEX IF NOT EXISTS idx_patient_created_at ON patient_info(created_at);

-- 创建触发器函数，用于自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
DROP TRIGGER IF EXISTS update_patient_info_updated_at ON patient_info;
CREATE TRIGGER update_patient_info_updated_at
    BEFORE UPDATE ON patient_info
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入示例数据（可选）
INSERT INTO patient_info (
    card_no, clinic_code, patient_name, sex_code, dept_code, dept_name,
    reg_date, doctor_code, allergy_history, discharge_summary,
    discharge_info, lis_result_detail, ai_report
) VALUES (
    '7000217139', 'ZY010101599931', '贾先生', '1', '心脏科', '心脏科',
    '2025-04-20 10:00:00', '李医生', '无已知过敏史', 
    '患者因胸痛入院，经检查诊断为心绞痛，经治疗后病情稳定',
    '病情稳定，可以出院，注意休息，定期复查', 
    '血常规正常，心电图显示轻微异常，建议进一步观察', 
    'AI分析: 患者心绞痛症状已缓解，建议定期随访，注意饮食和运动'
) ON CONFLICT (card_no, reg_date) DO NOTHING;

-- 显示表结构
\d patient_info;

-- 显示插入的数据
SELECT * FROM patient_info; 