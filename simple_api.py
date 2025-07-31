#!/usr/bin/env python3
"""
简化版医疗报告分析API
不依赖数据库，可以独立运行，用于测试和演示
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
import asyncio
import httpx
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("simple_medical_api")

# 大模型API配置
LLM_API_URL = os.getenv("OPENAI_API_BASE", "http://localhost:11434/api/generate")
LLM_MODEL = os.getenv("OPENAI_MODEL", "llama3.1")
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "sk-proj-1234567890")

# 创建FastAPI应用
app = FastAPI(
    title="医疗报告分析API (简化版)",
    description="医疗报告分析API的简化版本，不需要数据库连接，可用于测试和演示",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class RoutineLabReportRequest(BaseModel):
    cardNo: str
    reportDate: str
    resultList: str

class MicrobiologyReportRequest(BaseModel):
    cardNo: str
    reportDate: str
    microbeResultList: str
    bacterialResultList: Optional[str] = ""
    drugSensitivityList: Optional[str] = ""
    deptCode: Optional[str] = ""
    deptName: Optional[str] = ""
    diagnosisCode: Optional[str] = ""
    diagnosisName: Optional[str] = ""
    diagnosisDate: Optional[str] = ""
    testResultCode: Optional[str] = ""
    testResultName: Optional[str] = ""
    testQuantifyResult: Optional[str] = ""
    testQuantifyResultUnit: Optional[str] = ""

class ExaminationReportRequest(BaseModel):
    cardNo: str
    reportDate: str
    objectiveFindings: str
    conclusion: Optional[str] = ""
    suggestion: Optional[str] = ""
    deptCode: Optional[str] = ""
    deptName: Optional[str] = ""

class PathologyReportRequest(BaseModel):
    cardNo: str
    reportDate: str
    pathologyDescription: str
    pathologyDiagnosis: Optional[str] = ""
    deptCode: Optional[str] = ""
    deptName: Optional[str] = ""

# 响应模型
class AnalysisResponse(BaseModel):
    success: bool
    message: str
    analysis: Optional[str] = None
    suggestions: Optional[List[str]] = None
    risk_level: Optional[str] = None
    report_id: Optional[str] = None

# 模拟LLM分析函数
async def simulate_llm_analysis(report_type: str, content: str) -> Dict[str, Any]:
    """模拟大模型分析，返回示例分析结果"""
    
    # 模拟处理时间
    await asyncio.sleep(1)
    
    analysis_templates = {
        "routine_lab": {
            "analysis": f"常规检验报告分析：\n\n根据提供的检验结果，患者的各项指标基本正常。建议定期复查，保持健康的生活方式。\n\n报告内容：{content[:200]}...",
            "suggestions": [
                "建议定期复查相关指标",
                "保持健康饮食习惯",
                "适量运动",
                "如有异常症状及时就医"
            ],
            "risk_level": "低风险"
        },
        "microbiology": {
            "analysis": f"微生物检验报告分析：\n\n微生物培养结果显示需要关注感染控制。建议根据药敏结果选择合适的抗生素治疗。\n\n报告内容：{content[:200]}...",
            "suggestions": [
                "严格按照药敏结果用药",
                "注意个人卫生",
                "完成完整的抗生素疗程",
                "定期复查微生物培养"
            ],
            "risk_level": "中风险"
        },
        "examination": {
            "analysis": f"检查报告分析：\n\n影像学检查结果需要结合临床症状综合判断。建议与临床医生讨论后续治疗方案。\n\n报告内容：{content[:200]}...",
            "suggestions": [
                "与主治医生讨论检查结果",
                "如需要可进行进一步检查",
                "注意观察症状变化",
                "按医嘱进行随访"
            ],
            "risk_level": "中风险"
        },
        "pathology": {
            "analysis": f"病理报告分析：\n\n病理学检查是疾病诊断的金标准。建议根据病理结果制定个体化治疗方案。\n\n报告内容：{content[:200]}...",
            "suggestions": [
                "与专科医生详细讨论病理结果",
                "制定个体化治疗方案",
                "定期随访复查",
                "保持良好心态，积极治疗"
            ],
            "risk_level": "需要专业评估"
        }
    }
    
    return analysis_templates.get(report_type, analysis_templates["routine_lab"])

# API路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "医疗报告分析API (简化版)",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/routine-lab",
            "/microbiology",
            "/examination",
            "/pathology"
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "database": "not_required",
        "llm_configured": LLM_API_KEY != "sk-proj-1234567890"
    }

@app.post("/routine-lab", response_model=AnalysisResponse)
async def analyze_routine_lab_report(request: RoutineLabReportRequest, background_tasks: BackgroundTasks):
    """分析常规检验报告"""
    try:
        logger.info(f"收到常规检验报告分析请求 - 患者卡号: {request.cardNo}")
        
        # 模拟LLM分析
        analysis_result = await simulate_llm_analysis("routine_lab", request.resultList)
        
        # 生成报告ID
        report_id = f"LAB_{request.cardNo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"常规检验报告分析完成 - 报告ID: {report_id}")
        
        return AnalysisResponse(
            success=True,
            message="常规检验报告分析完成",
            analysis=analysis_result["analysis"],
            suggestions=analysis_result["suggestions"],
            risk_level=analysis_result["risk_level"],
            report_id=report_id
        )
        
    except Exception as e:
        logger.error(f"常规检验报告分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@app.post("/microbiology", response_model=AnalysisResponse)
async def analyze_microbiology_report(request: MicrobiologyReportRequest, background_tasks: BackgroundTasks):
    """分析微生物检验报告"""
    try:
        logger.info(f"收到微生物检验报告分析请求 - 患者卡号: {request.cardNo}")
        
        # 模拟LLM分析
        content = f"{request.microbeResultList} {request.bacterialResultList} {request.drugSensitivityList}"
        analysis_result = await simulate_llm_analysis("microbiology", content)
        
        # 生成报告ID
        report_id = f"MICRO_{request.cardNo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"微生物检验报告分析完成 - 报告ID: {report_id}")
        
        return AnalysisResponse(
            success=True,
            message="微生物检验报告分析完成",
            analysis=analysis_result["analysis"],
            suggestions=analysis_result["suggestions"],
            risk_level=analysis_result["risk_level"],
            report_id=report_id
        )
        
    except Exception as e:
        logger.error(f"微生物检验报告分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@app.post("/examination", response_model=AnalysisResponse)
async def analyze_examination_report(request: ExaminationReportRequest, background_tasks: BackgroundTasks):
    """分析检查报告"""
    try:
        logger.info(f"收到检查报告分析请求 - 患者卡号: {request.cardNo}")
        
        # 模拟LLM分析
        content = f"{request.objectiveFindings} {request.conclusion} {request.suggestion}"
        analysis_result = await simulate_llm_analysis("examination", content)
        
        # 生成报告ID
        report_id = f"EXAM_{request.cardNo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"检查报告分析完成 - 报告ID: {report_id}")
        
        return AnalysisResponse(
            success=True,
            message="检查报告分析完成",
            analysis=analysis_result["analysis"],
            suggestions=analysis_result["suggestions"],
            risk_level=analysis_result["risk_level"],
            report_id=report_id
        )
        
    except Exception as e:
        logger.error(f"检查报告分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@app.post("/pathology", response_model=AnalysisResponse)
async def analyze_pathology_report(request: PathologyReportRequest, background_tasks: BackgroundTasks):
    """分析病理报告"""
    try:
        logger.info(f"收到病理报告分析请求 - 患者卡号: {request.cardNo}")
        
        # 模拟LLM分析
        content = f"{request.pathologyDescription} {request.pathologyDiagnosis}"
        analysis_result = await simulate_llm_analysis("pathology", content)
        
        # 生成报告ID
        report_id = f"PATH_{request.cardNo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"病理报告分析完成 - 报告ID: {report_id}")
        
        return AnalysisResponse(
            success=True,
            message="病理报告分析完成",
            analysis=analysis_result["analysis"],
            suggestions=analysis_result["suggestions"],
            risk_level=analysis_result["risk_level"],
            report_id=report_id
        )
        
    except Exception as e:
        logger.error(f"病理报告分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7700)