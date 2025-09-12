"""
医疗报告分析API
接收各种医疗报告数据，调用大模型进行分析，并将结果存储到PostgreSQL数据库
支持基于LangChain的历史报告对比分析
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.exceptions import RequestValidationError
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
from dotenv import load_dotenv
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

load_dotenv(override=True)
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
# 导入优化后的报告处理服务和错误处理器
from report_service import (
    ReportProcessingService, ReportData, ReportType, report_service
)
from error_handlers import UnifiedErrorHandler, error_factory

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
LLM_API_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/api/generate")
LLM_MODEL = os.getenv("OPENAI_MODEL", "llama3.1")
# 使用统一的配置管理
from config import settings
LLM_API_KEY = settings.openai_api_key

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

# 请求验证错误处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误（422错误）"""
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.error(f"请求验证失败 - URL: {request.url}")
    logger.error(f"验证错误详情: {errors}")
    
    return JSONResponse(
        status_code=422,
        content={
            "code": "422",
            "error": "请求数据验证失败",
            "message": "请检查请求参数格式",
            "details": errors,
            "processed_at": datetime.utcnow().isoformat()
        }
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
                
                async with httpx.AsyncClient(timeout=30.0) as client:
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

# 导入LangChain相关模块
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

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
        # 构建报告分析提示
        analysis_context = "对比分析" if historical_report else "首次分析"
        
        if report_type == "routineLab":
            data_section = f"""当前报告：{json.dumps(report_data, ensure_ascii=False, indent=2)}
{f'历史报告：{json.dumps(historical_report, ensure_ascii=False, indent=2)}' if historical_report else ''}"""            
            
            prompt = f"""
作为检验医学专家，{analysis_context}以下常规检验报告：

{data_section}

分析要点：
1. 异常指标识别及临床意义{"和变化趋势" if historical_report else ""}
2. 疾病风险评估{"和进展评价" if historical_report else ""}
3. 诊疗建议和生活指导

{"重点关注指标变化幅度、好转恶化趋势。" if historical_report else "注：首次报告，无对比数据。"}

请用中文专业但通俗地回答。
            """
        elif report_type == "microbiology":
            data_section = f"""当前报告：{json.dumps(report_data, ensure_ascii=False, indent=2)}
{f'历史报告：{json.dumps(historical_report, ensure_ascii=False, indent=2)}' if historical_report else ''}"""            
            
            prompt = f"""
作为微生物感染科专家，{analysis_context}以下微生物检验报告：

{data_section}

分析要点：
1. 病原菌识别及致病性评估{"及变化趋势" if historical_report else ""}
2. 药敏结果及耐药性分析{"及变化" if historical_report else ""}
3. 感染控制{"效果评估和" if historical_report else ""}治疗建议

{"重点关注耐药性变化和治疗效果。" if historical_report else "注：首次检验，重点关注药敏结果。"}

请用中文专业但通俗地回答。
            """
        elif report_type == "examination":
            data_section = f"""当前报告：{json.dumps(report_data, ensure_ascii=False, indent=2)}
{f'历史报告：{json.dumps(historical_report, ensure_ascii=False, indent=2)}' if historical_report else ''}"""            
            
            prompt = f"""
作为影像学专家，{analysis_context}以下检查报告：

{data_section}

分析要点：
1. 客观所见解读{"及变化对比" if historical_report else ""}
2. 主观提示的临床意义{"及变化" if historical_report else ""}
3. 诊断{"及进展" if historical_report else "和鉴别诊断"}建议

请用中文专业但通俗地回答。
            """
        elif report_type == "pathology":
            data_section = f"""当前报告：{json.dumps(report_data, ensure_ascii=False, indent=2)}
{f'历史报告：{json.dumps(historical_report, ensure_ascii=False, indent=2)}' if historical_report else ''}"""            
            
            prompt = f"""
作为病理学专家，{analysis_context}以下病理报告：

{data_section}

分析要点：
1. 病理形态学特征{"及变化" if historical_report else ""}解读
2. 诊断及临床意义{"、进展评估" if historical_report else ""}
3. 预后评估和治疗建议

请用中文专业但通俗地回答。
            """
        else:
            data_section = f"""当前报告：{json.dumps(report_data, ensure_ascii=False, indent=2)}
{f'历史报告：{json.dumps(historical_report, ensure_ascii=False, indent=2)}' if historical_report else ''}"""            
            
            prompt = f"""
作为医疗AI专家，{analysis_context}以下{report_type}报告：

{data_section}

分析要点：
1. 关键指标解读和异常识别
2. 临床意义分析
3. 后续处理建议

请用中文专业但通俗地回答。
            """
        # 使用LangChain调用大模型
        try:
            # 创建ChatOpenAI客户端
            llm = ChatOpenAI(
                model=LLM_MODEL,
                temperature=0.7,
                max_tokens=2000,
                openai_api_key=LLM_API_KEY if LLM_API_KEY != "sk-proj-1234567890" else None,
                base_url=LLM_API_URL,
                request_timeout=200,  # 300秒超时
                max_retries=2        # 最多重试2次
            )
            
            # 创建消息
            message = HumanMessage(content=prompt)
            
            # 调用模型
            response = await llm.ainvoke([message])
            analysis = response.content
            
            analysis_type = "对比分析" if historical_report else "单独分析"
            logger.info(f"LangChain分析成功 - 报告类型: {report_type}, 分析类型: {analysis_type}")
            return analysis
            
        except Exception as llm_error:
            logger.error(f"LangChain调用错误: {str(llm_error)}")
            # 降级返回基础分析
            return f"大模型服务暂不可用，基础分析：{report_type}报告已接收并存储，请稍后重试获取AI分析结果。"
                
    except asyncio.TimeoutError:
        logger.error("LLM分析超时")
        return "分析超时，请稍后重试"
    except Exception as e:
        logger.error(f"LLM分析错误: {str(e)}")
        return f"分析过程中发生错误，将使用基础分析"

# 兼容性包装函数（保留原有API）
def create_legacy_error_response(card_no: str, error_message: str) -> Dict[str, Any]:
    """创建传统格式的错误响应（兼容性）"""
    return {
        "code": "500",
        "cardNo": card_no,
        "error": error_message,
        "processed_at": datetime.utcnow().isoformat()
    }

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
    注册常规检验报告信息 - 使用优化后的统一处理服务
    """
    # 打印request
    logger.info(f"request: {request}")
    
    # 处理reportDate为None的情况，使用当前时间
    report_date = request.reportDate or datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 构建报告数据
    report_data = ReportData(
        card_no=request.cardNo,
        report_date=report_date,
        report_type=ReportType.ROUTINE_LAB,
        data={
            "cardNo": request.cardNo,
            "reportDate": report_date,
            "resultList": request.resultList
        }
    )
    # 打印report_data
    logger.info(f"report_data: {report_data}")
    # 使用统一的报告处理服务和错误处理
    result = await report_service.process_report(
        report_data, db, analyze_with_llm, 
        lambda card_no, msg: error_factory.processing_error(card_no, msg, "常规检验报告处理")
    )
    
    return RoutineLabReportResponse(
        code=result["code"],
        cardNo=result["cardNo"],
        processed_at=result["processed_at"],
        ai_analysis=result.get("ai_analysis", result.get("error", ""))
    )

@app.post("/microbiology", response_model=MicrobiologyReportResponse)
async def create_microbiology_report(
    request: MicrobiologyReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    注册微生物检验报告信息 - 使用优化后的统一处理服务
    """
    # 打印request
    logger.info(f"request: {request}")
    
    # 处理可选字段的默认值
    report_date = request.reportDate or datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 构建报告数据
    report_data = ReportData(
        card_no=request.cardNo,
        report_date=report_date,
        report_type=ReportType.MICROBIOLOGY,
        data={
            "cardNo": request.cardNo,
            "reportDate": report_date,
            "microbeResultList": request.microbeResultList,
            "bacterialResultList": request.bacterialResultList,
            "drugSensitivityList": request.drugSensitivityList,
            "diagnosisDate": request.diagnosisDate or "",
            "testResultCode": request.testResultCode or "",
            "testResultName": request.testResultName or "",
            "testQuantifyResult": request.testQuantifyResult or "",
            "testQuantifyResultUnit": request.testQuantifyResultUnit or ""
        },
        dept_code=request.deptCode or "",
        dept_name=request.deptName or "",
        diagnosis_code=request.diagnosisCode or "",
        diagnosis_name=request.diagnosisName or ""
    )
    # 打印report_data
    logger.info(f"report_data: {report_data}")
    # 使用统一的报告处理服务
    result = await report_service.process_report(
        report_data, db, analyze_with_llm, create_legacy_error_response
    )
    
    return MicrobiologyReportResponse(
        code=result["code"],
        cardNo=result["cardNo"],
        processed_at=result["processed_at"],
        ai_analysis=result.get("ai_analysis", result.get("error", ""))
    )

@app.post("/examination", response_model=ExaminationReportResponse)
async def create_examination_report(
    request: ExaminationReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    注册检查报告信息 - 使用优化后的统一处理服务
    """
    # 打印request
    logger.info(f"request: {request}")
    
    # 处理可选字段的默认值
    report_date = request.reportDate or datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 构建报告数据
    report_data = ReportData(
        card_no=request.cardNo,
        report_date=report_date,
        report_type=ReportType.EXAMINATION,
        data={
            "cardNo": request.cardNo,
            "reportDate": report_date,
            "patientNo": request.patientNo or "",
            "examResultCode": request.examResultCode or "",
            "examResultName": request.examResultName or "",
            "examQuantifyResult": request.examQuantifyResult or "",
            "examQuantifyResultUnit": request.examQuantifyResultUnit or "",
            "examObservation": request.examObservation or "",
            "examResult": request.examResult or ""
        },
        patient_no=request.patientNo or ""
    )
    # 打印report_data
    logger.info(f"report_data: {report_data}")
    # 使用统一的报告处理服务
    result = await report_service.process_report(
        report_data, db, analyze_with_llm, create_legacy_error_response
    )
    
    return ExaminationReportResponse(
        code=result["code"],
        cardNo=result["cardNo"],
        processed_at=result["processed_at"],
        ai_analysis=result.get("ai_analysis", result.get("error", ""))
    )

@app.post("/pathology", response_model=PathologyReportResponse)
async def create_pathology_report(
    request: PathologyReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    注册病理报告信息 - 使用优化后的统一处理服务
    """
    # 打印request
    logger.info(f"request: {request}")
    
    # 处理reportDate为None的情况，使用当前时间
    report_date = request.reportDate or datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 构建报告数据
    report_data = ReportData(
        card_no=request.cardNo,
        report_date=report_date,
        report_type=ReportType.PATHOLOGY,
        data={
            "cardNo": request.cardNo,
            "reportDate": report_date,
            "chiefComplaint": request.chiefComplaint or "",
            "symptomDescribe": request.symptomDescribe or "",
            "symptomStartTime": request.symptomStartTime or "",
            "symptomEndTime": request.symptomEndTime or "",
            "examResultCode": request.examResultCode or "",
            "examResultName": request.examResultName or "",
            "examQuantifyResult": request.examQuantifyResult or "",
            "examQuantifyResultUnit": request.examQuantifyResultUnit or "",
            "diagnosisDescribe": request.diagnosisDescribe or "",
            "examObservation": request.examObservation or "",
            "examResult": request.examResult or ""
        },
        patient_no=request.patientNo or "",
        dept_code=request.deptCode or "",
        dept_name=request.deptName or "",
        diagnosis_code=request.diagnosisCode or "",
        diagnosis_name=request.diagnosisName or ""
    )
    # 打印report_data
    logger.info(f"report_data: {report_data}")
    # 使用统一的报告处理服务
    result = await report_service.process_report(
        report_data, db, analyze_with_llm, create_legacy_error_response
    )
    
    return PathologyReportResponse(
        code=result["code"],
        cardNo=result["cardNo"],
        processed_at=result["processed_at"],
        ai_analysis=result.get("ai_analysis", result.get("error", ""))
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7700) 