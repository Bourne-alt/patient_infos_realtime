"""
医疗报告分析API
接收各种医疗报告数据，调用大模型进行分析，并将结果存储到PostgreSQL数据库
支持基于LangChain的历史报告对比分析
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import asyncio
import httpx
from contextlib import asynccontextmanager
import traceback

# 导入数据库模型和Pydantic模型
from models import Base, MedicalReport, ReportComparisonAnalysis, PatientInfo
from schemas import (
    RoutineLabReportRequest, RoutineLabReportResponse,
    MicrobiologyReportRequest, MicrobiologyReportResponse,
    ExaminationReportRequest, ExaminationReportResponse,
    PathologyReportRequest, PathologyReportResponse,
    ReportComparisonRequest, ReportComparisonResponse,
    PatientHistoryRequest, PatientHistoryResponse,
    ErrorResponse
)

# 导入新的服务模块
from database_service import DatabaseService
from exceptions import (
    ErrorHandler, create_error_response, handle_database_error, 
    handle_llm_error, MedicalReportError, DatabaseError, LLMAnalysisError
)
from singletons import (
    get_medical_analyzer, get_database_session, get_database_engine, 
    get_connection_info, database_manager
)
from dependencies import (
    get_db, get_database_service, get_analyzer, get_services,
    get_health_check_db, validate_request_data, get_error_handler
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('medical_report_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("medical_report_api")

# 使用单例管理器获取数据库组件
engine = get_database_engine()
SessionLocal = database_manager.get_session_factory()

# 大模型API配置
LLM_API_URL = os.getenv("OPENAI_API_BASE", "http://localhost:11434/api/generate")
LLM_MODEL = os.getenv("OPENAI_MODEL", "llama3.1")
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "sk-proj-1234567890")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用程序生命周期 - 启动和关闭"""
    # 启动时创建数据库表
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    
    yield
    
    # 关闭时的清理操作
    logger.info("应用程序关闭")

# 创建FastAPI应用
app = FastAPI(
    title="医疗报告分析API",
    description="接收医疗报告数据，调用大模型进行分析，并存储到数据库。支持基于LangChain的历史报告对比分析",
    version="2.0.0",
    lifespan=lifespan
)

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {str(exc)}")
    logger.error(f"异常详情: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "code": "500",
            "error": "服务器内部错误",
            "message": "请联系管理员",
            "processed_at": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": str(exc.status_code),
            "error": exc.detail,
            "processed_at": datetime.utcnow().isoformat()
        }
    )

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = datetime.utcnow()
    
    # 记录请求信息
    logger.info(f"请求开始: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        
        # 记录响应信息
        process_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"请求完成: {request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
        
        return response
    except Exception as e:
        process_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"请求失败: {request.method} {request.url} - {str(e)} - {process_time:.2f}s")
        raise

# 注：数据库依赖现在由 dependencies.py 模块提供

# API根路径
@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "医疗报告分析API",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "basic_analysis": "基础AI分析",
            "historical_comparison": "历史对比分析（基于LangChain）",
            "trend_analysis": "趋势分析",
            "risk_assessment": "风险评估"
        },
        "database_structure": {
            "unified_table": "medical_reports",
            "supported_report_types": ["routine_lab", "microbiology", "examination", "pathology"],
            "removed_result_list_field": "使用report_data字段存储所有报告数据"
        },
        "endpoints": {
            "常规检验报告": "/routine-lab",
            "微生物检验报告": "/microbiology", 
            "检查报告": "/examination",
            "病理报告": "/pathology",
            "历史对比分析": "/compare-reports",
            "患者历史报告": "/patient-history",
            "健康检查": "/health"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_health_check_db)):
    """健康检查端点"""
    try:
        # 测试数据库连接
        if db:
            db.execute("SELECT 1")
        else:
            raise Exception("数据库连接失败")
        
        # 测试大模型API（如果配置了）
        llm_status = "not_configured"
        if LLM_API_URL != "http://localhost:11434/api/generate":
            try:
                # 准备测试请求的头部
                test_headers = {}
                if LLM_API_KEY and LLM_API_KEY != "sk-proj-1234567890":
                    test_headers["Authorization"] = f"Bearer {LLM_API_KEY}"
                
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        LLM_API_URL.replace("/api/generate", "/api/tags"),
                        headers=test_headers
                    )
                    llm_status = "connected" if response.status_code == 200 else "disconnected"
            except:
                llm_status = "disconnected"
        
        # 测试LangChain分析器和连接池状态
        try:
            analyzer_info = get_connection_info()
            langchain_status = "initialized" if analyzer_info["analyzer"]["initialized"] else "not_initialized"
            connection_pool_info = analyzer_info["database"]
        except Exception as e:
            langchain_status = f"error: {str(e)}"
            connection_pool_info = {"error": str(e)}
        
        # 检查API key配置状态
        api_key_status = "not_configured"
        if LLM_API_KEY and LLM_API_KEY != "sk-proj-1234567890":
            api_key_status = "configured"
        elif LLM_API_KEY == "sk-proj-1234567890":
            api_key_status = "default_placeholder"
        
        return {
            "status": "healthy",
            "database": "connected",
            "connection_pool": connection_pool_info,
            "llm_api": llm_status,
            "api_key": api_key_status,
            "langchain_analyzer": langchain_status,
            "llm_model": LLM_MODEL,
            "llm_url": LLM_API_URL.replace(LLM_API_KEY, "***") if LLM_API_KEY in LLM_API_URL else LLM_API_URL,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# 大模型分析函数
async def analyze_with_llm(report_type: str, report_data: Dict[str, Any], historical_report: Optional[Dict[str, Any]] = None) -> str:
    """
    调用大模型分析医疗报告
    
    Args:
        report_type: 报告类型
        report_data: 报告数据
        historical_report: 历史报告数据（可选）
        
    Returns:
        分析结果
    """
    try:
        # 构建不同类型报告的专业分析提示
        if report_type == "routineLab":
            if historical_report:
                # 有历史报告时进行对比分析
                prompt = f"""
                请作为专业的临床检验医学专家，对比分析以下常规检验报告：
                
                【当前报告】：
                {json.dumps(report_data, ensure_ascii=False, indent=2)}
                
                【历史报告】（最近一次）：
                {json.dumps(historical_report, ensure_ascii=False, indent=2)}
                
                请从以下几个方面进行详细的对比分析：
                1. 当前报告各项检验指标的参考值范围和实际值对比
                2. 与历史报告相比，各项指标的变化趋势（上升、下降、稳定）
                3. 异常指标的临床意义和可能的病理状态变化
                4. 检验结果的整体评估和疾病风险评估
                5. 基于变化趋势的健康状况分析
                6. 建议的进一步检查、治疗措施或生活方式调整
                7. 针对变化趋势的用药建议和随访建议
                
                请特别关注：
                - 哪些指标有显著变化
                - 变化的幅度和临床意义
                - 是否存在好转或恶化的趋势
                - 需要重点关注的风险指标
                
                请用专业但通俗易懂的中文回答，突出对比分析的结果。
                """
            else:
                # 无历史报告时进行单独分析
                prompt = f"""
                请作为专业的临床检验医学专家，分析以下常规检验报告：
                
                报告数据：{json.dumps(report_data, ensure_ascii=False, indent=2)}
                
                请从以下几个方面进行详细分析：
                1. 各项检验指标的参考值范围和实际值对比
                2. 异常指标的临床意义和可能的病理状态
                3. 检验结果的整体评估和疾病风险
                4. 建议的进一步检查或治疗措施
                5. 患者生活方式和用药建议
                
                注意：这是该患者的首次检验报告，暂无历史数据可供对比。
                
                请用专业但通俗易懂的中文回答。
                """
        elif report_type == "microbiology":
            if historical_report:
                # 有历史报告时进行对比分析
                prompt = f"""
                请作为专业的微生物学和感染科专家，对比分析以下微生物检验报告：
                
                【当前报告】：
                {json.dumps(report_data, ensure_ascii=False, indent=2)}
                
                【历史报告】（最近一次）：
                {json.dumps(historical_report, ensure_ascii=False, indent=2)}
                
                请从以下几个方面进行详细的对比分析：
                1. 微生物培养结果的变化和临床意义
                2. 病原菌种类、数量的变化趋势
                3. 药敏试验结果的变化和耐药性分析
                4. 感染控制效果评估
                5. 治疗方案的有效性评估
                6. 后续治疗建议和预防措施
                
                请特别关注感染是否得到控制、耐药性变化等关键信息。
                
                请用专业但通俗易懂的中文回答。
                """
            else:
                prompt = f"""
                请作为专业的微生物学和感染科专家，分析以下微生物检验报告：
                
                报告数据：{json.dumps(report_data, ensure_ascii=False, indent=2)}
                
                请从以下几个方面进行详细分析：
                1. 微生物培养结果的临床意义
                2. 病原菌的致病性和传播途径
                3. 药敏试验结果的解读和抗菌药物选择
                4. 感染控制措施和预防建议
                5. 治疗方案的制定和疗程建议
                
                请用专业但通俗易懂的中文回答。
                """
        elif report_type == "examination":
            if historical_report:
                # 有历史报告时进行对比分析
                prompt = f"""
                请作为专业的影像学和临床医学专家，对比分析以下检查报告：
                
                【当前报告】：
                {json.dumps(report_data, ensure_ascii=False, indent=2)}
                
                【历史报告】（最近一次）：
                {json.dumps(historical_report, ensure_ascii=False, indent=2)}
                
                请从以下几个方面进行详细的对比分析：
                1. 客观所见的变化对比
                2. 主观提示的变化分析
                3. 病变进展、稳定或好转的评估
                4. 治疗效果的评估
                5. 后续诊疗建议
                
                请用专业但通俗易懂的中文回答。
                """
            else:
                prompt = f"""
                请作为专业的影像学和临床医学专家，分析以下检查报告：
                
                报告数据：{json.dumps(report_data, ensure_ascii=False, indent=2)}
                
                请从以下几个方面进行详细分析：
                1. 客观所见的详细解读
                2. 主观提示的临床意义
                3. 检查结果与临床症状的关联性
                4. 可能的诊断和鉴别诊断
                5. 建议的后续检查或治疗方案
                
                请用专业但通俗易懂的中文回答。
                """
        elif report_type == "pathology":
            if historical_report:
                # 有历史报告时进行对比分析
                prompt = f"""
                请作为专业的病理学专家，对比分析以下病理报告：
                
                【当前报告】：
                {json.dumps(report_data, ensure_ascii=False, indent=2)}
                
                【历史报告】（最近一次）：
                {json.dumps(historical_report, ensure_ascii=False, indent=2)}
                
                请从以下几个方面进行详细的对比分析：
                1. 病理形态学特征的变化
                2. 诊断结果的变化和临床意义
                3. 疾病进展、稳定或好转的评估
                4. 治疗效果的病理学评估
                5. 预后评估和后续治疗建议
                
                请用专业但通俗易懂的中文回答。
                """
            else:
                prompt = f"""
                请作为专业的病理学专家，分析以下病理报告：
                
                报告数据：{json.dumps(report_data, ensure_ascii=False, indent=2)}
                
                请从以下几个方面进行详细分析：
                1. 病理形态学特征的详细解读
                2. 诊断结果的临床意义和严重程度
                3. 疾病的发生发展机制
                4. 预后评估和危险因素分析
                5. 治疗方案建议和随访计划
                
                请用专业但通俗易懂的中文回答。
                """
        else:
            prompt = f"""
            请作为专业的医疗AI助手，分析以下{report_type}：
            
            报告数据：{json.dumps(report_data, ensure_ascii=False, indent=2)}
            
            请提供详细的分析，包括：
            1. 关键指标解读
            2. 异常值识别
            3. 临床意义
            4. 建议的后续处理
            
            请用中文回答，保持专业性和准确性。
            """
        
        # 调用大模型API
        payload = {
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000
            }
        }
        
        # 准备请求头，包含API key
        headers = {
            "Content-Type": "application/json"
        }
        
        # 如果配置了API key，添加到请求头
        if LLM_API_KEY and LLM_API_KEY != "sk-proj-1234567890":
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"
            logger.debug("使用API key进行大模型调用")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(LLM_API_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get("response", "无法获取分析结果")
                analysis_type = "对比分析" if historical_report else "单独分析"
                logger.info(f"LLM分析成功 - 报告类型: {report_type}, 分析类型: {analysis_type}")
                return analysis
            else:
                logger.error(f"LLM API错误: {response.status_code} - {response.text}")
                return "大模型分析暂时不可用，请稍后重试"
                
    except asyncio.TimeoutError:
        logger.error("LLM分析超时")
        return "分析超时，请稍后重试"
    except Exception as e:
        logger.error(f"LLM分析错误: {str(e)}")
        return f"分析过程中发生错误，将使用基础分析"

# 兼容性包装函数（保留原有API）
def create_legacy_error_response(card_no: str, error_message: str) -> ErrorResponse:
    """创建传统格式的错误响应（兼容性）"""
    return ErrorResponse(
        code="500",
        cardNo=card_no,
        error=error_message,
        processed_at=datetime.utcnow().isoformat()
    )

# 新增：历史对比分析端点
@app.post("/compare-reports", response_model=ReportComparisonResponse)
async def compare_reports(
    request: ReportComparisonRequest,
    background_tasks: BackgroundTasks,
    services: tuple = Depends(get_services)
):
    """
    基于LangChain的历史报告对比分析
    
    Args:
        request: 对比分析请求数据
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        对比分析结果
    """
    try:
        logger.info(f"开始历史对比分析: {request.cardNo} - {request.reportType}")
        
        # 从依赖注入获取服务
        db_service, medical_analyzer = services
        
        # 获取当前报告数据
        current_report = db_service.get_current_report_by_id(request.reportType, request.currentReportId)
        if not current_report:
            return create_legacy_error_response(request.cardNo, "未找到指定的当前报告")
        
        # 获取历史报告数据
        historical_reports = db_service.get_historical_reports_by_type(
            request.cardNo, 
            request.reportType, 
            request.comparisonPeriod,
            request.currentReportId
        )
        
        if not historical_reports:
            logger.warning(f"未找到历史报告: {request.cardNo} - {request.reportType}")
            return ReportComparisonResponse(
                code="200",
                cardNo=request.cardNo,
                processed_at=datetime.utcnow().isoformat(),
                comparison_analysis="暂无历史报告数据可供对比分析",
                historical_reports_count=0,
                trend_analysis="无历史数据",
                risk_assessment="无法评估",
                recommendations="建议积累更多历史数据"
            )
        
        # 使用LangChain进行对比分析
        analysis_result = await medical_analyzer.compare_reports(
            card_no=request.cardNo,
            report_type=request.reportType,
            current_report=current_report,
            historical_reports=historical_reports,
            comparison_period=request.comparisonPeriod
        )
        
        # 保存对比分析结果到数据库
        save_success = db_service.save_comparison_analysis(
            card_no=request.cardNo,
            patient_no=current_report.get("patient_no"),
            report_type=request.reportType,
            current_report_id=request.currentReportId,
            current_report_date=current_report.get("report_date", str(current_report.get("created_at", ""))),
            current_report_data=current_report,
            historical_reports_data=historical_reports,
            comparison_period=request.comparisonPeriod,
            analysis_result=analysis_result
        )
        
        if not save_success:
            logger.warning(f"保存对比分析结果失败: {request.cardNo}")
        
        # 返回成功响应
        return ReportComparisonResponse(
            code="200",
            cardNo=request.cardNo,
            processed_at=datetime.utcnow().isoformat(),
            comparison_analysis=analysis_result.get("langchain_analysis"),
            key_changes=analysis_result.get("key_changes"),
            trend_analysis=analysis_result.get("trend_analysis"),
            risk_assessment=analysis_result.get("risk_assessment"),
            recommendations=analysis_result.get("recommendations"),
            historical_reports_count=len(historical_reports),
            analysis_model=analysis_result.get("analysis_model"),
            analysis_confidence=analysis_result.get("analysis_confidence")
        )
        
    except MedicalReportError as e:
        # 处理自定义医疗报告异常
        error_dict = ErrorHandler.create_error_response(request.cardNo, e)
        return ReportComparisonResponse(
            code=error_dict["code"],
            cardNo=error_dict["cardNo"],
            processed_at=error_dict["processed_at"],
            comparison_analysis=error_dict["error"],
            historical_reports_count=0,
            trend_analysis="分析失败",
            risk_assessment="无法评估",
            recommendations=error_dict["message"]
        )
    except Exception as e:
        # 处理其他未预期异常
        error_dict = ErrorHandler.create_error_response(request.cardNo, e, "对比分析失败")
        return ReportComparisonResponse(
            code=error_dict["code"],
            cardNo=error_dict["cardNo"],
            processed_at=error_dict["processed_at"],
            comparison_analysis=error_dict["error"],
            historical_reports_count=0,
            trend_analysis="分析失败",
            risk_assessment="无法评估",
            recommendations=error_dict["message"]
        )

# 新增：患者历史报告查询端点
@app.post("/patient-history", response_model=PatientHistoryResponse)
async def get_patient_history(
    request: PatientHistoryRequest,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    获取患者历史报告摘要
    
    Args:
        request: 患者历史查询请求
        db: 数据库会话
        
    Returns:
        患者历史报告摘要
    """
    try:
        logger.info(f"查询患者历史报告: {request.cardNo}")
        
        # 获取患者历史报告摘要
        reports_summary, total_count = db_service.get_patient_all_reports_summary(
            request.cardNo,
            request.limit,
            request.offset
        )
        
        return PatientHistoryResponse(
            cardNo=request.cardNo,
            total_reports=total_count,
            reports=reports_summary,
            processed_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"查询患者历史报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

# API端点实现

@app.post("/routine-lab", response_model=RoutineLabReportResponse)
async def create_routine_lab_report(
    request: RoutineLabReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    注册常规检验报告信息
    
    Args:
        request: 常规检验报告请求数据
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        处理结果
    """
    try:
        # 验证和解析JSON数据
        try:
            result_list_data = json.loads(request.resultList)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return create_legacy_error_response(request.cardNo, "检查结果数据格式错误")
        
        # 准备报告数据用于AI分析
        report_data = {
            "cardNo": request.cardNo,
            "reportDate": request.reportDate,
            "resultList": result_list_data
        }
        
        # 创建数据库服务实例，查询最近的历史报告
        db_service = DatabaseService(db)
        
        # 从patient_info表获取最新的lis_result_detail文本数据
        latest_lis_result = db_service.get_latest_lis_result_detail(request.cardNo)
        
        latest_historical_report = None
        if latest_lis_result and latest_lis_result.get('lis_result_detail'):
            # 直接使用lis_result_detail文本内容作为历史数据
            latest_historical_report = {
                "card_no": latest_lis_result['card_no'],
                "patient_name": latest_lis_result.get('patient_name'),
                "report_date": str(latest_lis_result['reg_date']),
                "lis_result_detail": latest_lis_result['lis_result_detail'],  # 直接使用文本内容
                "source": "patient_info_table"
            }
            logger.info(f"找到patient_info表历史检验数据 - 患者: {request.cardNo}, 登记日期: {latest_lis_result['reg_date']}")
        else:
            logger.info(f"未找到patient_info表历史数据 - 患者: {request.cardNo}, 跳过历史对比")
        
        # 调用AI分析（异步），传入历史报告数据
        ai_analysis = await analyze_with_llm("routineLab", report_data, latest_historical_report)
        
        # 创建数据库记录
        db_report = MedicalReport(
            card_no=request.cardNo,
            report_type="routine_lab",
            report_date=request.reportDate,
            report_data=result_list_data,
            ai_analysis=ai_analysis,
            processed_at=datetime.utcnow()
        )
        
        # 保存到数据库
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        logger.info(f"常规检验报告保存成功 - 患者卡号: {request.cardNo}")
        
        # 返回成功响应
        return RoutineLabReportResponse(
            code="200",
            cardNo=request.cardNo,
            processed_at=datetime.utcnow().isoformat(),
            ai_analysis=ai_analysis
        )
        
    except SQLAlchemyError as e:
        db.rollback()
        db_error = handle_database_error("保存常规检验报告", request.cardNo, e)
        error_dict = ErrorHandler.create_error_response(request.cardNo, db_error)
        return RoutineLabReportResponse(
            code=error_dict["code"],
            cardNo=error_dict["cardNo"],
            processed_at=error_dict["processed_at"],
            ai_analysis=error_dict["error"]
        )
    except Exception as e:
        db.rollback()
        error_dict = ErrorHandler.create_error_response(request.cardNo, e, "处理常规检验报告失败")
        return RoutineLabReportResponse(
            code=error_dict["code"],
            cardNo=error_dict["cardNo"],
            processed_at=error_dict["processed_at"],
            ai_analysis=error_dict["error"]
        )

@app.post("/microbiology", response_model=MicrobiologyReportResponse)
async def create_microbiology_report(
    request: MicrobiologyReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    注册微生物检验报告信息
    
    Args:
        request: 微生物检验报告请求数据
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        处理结果
    """
    try:
        # 验证和解析JSON数据
        try:
            microbe_result_data = json.loads(request.microbeResultList)
            bacterial_result_data = json.loads(request.bacterialResultList)
            drug_sensitivity_data = json.loads(request.drugSensitivityList)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return create_error_response(request.cardNo, "微生物检验数据格式错误")
        
        # 准备报告数据用于AI分析
        report_data = {
            "cardNo": request.cardNo,
            "reportDate": request.reportDate,
            "microbeResultList": microbe_result_data,
            "bacterialResultList": bacterial_result_data,
            "drugSensitivityList": drug_sensitivity_data,
            "deptCode": request.deptCode,
            "deptName": request.deptName,
            "diagnosisCode": request.diagnosisCode,
            "diagnosisName": request.diagnosisName,
            "diagnosisDate": request.diagnosisDate,
            "testResultCode": request.testResultCode,
            "testResultName": request.testResultName,
            "testQuantifyResult": request.testQuantifyResult,
            "testQuantifyResultUnit": request.testQuantifyResultUnit
        }
        
        # 创建数据库服务实例，查询最近的历史报告
        db_service = DatabaseService(db)
        
        # 从patient_info表获取最新的lis_result_detail文本数据
        latest_lis_result = db_service.get_latest_lis_result_detail(request.cardNo)
        
        latest_historical_report = None
        if latest_lis_result and latest_lis_result.get('lis_result_detail'):
            # 直接使用lis_result_detail文本内容作为历史数据
            latest_historical_report = {
                "card_no": latest_lis_result['card_no'],
                "patient_name": latest_lis_result.get('patient_name'),
                "report_date": str(latest_lis_result['reg_date']),
                "lis_result_detail": latest_lis_result['lis_result_detail'],  # 直接使用文本内容
                "source": "patient_info_table"
            }
            logger.info(f"找到patient_info表历史检验数据 - 患者: {request.cardNo}, 登记日期: {latest_lis_result['reg_date']}")
        else:
            logger.info(f"未找到patient_info表历史数据 - 患者: {request.cardNo}, 跳过历史对比")
        
        # 调用AI分析（异步），传入历史报告数据
        ai_analysis = await analyze_with_llm("microbiology", report_data, latest_historical_report)
        
        # 准备微生物报告数据
        microbiology_data = {
            "microbe_result_list": microbe_result_data,
            "bacterial_result_list": bacterial_result_data,
            "drug_sensitivity_list": drug_sensitivity_data,
            "diagnosis_date": request.diagnosisDate,
            "test_result_code": request.testResultCode,
            "test_result_name": request.testResultName,
            "test_quantify_result": request.testQuantifyResult,
            "test_quantify_result_unit": request.testQuantifyResultUnit
        }
        
        # 创建数据库记录
        db_report = MedicalReport(
            card_no=request.cardNo,
            report_type="microbiology",
            report_date=request.reportDate,
            report_data=microbiology_data,
            dept_code=request.deptCode,
            dept_name=request.deptName,
            diagnosis_code=request.diagnosisCode,
            diagnosis_name=request.diagnosisName,
            ai_analysis=ai_analysis,
            processed_at=datetime.utcnow()
        )
        
        # 保存到数据库
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        logger.info(f"微生物检验报告保存成功 - 患者卡号: {request.cardNo}")
        
        # 返回成功响应
        return MicrobiologyReportResponse(
            code="200",
            cardNo=request.cardNo,
            processed_at=datetime.utcnow().isoformat(),
            ai_analysis=ai_analysis
        )
        
    except SQLAlchemyError as e:
        logger.error(f"数据库错误: {e}")
        db.rollback()
        return create_error_response(request.cardNo, "数据库保存失败")
    except Exception as e:
        logger.error(f"处理微生物检验报告时发生错误: {e}")
        db.rollback()
        return create_error_response(request.cardNo, f"处理失败: {str(e)}")

@app.post("/examination", response_model=ExaminationReportResponse)
async def create_examination_report(
    request: ExaminationReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    注册检查报告信息
    
    Args:
        request: 检查报告请求数据
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        处理结果
    """
    try:
        # 准备报告数据用于AI分析
        report_data = {
            "cardNo": request.cardNo,
            "patientNo": request.patientNo,
            "reportDate": request.reportDate,
            "examResultCode": request.examResultCode,
            "examResultName": request.examResultName,
            "examQuantifyResult": request.examQuantifyResult,
            "examQuantifyResultUnit": request.examQuantifyResultUnit,
            "examObservation": request.examObservation,
            "examResult": request.examResult
        }
        
        # 创建数据库服务实例，查询最近的历史报告
        db_service = DatabaseService(db)
        
        # 从patient_info表获取最新的lis_result_detail文本数据
        latest_lis_result = db_service.get_latest_lis_result_detail(request.cardNo)
        
        latest_historical_report = None
        if latest_lis_result and latest_lis_result.get('lis_result_detail'):
            # 直接使用lis_result_detail文本内容作为历史数据
            latest_historical_report = {
                "card_no": latest_lis_result['card_no'],
                "patient_name": latest_lis_result.get('patient_name'),
                "report_date": str(latest_lis_result['reg_date']),
                "lis_result_detail": latest_lis_result['lis_result_detail'],  # 直接使用文本内容
                "source": "patient_info_table"
            }
            logger.info(f"找到patient_info表历史检验数据 - 患者: {request.cardNo}, 登记日期: {latest_lis_result['reg_date']}")
        else:
            logger.info(f"未找到patient_info表历史数据 - 患者: {request.cardNo}, 跳过历史对比")
        
        # 调用AI分析（异步），传入历史报告数据
        ai_analysis = await analyze_with_llm("examination", report_data, latest_historical_report)
        
        # 准备检查报告数据
        examination_data = {
            "exam_result_code": request.examResultCode,
            "exam_result_name": request.examResultName,
            "exam_quantify_result": request.examQuantifyResult,
            "exam_quantify_result_unit": request.examQuantifyResultUnit,
            "exam_observation": request.examObservation,
            "exam_result": request.examResult
        }
        
        # 创建数据库记录
        db_report = MedicalReport(
            card_no=request.cardNo,
            patient_no=request.patientNo,
            report_type="examination",
            report_date=request.reportDate,
            report_data=examination_data,
            ai_analysis=ai_analysis,
            processed_at=datetime.utcnow()
        )
        
        # 保存到数据库
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        logger.info(f"检查报告保存成功 - 患者卡号: {request.cardNo}")
        
        # 返回成功响应
        return ExaminationReportResponse(
            code="200",
            cardNo=request.cardNo,
            processed_at=datetime.utcnow().isoformat(),
            ai_analysis=ai_analysis
        )
        
    except SQLAlchemyError as e:
        logger.error(f"数据库错误: {e}")
        db.rollback()
        return create_error_response(request.cardNo, "数据库保存失败")
    except Exception as e:
        logger.error(f"处理检查报告时发生错误: {e}")
        db.rollback()
        return create_error_response(request.cardNo, f"处理失败: {str(e)}")

@app.post("/pathology", response_model=PathologyReportResponse)
async def create_pathology_report(
    request: PathologyReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    注册病理报告信息
    
    Args:
        request: 病理报告请求数据
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        处理结果
    """
    try:
        # 准备报告数据用于AI分析
        report_data = {
            "cardNo": request.cardNo,
            "patientNo": request.patientNo,
            "deptCode": request.deptCode,
            "deptName": request.deptName,
            "diagnosisCode": request.diagnosisCode,
            "diagnosisName": request.diagnosisName,
            "chiefComplaint": request.chiefComplaint,
            "symptomDescribe": request.symptomDescribe,
            "symptomStartTime": request.symptomStartTime,
            "symptomEndTime": request.symptomEndTime,
            "examResultCode": request.examResultCode,
            "examResultName": request.examResultName,
            "examQuantifyResult": request.examQuantifyResult,
            "examQuantifyResultUnit": request.examQuantifyResultUnit,
            "diagnosisDescribe": request.diagnosisDescribe,
            "examObservation": request.examObservation,
            "examResult": request.examResult
        }
        
        # 创建数据库服务实例，查询最近的历史报告
        db_service = DatabaseService(db)
        
        # 从patient_info表获取最新的lis_result_detail文本数据
        latest_lis_result = db_service.get_latest_lis_result_detail(request.cardNo)
        
        latest_historical_report = None
        if latest_lis_result and latest_lis_result.get('lis_result_detail'):
            # 直接使用lis_result_detail文本内容作为历史数据
            latest_historical_report = {
                "card_no": latest_lis_result['card_no'],
                "patient_name": latest_lis_result.get('patient_name'),
                "report_date": str(latest_lis_result['reg_date']),
                "lis_result_detail": latest_lis_result['lis_result_detail'],  # 直接使用文本内容
                "source": "patient_info_table"
            }
            logger.info(f"找到patient_info表历史检验数据 - 患者: {request.cardNo}, 登记日期: {latest_lis_result['reg_date']}")
        else:
            logger.info(f"未找到patient_info表历史数据 - 患者: {request.cardNo}, 跳过历史对比")
        
        # 调用AI分析（异步），传入历史报告数据
        ai_analysis = await analyze_with_llm("pathology", report_data, latest_historical_report)
        
        # 准备病理报告数据
        pathology_data = {
            "chief_complaint": request.chiefComplaint,
            "symptom_describe": request.symptomDescribe,
            "symptom_start_time": request.symptomStartTime,
            "symptom_end_time": request.symptomEndTime,
            "exam_result_code": request.examResultCode,
            "exam_result_name": request.examResultName,
            "exam_quantify_result": request.examQuantifyResult,
            "exam_quantify_result_unit": request.examQuantifyResultUnit,
            "diagnosis_describe": request.diagnosisDescribe,
            "exam_observation": request.examObservation,
            "exam_result": request.examResult
        }
        
        # 创建数据库记录
        db_report = MedicalReport(
            card_no=request.cardNo,
            patient_no=request.patientNo,
            report_type="pathology",
            report_date=request.reportDate,
            report_data=pathology_data,
            dept_code=request.deptCode,
            dept_name=request.deptName,
            diagnosis_code=request.diagnosisCode,
            diagnosis_name=request.diagnosisName,
            ai_analysis=ai_analysis,
            processed_at=datetime.utcnow()
        )
        
        # 保存到数据库
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        logger.info(f"病理报告保存成功 - 患者卡号: {request.cardNo}")
        
        # 返回成功响应
        return PathologyReportResponse(
            code="200",
            cardNo=request.cardNo,
            processed_at=datetime.utcnow().isoformat(),
            ai_analysis=ai_analysis
        )
        
    except SQLAlchemyError as e:
        logger.error(f"数据库错误: {e}")
        db.rollback()
        return create_error_response(request.cardNo, "数据库保存失败")
    except Exception as e:
        logger.error(f"处理病理报告时发生错误: {e}")
        db.rollback()
        return create_error_response(request.cardNo, f"处理失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7700) 