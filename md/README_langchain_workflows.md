# LangChain 链式工作流样例

这个项目展示了如何使用 LangChain 框架构建不同类型的链式工作流，专门针对医疗领域的应用场景。

## 🎯 项目特色

本样例包含了以下7种不同类型的工作流：

1. **简单链 (Simple Chain)** - 基础的单步骤LLM处理
2. **顺序链 (Sequential Chain)** - 多步骤串行处理流程
3. **分支链 (Router Chain)** - 智能路由分发到不同处理链
4. **记忆链 (Memory Chain)** - 带有对话历史的连续对话
5. **解析器链 (Parser Chain)** - 结构化输出解析
6. **Agent工作流** - 使用工具的智能代理
7. **复合工作流** - 组合多种链的复杂处理流程

## 🚀 快速开始

### 环境准备

1. 安装依赖：
```bash
pip install -r requirements_langchain.txt
```

2. 设置环境变量：
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

或者创建 `.env` 文件：
```
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o  # 可选，默认为gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，默认官方API
```

### 运行演示

```bash
python langchain_workflow_examples.py
```

## 📋 详细功能介绍

### 1. 简单链 (Simple Chain)

**用途**：基础的症状分析
**特点**：
- 单步骤处理
- 简单的输入输出
- 适合基础查询

**示例**：
```python
simple_chain = workflow.create_simple_chain()
result = simple_chain.run({
    "symptoms": "头痛、发热、咳嗽",
    "patient_age": "35",
    "gender": "女"
})
```

### 2. 顺序链 (Sequential Chain)

**用途**：完整的医疗分析流程
**特点**：
- 多步骤串行处理
- 步骤间数据传递
- 结构化的处理流程

**工作流程**：
1. 症状分析 → 疾病方向
2. 检查建议 → 检查项目列表
3. 治疗建议 → 治疗方案

**示例**：
```python
sequential_chain = workflow.create_sequential_chain()
result = sequential_chain.run({
    "symptoms": "胸痛、气短",
    "patient_info": "45岁男性，有高血压史"
})
```

### 3. 分支链 (Router Chain)

**用途**：根据问题类型分发到不同科室
**特点**：
- 智能路由分发
- 专科化处理
- 灵活的扩展性

**支持科室**：
- 内科 (internal_medicine)
- 外科 (surgery)
- 儿科 (pediatrics)
- 全科 (default)

**示例**：
```python
router_chain = workflow.create_router_chain()
result = router_chain.run("3岁儿童反复发热")
```

### 4. 记忆链 (Memory Chain)

**用途**：连续对话，保持上下文
**特点**：
- 对话历史记忆
- 上下文连贯性
- 个性化响应

**记忆类型**：
- `ConversationBufferWindowMemory`：保留最近N轮对话
- `ConversationSummaryMemory`：总结式记忆
- `ConversationBufferMemory`：完整记忆

**示例**：
```python
memory_chain = workflow.create_memory_chain()
result1 = memory_chain.run("我有点头痛")
result2 = memory_chain.run("这种情况持续了三天")
```

### 5. 解析器链 (Parser Chain)

**用途**：结构化输出解析
**特点**：
- 自定义输出格式
- 结构化数据提取
- 便于后续处理

**输出结构**：
```python
{
    "diagnosis": "诊断结果",
    "recommendations": "治疗建议",
    "precautions": "注意事项",
    "full_analysis": "完整分析"
}
```

### 6. Agent工作流

**用途**：使用工具的智能代理
**特点**：
- 工具调用能力
- 推理决策
- 复杂任务处理

**可用工具**：
- `PatientInfoTool`：患者信息查询
- `SymptomAnalysisTool`：症状分析

**示例**：
```python
agent = workflow.create_agent_workflow()
result = agent.run("查询患者001的信息，并分析发热症状")
```

### 7. 复合工作流

**用途**：综合多种链的复杂处理
**特点**：
- 多阶段处理
- 信息预处理
- 结构化报告生成

**处理流程**：
1. 信息预处理 → 提取关键信息
2. 专业分析 → 医疗分析
3. 报告生成 → 结构化医疗报告

## 🛠️ 自定义扩展

### 添加新的科室链

```python
# 新增专科链
nephrology_prompt = PromptTemplate(
    input_variables=["query"],
    template="""
    作为肾内科医生，请回答以下问题：{query}
    
    请从肾内科角度提供专业的分析和建议。
    """
)

nephrology_chain = LLMChain(
    llm=self.llm,
    prompt=nephrology_prompt,
    output_key="result"
)

# 添加到destination_chains
destination_chains["nephrology"] = nephrology_chain
```

### 添加新的工具

```python
class MedicationTool(BaseTool):
    """药物信息查询工具"""
    name = "medication_lookup"
    description = "查询药物信息，输入药物名称"
    
    def _run(self, medication_name: str) -> str:
        # 实现药物查询逻辑
        return f"药物{medication_name}的相关信息"
    
    def _arun(self, medication_name: str) -> str:
        return self._run(medication_name)
```

### 自定义输出解析器

```python
class CustomMedicalParser(BaseOutputParser):
    """自定义医疗解析器"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        # 实现自定义解析逻辑
        return {
            "custom_field": "extracted_value",
            "original_text": text
        }
```

## 🎨 配置选项

### 模型配置

```python
# 使用不同的模型
self.llm = ChatOpenAI(
    model_name="gpt-4o",  # 或 "gpt-3.5-turbo"
    temperature=0.7,      # 控制创造性
    max_tokens=2000,      # 最大输出长度
    request_timeout=60    # 请求超时
)
```

### 记忆配置

```python
# 滑动窗口记忆
memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    input_key="query",
    k=5  # 保留最近5轮对话
)

# 总结式记忆
memory = ConversationSummaryMemory(
    llm=self.llm,
    memory_key="chat_history",
    return_messages=True
)
```

## 📊 性能优化建议

1. **并行处理**：对于独立的处理步骤，考虑使用并行执行
2. **缓存机制**：为重复查询实现缓存
3. **流式输出**：对于长文本生成，使用流式处理
4. **错误处理**：实现完善的错误处理和重试机制

## 🐛 常见问题

### Q: 如何处理API限制？
A: 实现指数退避重试机制，添加请求间隔

### Q: 如何提高响应速度？
A: 使用较小的模型，减少prompt长度，实现缓存

### Q: 如何处理长文本？
A: 使用文本分割，分块处理，或使用更大上下文的模型

### Q: 如何保证输出质量？
A: 优化prompt设计，使用few-shot示例，实现输出验证

## 📝 日志和监控

代码包含详细的日志记录：

```python
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 记录关键操作
logger.info("工作流初始化完成")
logger.debug(f"处理查询: {query}")
```

## 🔐 安全考虑

1. **API密钥管理**：使用环境变量，避免硬编码
2. **输入验证**：验证用户输入，防止注入攻击
3. **数据脱敏**：处理敏感医疗信息时注意脱敏
4. **访问控制**：实现适当的访问控制机制

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

## 📞 联系支持

如有问题或建议，请通过以下方式联系：

- 创建 Issue
- 发送邮件
- 加入讨论群

---

**注意**: 这个样例代码仅用于教学和演示目的，在生产环境中使用时请确保遵循相关的医疗数据安全和隐私法规。 