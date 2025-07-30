"""
LangChain服务模块
使用LangChain框架进行医疗报告的历史对比分析
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from exceptions import handle_langchain_error, LangChainError, ErrorHandler
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.callbacks import get_openai_callback

# 设置日志
logger = logging.getLogger(__name__)

class MedicalReportAnalyzer:
    """医疗报告分析器 - 使用LangChain进行历史报告对比分析"""
    
    def __init__(self):
        """初始化分析器"""
        # 配置OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # 如果没有配置OpenAI，使用本地模型
        if not self.openai_api_key:
            logger.warning("未配置OpenAI API Key, 将使用本地模型")
            self.use_local_model = True
        else:
            self.use_local_model = False
            
        # 初始化LangChain模型
        self._init_langchain_model()
        
        # 初始化Prompt模板
        self._init_prompt_templates()
    
    def _init_langchain_model(self):
        """初始化LangChain模型"""
        try:
            if not self.use_local_model:
                # 使用OpenAI模型
                self.llm = ChatOpenAI(
                    openai_api_key=self.openai_api_key,
                    openai_api_base=self.openai_api_base,
                    model_name=self.model_name,
                    temperature=0.7,
                    max_tokens=3000
                )
                logger.info(f"初始化OpenAI模型: {self.model_name}")
            else:
                # 使用本地模型（这里可以配置本地Ollama或其他模型）
                from langchain_community.llms import Ollama
                self.llm = Ollama(
                    model="llama3.1",
                    base_url="http://localhost:11434"
                )
                logger.info("初始化本地Ollama模型")
        except Exception as e:
            raise handle_langchain_error("模型初始化", "system", e)
    
    def _init_prompt_templates(self):
        """初始化Prompt模板"""
        
        # 常规检验报告对比分析模板
        self.routine_lab_comparison_template = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
            你是一位专业的临床检验医学专家，擅长分析常规检验报告的历史变化趋势。
            请根据患者的历史检验报告数据，对比分析当前报告与历史报告的变化情况。
            
            分析要求：
            1. 识别关键指标的变化趋势（上升、下降、稳定）
            2. 评估异常指标的临床意义
            3. 分析病情发展趋势和潜在风险
            4. 提供个性化的医疗建议
            5. 识别需要特别关注的指标变化
            
            输出格式要求：
            - 使用专业但通俗易懂的中文
            - 结构化输出，包含：趋势分析、风险评估、医疗建议
            - 突出关键变化和异常指标
            """),
            HumanMessage(content="""
            患者卡号: {card_no}
            对比时间段: {comparison_period}
            
            当前报告 (日期: {current_date}):
            {current_report}
            
            历史报告数据 (共{history_count}份):
            {historical_reports}
            
            请进行详细的对比分析。
            """)
        ])
        
        # 微生物检验报告对比分析模板
        self.microbiology_comparison_template = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
            你是一位专业的微生物学和感染科专家，擅长分析微生物检验报告的变化趋势。
            请根据患者的历史微生物检验报告，对比分析感染情况的变化。
            
            分析要求：
            1. 分析病原菌种类和数量的变化
            2. 评估药敏结果的变化趋势
            3. 判断感染控制效果
            4. 识别耐药性发展趋势
            5. 提供抗感染治疗建议
            
            输出格式要求：
            - 专业术语与通俗解释相结合
            - 重点关注耐药性和治疗效果
            - 提供个性化的抗感染方案建议
            """),
            HumanMessage(content="""
            患者卡号: {card_no}
            对比时间段: {comparison_period}
            
            当前报告 (日期: {current_date}):
            {current_report}
            
            历史报告数据 (共{history_count}份):
            {historical_reports}
            
            请进行详细的微生物学对比分析。
            """)
        ])
        
        # 检查报告对比分析模板
        self.examination_comparison_template = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
            你是一位专业的影像学和临床医学专家，擅长分析各类检查报告的变化趋势。
            请根据患者的历史检查报告，对比分析疾病进展情况。
            
            分析要求：
            1. 对比影像学或检查结果的变化
            2. 分析病变的进展、稳定或好转情况
            3. 评估治疗效果和预后
            4. 识别新出现的异常发现
            5. 提供后续检查和治疗建议
            
            输出格式要求：
            - 重点关注形态学和功能性变化
            - 结合临床意义进行解读
            - 提供个性化的随访建议
            """),
            HumanMessage(content="""
            患者卡号: {card_no}
            对比时间段: {comparison_period}
            
            当前报告 (日期: {current_date}):
            {current_report}
            
            历史报告数据 (共{history_count}份):
            {historical_reports}
            
            请进行详细的检查结果对比分析。
            """)
        ])
        
        # 病理报告对比分析模板
        self.pathology_comparison_template = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
            你是一位专业的病理学专家，擅长分析病理报告的变化和疾病进展。
            请根据患者的历史病理报告，对比分析疾病的病理学变化。
            
            分析要求：
            1. 分析病理形态学的变化趋势
            2. 评估疾病进展、转归或复发情况
            3. 分析治疗反应和预后指标
            4. 识别恶性转化或进展风险
            5. 提供个性化的治疗和随访建议
            
            输出格式要求：
            - 重点关注病理分级和分期变化
            - 结合分子病理学指标进行分析
            - 提供循证医学的治疗建议
            """),
            HumanMessage(content="""
            患者卡号: {card_no}
            对比时间段: {comparison_period}
            
            当前报告 (日期: {current_date}):
            {current_report}
            
            历史报告数据 (共{history_count}份):
            {historical_reports}
            
            请进行详细的病理学对比分析。
            """)
        ])
    
    def _get_comparison_template(self, report_type: str) -> ChatPromptTemplate:
        """根据报告类型获取对应的对比分析模板"""
        template_map = {
            "routine_lab": self.routine_lab_comparison_template,
            "microbiology": self.microbiology_comparison_template,
            "examination": self.examination_comparison_template,
            "pathology": self.pathology_comparison_template
        }
        return template_map.get(report_type, self.routine_lab_comparison_template)
    
    def _format_report_data(self, report_data: Dict[str, Any], report_type: str) -> str:
        """格式化报告数据为便于分析的文本"""
        try:
            if report_type == "routine_lab":
                # 常规检验报告格式化
                if 'result_list' in report_data:
                    results = report_data['result_list']
                    formatted_text = "检验项目及结果：\n"
                    if isinstance(results, list):
                        for item in results:
                            if isinstance(item, dict):
                                name = item.get('name', '未知项目')
                                value = item.get('value', '未知值')
                                unit = item.get('unit', '')
                                reference = item.get('reference', '')
                                formatted_text += f"- {name}: {value} {unit}"
                                if reference:
                                    formatted_text += f" (参考值: {reference})"
                                formatted_text += "\n"
                    return formatted_text
                    
            elif report_type == "microbiology":
                # 微生物检验报告格式化
                formatted_text = "微生物检验结果：\n"
                if 'microbe_result_list' in report_data:
                    formatted_text += f"微生物培养: {report_data['microbe_result_list']}\n"
                if 'bacterial_result_list' in report_data:
                    formatted_text += f"细菌鉴定: {report_data['bacterial_result_list']}\n"
                if 'drug_sensitivity_list' in report_data:
                    formatted_text += f"药敏结果: {report_data['drug_sensitivity_list']}\n"
                return formatted_text
                
            elif report_type == "examination":
                # 检查报告格式化
                formatted_text = "检查报告结果：\n"
                if 'exam_observation' in report_data:
                    formatted_text += f"客观所见: {report_data['exam_observation']}\n"
                if 'exam_result' in report_data:
                    formatted_text += f"主观提示: {report_data['exam_result']}\n"
                return formatted_text
                
            elif report_type == "pathology":
                # 病理报告格式化
                formatted_text = "病理报告结果：\n"
                if 'diagnosis_name' in report_data:
                    formatted_text += f"诊断: {report_data['diagnosis_name']}\n"
                if 'exam_observation' in report_data:
                    formatted_text += f"镜下所见: {report_data['exam_observation']}\n"
                if 'exam_result' in report_data:
                    formatted_text += f"病理诊断: {report_data['exam_result']}\n"
                return formatted_text
            
            # 默认格式化
            return json.dumps(report_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"格式化报告数据失败: {e}")
            # 返回JSON格式作为备选方案
            return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def _extract_key_changes(self, analysis_text: str) -> Dict[str, Any]:
        """从分析文本中提取关键变化信息"""
        try:
            # 简单的关键词提取，实际应用中可以使用更复杂的NLP技术
            key_changes = {
                "significant_changes": [],
                "trends": [],
                "abnormal_values": [],
                "recommendations": []
            }
            
            # 分析文本中的关键词
            if "上升" in analysis_text or "增高" in analysis_text or "升高" in analysis_text:
                key_changes["trends"].append("指标上升")
            if "下降" in analysis_text or "降低" in analysis_text or "减少" in analysis_text:
                key_changes["trends"].append("指标下降")
            if "异常" in analysis_text or "超标" in analysis_text or "偏高" in analysis_text or "偏低" in analysis_text:
                key_changes["abnormal_values"].append("存在异常值")
            if "建议" in analysis_text or "推荐" in analysis_text:
                key_changes["recommendations"].append("需要关注")
            
            return key_changes
            
        except Exception as e:
            logger.error(f"提取关键变化失败: {e}")
            # 返回空的关键变化字典
            return {
                "significant_changes": [],
                "trends": [],
                "abnormal_values": [],
                "recommendations": []
            }
    
    def _calculate_analysis_confidence(self, historical_reports_count: int, analysis_text: str) -> str:
        """计算分析置信度"""
        try:
            # 基于历史报告数量和分析文本长度计算置信度
            if historical_reports_count >= 5 and len(analysis_text) > 500:
                return "高"
            elif historical_reports_count >= 3 and len(analysis_text) > 300:
                return "中"
            else:
                return "低"
        except:
            return "未知"
    
    async def compare_reports(
        self,
        card_no: str,
        report_type: str,
        current_report: Dict[str, Any],
        historical_reports: List[Dict[str, Any]],
        comparison_period: str = "6months"
    ) -> Dict[str, Any]:
        """
        使用LangChain进行历史报告对比分析
        
        Args:
            card_no: 患者卡号
            report_type: 报告类型
            current_report: 当前报告数据
            historical_reports: 历史报告数据列表
            comparison_period: 对比时间段
            
        Returns:
            对比分析结果
        """
        try:
            logger.info(f"开始对比分析 - 患者: {card_no}, 报告类型: {report_type}")
            
            # 获取对应的模板
            template = self._get_comparison_template(report_type)
            
            # 格式化当前报告数据
            current_report_text = self._format_report_data(current_report, report_type)
            current_date = current_report.get('report_date', current_report.get('created_at', '未知'))
            
            # 格式化历史报告数据
            historical_reports_text = ""
            for i, report in enumerate(historical_reports, 1):
                report_date = report.get('report_date', report.get('created_at', '未知'))
                report_text = self._format_report_data(report, report_type)
                historical_reports_text += f"\n第{i}份历史报告 (日期: {report_date}):\n{report_text}\n"
            
            # 构建分析链
            analysis_chain = LLMChain(
                llm=self.llm,
                prompt=template,
                verbose=True
            )
            
            # 执行分析
            if not self.use_local_model:
                # 使用OpenAI时跟踪token使用
                with get_openai_callback() as cb:
                    analysis_result = await analysis_chain.ainvoke({
                        "card_no": card_no,
                        "comparison_period": comparison_period,
                        "current_date": current_date,
                        "current_report": current_report_text,
                        "history_count": len(historical_reports),
                        "historical_reports": historical_reports_text
                    })
                    tokens_used = cb.total_tokens
            else:
                # 使用本地模型
                analysis_result = await analysis_chain.ainvoke({
                    "card_no": card_no,
                    "comparison_period": comparison_period,
                    "current_date": current_date,
                    "current_report": current_report_text,
                    "history_count": len(historical_reports),
                    "historical_reports": historical_reports_text
                })
                tokens_used = 0
            
            # 从LangChain 0.3的返回结果中提取文本内容
            if isinstance(analysis_result, dict) and 'text' in analysis_result:
                analysis_text = analysis_result['text']
            elif hasattr(analysis_result, 'content'):
                analysis_text = analysis_result.content
            else:
                analysis_text = str(analysis_result)
            
            # 提取关键变化
            key_changes = self._extract_key_changes(analysis_text)
            
            # 计算置信度
            confidence = self._calculate_analysis_confidence(len(historical_reports), analysis_text)
            
            # 分析结果分段
            result_sections = analysis_text.split('\n\n')
            trend_analysis = ""
            risk_assessment = ""
            recommendations = ""
            
            # 简单的文本分段逻辑
            for section in result_sections:
                if any(keyword in section for keyword in ['趋势', '变化', '发展']):
                    trend_analysis += section + "\n"
                elif any(keyword in section for keyword in ['风险', '评估', '危险']):
                    risk_assessment += section + "\n"
                elif any(keyword in section for keyword in ['建议', '推荐', '注意']):
                    recommendations += section + "\n"
            
            # 从LangChain 0.3的返回结果中提取文本内容
            if isinstance(analysis_result, dict) and 'text' in analysis_result:
                analysis_text = analysis_result['text']
            elif hasattr(analysis_result, 'content'):
                analysis_text = analysis_result.content
            else:
                analysis_text = str(analysis_result)
            
            return {
                "langchain_analysis": analysis_text,
                "key_changes": key_changes,
                "trend_analysis": trend_analysis.strip() or "未识别到明显趋势",
                "risk_assessment": risk_assessment.strip() or "风险评估需要更多数据",
                "recommendations": recommendations.strip() or "建议咨询专业医生",
                "analysis_model": self.model_name if not self.use_local_model else "llama3.1",
                "analysis_confidence": confidence,
                "tokens_used": tokens_used
            }
            
        except LangChainError:
            # 重新抛出已经处理过的LangChain错误
            raise
        except Exception as e:
            # 处理其他未预期的错误
            langchain_error = handle_langchain_error("报告对比分析", card_no, e)
            return {
                "langchain_analysis": f"分析过程中发生错误: {langchain_error.message}",
                "key_changes": {},
                "trend_analysis": "分析失败",
                "risk_assessment": "无法评估",
                "recommendations": "请联系技术支持",
                "analysis_model": "error",
                "analysis_confidence": "无",
                "tokens_used": 0
            }

# 创建全局分析器实例
medical_analyzer = MedicalReportAnalyzer() 