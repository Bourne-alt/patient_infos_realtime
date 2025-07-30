"""
LangChain 链式工作流样例代码
展示8种工作流模式：简单链、顺序链、分支链、记忆链、解析器链、Agent工作流、LCEL管道操作符、复合工作流等
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dotenv import load_dotenv

# LangChain 核心导入
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.chains import LLMChain, SequentialChain, RouterChain, MultiRetrievalQAChain
from langchain.chains.router.llm_router import LLMRouterChain
from langchain.chains.router.multi_retrieval_prompt import MULTI_RETRIEVAL_ROUTER_TEMPLATE
from langchain.chains.router import MultiRouteChain
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory, ConversationBufferWindowMemory
from langchain.schema import BaseOutputParser, OutputParserException
from langchain.callbacks import StdOutCallbackHandler
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain.tools import BaseTool
from langchain.schema import AgentAction, AgentFinish
from langchain.agents.react.base import DocstoreExplorer
from langchain.docstore import InMemoryDocstore
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

# LCEL (LangChain Expression Language) 导入
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough, RunnableParallel
from langchain.schema.runnable.config import RunnableConfig
from langchain.schema import BaseMessage

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class MedicalWorkflowExample:
    """医疗工作流样例类"""
    
    def __init__(self):
        """初始化工作流"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")
        
        # 初始化模型
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model_name="gpt-4o",
            temperature=0.7
        )
        
        self.simple_llm = OpenAI(
            openai_api_key=self.api_key,
            temperature=0.7
        )
        
        # 初始化记忆
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        logger.info("医疗工作流初始化完成")
    
    # ==================== 1. 简单链 (Simple Chain) ====================
    def create_simple_chain(self) -> LLMChain:
        """创建简单链 - 患者症状分析"""
        
        prompt = PromptTemplate(
            input_variables=["symptoms", "patient_age", "gender"],
            template="""
            作为一名专业的医疗助手，请分析以下患者信息：
            
            患者年龄：{patient_age}
            患者性别：{gender}
            症状描述：{symptoms}
            
            请提供：
            1. 可能的诊断方向
            2. 建议的检查项目
            3. 注意事项
            
            回答：
            """
        )
        
        chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            output_key="analysis_result"
        )
        
        return chain
    
    # ==================== 2. 顺序链 (Sequential Chain) ====================
    def create_sequential_chain(self) -> SequentialChain:
        """创建顺序链 - 完整的医疗分析流程"""
        
        # 第一步：症状分析
        symptom_analysis_prompt = PromptTemplate(
            input_variables=["symptoms", "patient_info"],
            template="""
            患者信息：{patient_info}
            症状：{symptoms}
            
            请分析患者症状，提供可能的疾病方向。
            输出格式：简洁的疾病分析，不超过200字。
            """
        )
        
        symptom_chain = LLMChain(
            llm=self.llm,
            prompt=symptom_analysis_prompt,
            output_key="symptom_analysis"
        )
        
        # 第二步：检查建议
        examination_prompt = PromptTemplate(
            input_variables=["symptom_analysis", "patient_info"],
            template="""
            患者信息：{patient_info}
            症状分析：{symptom_analysis}
            
            基于以上分析，请推荐具体的检查项目和优先级。
            输出格式：检查项目列表，包含优先级。
            """
        )
        
        examination_chain = LLMChain(
            llm=self.llm,
            prompt=examination_prompt,
            output_key="examination_plan"
        )
        
        # 第三步：治疗建议
        treatment_prompt = PromptTemplate(
            input_variables=["symptom_analysis", "examination_plan", "patient_info"],
            template="""
            患者信息：{patient_info}
            症状分析：{symptom_analysis}
            检查计划：{examination_plan}
            
            请提供初步的治疗建议和生活指导。
            输出格式：治疗建议和注意事项。
            """
        )
        
        treatment_chain = LLMChain(
            llm=self.llm,
            prompt=treatment_prompt,
            output_key="treatment_plan"
        )
        
        # 组合成顺序链
        sequential_chain = SequentialChain(
            chains=[symptom_chain, examination_chain, treatment_chain],
            input_variables=["symptoms", "patient_info"],
            output_variables=["symptom_analysis", "examination_plan", "treatment_plan"],
            verbose=True
        )
        
        return sequential_chain
    
    # ==================== 3. 分支链 (Router Chain) ====================
    def create_router_chain(self) -> MultiRouteChain:
        """创建分支链 - 根据不同科室分发查询"""
        
        # 内科链
        internal_medicine_prompt = PromptTemplate(
            input_variables=["query"],
            template="""
            作为内科医生，请回答以下问题：{query}
            
            请从内科角度提供专业的分析和建议。
            """
        )
        
        internal_medicine_chain = LLMChain(
            llm=self.llm,
            prompt=internal_medicine_prompt,
            output_key="result"
        )
        
        # 外科链
        surgery_prompt = PromptTemplate(
            input_variables=["query"],
            template="""
            作为外科医生，请回答以下问题：{query}
            
            请从外科角度提供专业的分析和建议。
            """
        )
        
        surgery_chain = LLMChain(
            llm=self.llm,
            prompt=surgery_prompt,
            output_key="result"
        )
        
        # 儿科链
        pediatrics_prompt = PromptTemplate(
            input_variables=["query"],
            template="""
            作为儿科医生，请回答以下问题：{query}
            
            请从儿科角度提供专业的分析和建议，特别注意儿童的特殊性。
            """
        )
        
        pediatrics_chain = LLMChain(
            llm=self.llm,
            prompt=pediatrics_prompt,
            output_key="result"
        )
        
        # 默认链
        default_prompt = PromptTemplate(
            input_variables=["query"],
            template="""
            作为全科医生，请回答以下问题：{query}
            
            请提供综合的医疗建议。
            """
        )
        
        default_chain = LLMChain(
            llm=self.llm,
            prompt=default_prompt,
            output_key="result"
        )
        
        # 路由器模板
        router_template = """
        给定一个医疗查询，选择最合适的专科来回答。
        
        可选专科：
        internal_medicine: 内科相关问题，如发热、咳嗽、高血压、糖尿病等
        surgery: 外科相关问题，如外伤、手术、疼痛等
        pediatrics: 儿科相关问题，涉及儿童患者
        
        查询: {input}
        
        请选择: internal_medicine, surgery, pediatrics 中的一个，或选择 DEFAULT
        """
        
        router_prompt = PromptTemplate(
            template=router_template,
            input_variables=["input"],
            output_parser=None
        )
        
        router_chain = LLMRouterChain.from_llm(
            llm=self.llm,
            prompt=router_prompt
        )
        
        # 创建多路由链
        destination_chains = {
            "internal_medicine": internal_medicine_chain,
            "surgery": surgery_chain,
            "pediatrics": pediatrics_chain
        }
        
        multi_route_chain = MultiRouteChain(
            router_chain=router_chain,
            destination_chains=destination_chains,
            default_chain=default_chain,
            verbose=True
        )
        
        return multi_route_chain
    
    # ==================== 4. 记忆链 (Memory Chain) ====================
    def create_memory_chain(self) -> LLMChain:
        """创建带记忆的链 - 连续对话"""
        
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            input_key="query",
            k=5  # 保留最近5轮对话
        )
        
        prompt = PromptTemplate(
            input_variables=["chat_history", "query"],
            template="""
            以下是我们之前的对话历史：
            {chat_history}
            
            当前问题：{query}
            
            作为医疗助手，请基于对话历史为患者提供连贯的医疗建议。
            
            回答：
            """
        )
        
        memory_chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            memory=memory,
            verbose=True
        )
        
        return memory_chain
    
    # ==================== 5. 自定义输出解析器 ====================
    class MedicalAnalysisParser(BaseOutputParser):
        """医疗分析结果解析器"""
        
        def parse(self, text: str) -> Dict[str, str]:
            """解析医疗分析结果"""
            result = {}
            
            # 简单解析逻辑
            if "诊断" in text or "可能" in text:
                result["diagnosis"] = text.split("诊断")[-1].split("\n")[0] if "诊断" in text else "需要进一步检查"
            
            if "建议" in text:
                result["recommendations"] = text.split("建议")[-1].split("\n")[0] if "建议" in text else "暂无建议"
            
            if "注意" in text:
                result["precautions"] = text.split("注意")[-1].split("\n")[0] if "注意" in text else "暂无注意事项"
            
            result["full_analysis"] = text
            
            return result
    
    def create_parsed_chain(self) -> LLMChain:
        """创建带解析器的链"""
        
        prompt = PromptTemplate(
            input_variables=["symptoms"],
            template="""
            症状：{symptoms}
            
            请提供：
            1. 可能的诊断
            2. 治疗建议
            3. 注意事项
            
            回答：
            """
        )
        
        chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            output_parser=self.MedicalAnalysisParser()
        )
        
        return chain
    
    # ==================== 6. 工具定义 ====================
    class PatientInfoTool(BaseTool):
        """患者信息查询工具"""
        name = "patient_info_lookup"
        description = "用于查询患者基本信息，输入患者ID"
        
        def _run(self, patient_id: str) -> str:
            # 模拟患者信息查询
            patient_data = {
                "001": "张三，男，45岁，患有高血压和糖尿病",
                "002": "李四，女，32岁，无既往病史",
                "003": "王五，男，65岁，有心脏病史"
            }
            
            return patient_data.get(patient_id, "未找到该患者信息")
        
        def _arun(self, patient_id: str) -> str:
            return self._run(patient_id)
    
    class SymptomAnalysisTool(BaseTool):
        """症状分析工具"""
        name = "symptom_analysis"
        description = "用于分析患者症状，输入症状描述"
        
        def _run(self, symptoms: str) -> str:
            # 简单的症状分析逻辑
            if "发热" in symptoms:
                return "可能存在感染，建议检查血常规"
            elif "胸痛" in symptoms:
                return "需要排除心脏疾病，建议做心电图"
            elif "头痛" in symptoms:
                return "可能为偏头痛或血压问题，建议测量血压"
            else:
                return "需要更详细的症状描述进行分析"
        
        def _arun(self, symptoms: str) -> str:
            return self._run(symptoms)
    
    # ==================== 7. Agent 工作流 ====================
    def create_agent_workflow(self) -> AgentExecutor:
        """创建Agent工作流"""
        
        # 创建工具
        tools = [
            self.PatientInfoTool(),
            self.SymptomAnalysisTool()
        ]
        
        # 创建Agent提示
        agent_prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad"],
            template="""
            你是一个医疗助手Agent，可以使用以下工具：
            
            {tools}
            
            用户输入：{input}
            
            思考过程：
            {agent_scratchpad}
            
            请使用适当的工具来回答用户问题。
            """
        )
        
        # 创建Agent
        agent = create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=agent_prompt
        )
        
        # 创建Agent执行器
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    # ==================== 8. LCEL 管道操作符工作流 ====================
    def create_lcel_pipeline_workflow(self) -> Dict[str, Any]:
        """创建使用 | 管道操作符的 LCEL 工作流"""
        
        # 1. 简单管道链 - 症状分析
        simple_pipeline = (
            PromptTemplate.from_template(
                "作为医疗助手，分析以下症状：{symptoms}\n请提供简洁的分析："
            )
            | self.llm
            | StrOutputParser()
        )
        
        # 2. 复杂管道链 - 多步骤处理
        # 第一步：提取患者信息
        extract_info_prompt = PromptTemplate.from_template(
            """从以下文本中提取患者信息：
            {input_text}
            
            请提取：年龄、性别、主要症状
            格式：年龄：X岁，性别：X，症状：X"""
        )
        
        # 第二步：症状分析
        analyze_symptoms_prompt = PromptTemplate.from_template(
            """基于患者信息进行症状分析：
            {patient_info}
            
            请提供可能的诊断和建议检查："""
        )
        
        # 第三步：治疗建议
        treatment_prompt = PromptTemplate.from_template(
            """基于以下信息提供治疗建议：
            患者信息：{patient_info}
            症状分析：{symptom_analysis}
            
            请提供治疗建议和注意事项："""
        )
        
        # 组合成复杂管道
        complex_pipeline = (
            {
                "patient_info": extract_info_prompt | self.llm | StrOutputParser(),
                "input_text": RunnablePassthrough()
            }
            | RunnablePassthrough.assign(
                symptom_analysis=analyze_symptoms_prompt | self.llm | StrOutputParser()
            )
            | treatment_prompt
            | self.llm
            | StrOutputParser()
        )
        
        # 3. 并行处理管道
        parallel_analysis_pipeline = RunnableParallel(
            # 内科分析
            internal_medicine=(
                PromptTemplate.from_template(
                    "从内科角度分析：{symptoms}\n内科建议："
                )
                | self.llm
                | StrOutputParser()
            ),
            # 急诊科分析
            emergency=(
                PromptTemplate.from_template(
                    "从急诊科角度评估：{symptoms}\n紧急程度和处理："
                )
                | self.llm
                | StrOutputParser()
            ),
            # 预防医学分析
            preventive=(
                PromptTemplate.from_template(
                    "从预防医学角度建议：{symptoms}\n预防措施："
                )
                | self.llm
                | StrOutputParser()
            )
        )
        
        # 4. 条件分支管道
        def route_by_age(inputs):
            """根据年龄路由到不同的分析管道"""
            age_text = inputs.get("age", "")
            try:
                age = int(age_text)
                if age < 18:
                    return "pediatric"
                elif age >= 65:
                    return "geriatric"
                else:
                    return "adult"
            except:
                return "adult"
        
        # 儿科管道
        pediatric_pipeline = (
            PromptTemplate.from_template(
                "儿科医生分析：患者{age}岁，症状：{symptoms}\n儿科专业建议："
            )
            | self.llm
            | StrOutputParser()
        )
        
        # 成人管道
        adult_pipeline = (
            PromptTemplate.from_template(
                "成人医学分析：患者{age}岁，症状：{symptoms}\n成人医学建议："
            )
            | self.llm
            | StrOutputParser()
        )
        
        # 老年医学管道
        geriatric_pipeline = (
            PromptTemplate.from_template(
                "老年医学分析：患者{age}岁，症状：{symptoms}\n老年医学专业建议："
            )
            | self.llm
            | StrOutputParser()
        )
        
        # 5. 带记忆的管道链
        memory_pipeline = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x.get("chat_history", [])
            }
            | PromptTemplate.from_template(
                """对话历史：{chat_history}
                
                当前问题：{input}
                
                作为医疗助手，基于对话历史提供连贯的回答："""
            )
            | self.llm
            | StrOutputParser()
        )
        
        # 6. 多格式输出管道
        structured_output_pipeline = (
            PromptTemplate.from_template(
                """分析症状：{symptoms}
                
                请以以下JSON格式输出：
                {{
                    "diagnosis": "可能诊断",
                    "severity": "严重程度(轻度/中度/重度)",
                    "urgency": "紧急程度(低/中/高)",
                    "recommendations": ["建议1", "建议2"],
                    "next_steps": "下一步行动"
                }}"""
            )
            | self.llm
            | StrOutputParser()
        )
        
        return {
            "simple_pipeline": simple_pipeline,
            "complex_pipeline": complex_pipeline,
            "parallel_analysis": parallel_analysis_pipeline,
            "conditional_routing": {
                "router": route_by_age,
                "pediatric": pediatric_pipeline,
                "adult": adult_pipeline,
                "geriatric": geriatric_pipeline
            },
            "memory_pipeline": memory_pipeline,
            "structured_output": structured_output_pipeline
        }
    
    # ==================== 9. 复合工作流 ====================
    async def create_complex_workflow(self) -> Dict[str, Any]:
        """创建复合工作流 - 结合多种链"""
        
        # 患者信息预处理链
        preprocess_prompt = PromptTemplate(
            input_variables=["raw_input"],
            template="""
            原始输入：{raw_input}
            
            请提取其中的关键信息：
            1. 患者基本信息（年龄、性别等）
            2. 症状描述
            3. 查询类型（诊断、治疗、预防等）
            
            输出格式：
            基本信息：
            症状：
            查询类型：
            """
        )
        
        preprocess_chain = LLMChain(
            llm=self.llm,
            prompt=preprocess_prompt,
            output_key="processed_info"
        )
        
        # 专业分析链
        analysis_prompt = PromptTemplate(
            input_variables=["processed_info"],
            template="""
            基于以下信息进行专业分析：
            {processed_info}
            
            请提供：
            1. 专业的医疗分析
            2. 诊断建议
            3. 治疗方案
            4. 注意事项
            
            回答：
            """
        )
        
        analysis_chain = LLMChain(
            llm=self.llm,
            prompt=analysis_prompt,
            output_key="analysis_result"
        )
        
        # 报告生成链
        report_prompt = PromptTemplate(
            input_variables=["processed_info", "analysis_result"],
            template="""
            患者信息：{processed_info}
            
            分析结果：{analysis_result}
            
            请生成一份结构化的医疗报告，包含：
            1. 患者摘要
            2. 症状分析
            3. 诊断结论
            4. 治疗建议
            5. 随访计划
            
            医疗报告：
            """
        )
        
        report_chain = LLMChain(
            llm=self.llm,
            prompt=report_prompt,
            output_key="medical_report"
        )
        
        # 组合成复合链
        complex_chain = SequentialChain(
            chains=[preprocess_chain, analysis_chain, report_chain],
            input_variables=["raw_input"],
            output_variables=["processed_info", "analysis_result", "medical_report"],
            verbose=True
        )
        
        return {
            "complex_chain": complex_chain,
            "preprocess_chain": preprocess_chain,
            "analysis_chain": analysis_chain,
            "report_chain": report_chain
        }
    
    # ==================== 10. 演示函数 ====================
    async def demonstrate_workflows(self):
        """演示所有工作流"""
        print("="*60)
        print("🏥 LangChain 医疗工作流演示")
        print("="*60)
        
        # 1. 简单链演示
        print("\n1️⃣ 简单链演示 - 症状分析")
        print("-" * 40)
        simple_chain = self.create_simple_chain()
        result = simple_chain.run({
            "symptoms": "头痛、发热、咳嗽",
            "patient_age": "35",
            "gender": "女"
        })
        print(f"分析结果：{result}")
        
        # 2. 顺序链演示
        print("\n2️⃣ 顺序链演示 - 完整医疗流程")
        print("-" * 40)
        sequential_chain = self.create_sequential_chain()
        result = sequential_chain.run({
            "symptoms": "胸痛、气短",
            "patient_info": "45岁男性，有高血压史"
        })
        print(f"症状分析：{result['symptom_analysis']}")
        print(f"检查计划：{result['examination_plan']}")
        print(f"治疗方案：{result['treatment_plan']}")
        
        # 3. 分支链演示
        print("\n3️⃣ 分支链演示 - 科室分发")
        print("-" * 40)
        router_chain = self.create_router_chain()
        result = router_chain.run("3岁儿童反复发热")
        print(f"专科建议：{result}")
        
        # 4. 记忆链演示
        print("\n4️⃣ 记忆链演示 - 连续对话")
        print("-" * 40)
        memory_chain = self.create_memory_chain()
        
        # 第一轮对话
        result1 = memory_chain.run("我有点头痛")
        print(f"第一轮回答：{result1}")
        
        # 第二轮对话
        result2 = memory_chain.run("这种情况持续了三天")
        print(f"第二轮回答：{result2}")
        
        # 5. 解析器链演示
        print("\n5️⃣ 解析器链演示 - 结构化输出")
        print("-" * 40)
        parsed_chain = self.create_parsed_chain()
        result = parsed_chain.run("腹痛、恶心、呕吐")
        print(f"解析结果：{result}")
        
        # 6. Agent演示
        print("\n6️⃣ Agent演示 - 工具使用")
        print("-" * 40)
        agent = self.create_agent_workflow()
        result = agent.run("查询患者001的信息，并分析发热症状")
        print(f"Agent结果：{result}")
        
        # 7. LCEL 管道操作符演示
        print("\n7️⃣ LCEL 管道操作符演示 - 现代语法")
        print("-" * 40)
        lcel_workflows = self.create_lcel_pipeline_workflow()
        
        # 7.1 简单管道演示
        print("  📌 简单管道 (prompt | llm | parser):")
        simple_result = lcel_workflows["simple_pipeline"].invoke({
            "symptoms": "持续性头痛伴恶心"
        })
        print(f"    结果: {simple_result}")
        
        # 7.2 并行处理管道演示
        print("\n  📌 并行分析管道:")
        parallel_result = lcel_workflows["parallel_analysis"].invoke({
            "symptoms": "胸闷、心悸、出汗"
        })
        print(f"    内科观点: {parallel_result['internal_medicine']}")
        print(f"    急诊观点: {parallel_result['emergency']}")
        print(f"    预防观点: {parallel_result['preventive']}")
        
        # 7.3 条件路由管道演示
        print("\n  📌 条件路由管道:")
        routing_config = lcel_workflows["conditional_routing"]
        
        # 儿童患者
        child_input = {"age": "8", "symptoms": "发热、咳嗽"}
        route = routing_config["router"](child_input)
        child_result = routing_config[route].invoke(child_input)
        print(f"    儿童患者路由到: {route}")
        print(f"    分析结果: {child_result}")
        
        # 老年患者
        elderly_input = {"age": "75", "symptoms": "胸痛、气短"}
        route = routing_config["router"](elderly_input)
        elderly_result = routing_config[route].invoke(elderly_input)
        print(f"    老年患者路由到: {route}")
        print(f"    分析结果: {elderly_result}")
        
        # 7.4 结构化输出管道演示
        print("\n  📌 结构化输出管道:")
        structured_result = lcel_workflows["structured_output"].invoke({
            "symptoms": "剧烈腹痛、呕吐、发热"
        })
        print(f"    JSON格式输出: {structured_result}")
        
        # 7.5 记忆管道演示
        print("\n  📌 记忆管道演示:")
        memory_pipeline = lcel_workflows["memory_pipeline"]
        
        # 第一轮对话
        result1 = memory_pipeline.invoke({
            "input": "我经常头痛",
            "chat_history": []
        })
        print(f"    第一轮: {result1}")
        
        # 第二轮对话（带历史）
        result2 = memory_pipeline.invoke({
            "input": "这种头痛已经持续一周了",
            "chat_history": [f"用户: 我经常头痛\n助手: {result1}"]
        })
        print(f"    第二轮: {result2}")
        
        # 8. 复合工作流演示
        print("\n8️⃣ 复合工作流演示 - 综合分析")
        print("-" * 40)
        complex_workflows = await self.create_complex_workflow()
        complex_chain = complex_workflows["complex_chain"]
        result = complex_chain.run({
            "raw_input": "我是30岁女性，最近几天一直头痛，还伴有恶心症状，请帮我分析一下"
        })
        print(f"医疗报告：{result['medical_report']}")
        
        print("\n" + "="*60)
        print("🎉 所有8种工作流演示完成！")
        print("包含：简单链、顺序链、分支链、记忆链、解析器链、Agent工作流、LCEL管道操作符、复合工作流")
        print("="*60)

# ==================== 主函数 ====================
async def main():
    """主函数"""
    try:
        # 创建工作流实例
        workflow = MedicalWorkflowExample()
        
        # 运行演示
        await workflow.demonstrate_workflows()
        
    except Exception as e:
        logger.error(f"运行出错: {e}")
        print(f"❌ 错误：{e}")
        print("请检查：")
        print("1. OPENAI_API_KEY 是否正确设置")
        print("2. 网络连接是否正常")
        print("3. 依赖库是否正确安装")

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main()) 