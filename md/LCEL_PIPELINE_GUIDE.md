# LangChain Expression Language (LCEL) 管道操作符指南

## 🚀 什么是 LCEL？

LangChain Expression Language (LCEL) 是 LangChain 的现代语法，使用 `|` 管道操作符将不同的组件链接在一起。这种语法更简洁、更直观，也更容易理解和维护。

## 🔄 传统语法 vs LCEL 语法

### 传统语法：
```python
# 传统方式
prompt = PromptTemplate(...)
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run({"input": "症状描述"})
```

### LCEL 语法：
```python
# 现代 LCEL 方式
chain = prompt | llm | StrOutputParser()
result = chain.invoke({"input": "症状描述"})
```

## 📊 LCEL 的主要组件

### 1. 基础组件

| 组件 | 作用 | 示例 |
|------|------|------|
| `PromptTemplate` | 创建提示模板 | `PromptTemplate.from_template("分析症状：{symptoms}")` |
| `ChatOpenAI/OpenAI` | 大语言模型 | `ChatOpenAI(model="gpt-4o")` |
| `StrOutputParser()` | 字符串输出解析器 | 将LLM输出转换为字符串 |
| `RunnablePassthrough` | 数据传递 | 不改变数据，直接传递 |
| `RunnableParallel` | 并行执行 | 同时执行多个操作 |

### 2. 数据操作符

| 操作符 | 作用 | 语法 |
|--------|------|------|
| `\|` | 管道连接 | `a \| b \| c` |
| `{}` | 数据字典 | `{"key": value}` |
| `assign()` | 添加新字段 | `RunnablePassthrough.assign(new_field=...)` |

## 🎯 LCEL 使用模式

### 1. 简单管道
最基础的使用模式：

```python
simple_chain = (
    PromptTemplate.from_template("分析症状：{symptoms}")
    | llm
    | StrOutputParser()
)

result = simple_chain.invoke({"symptoms": "头痛、发热"})
```

**优势**：
- 语法简洁明了
- 易于理解和修改
- 支持流式处理

### 2. 并行处理管道
同时执行多个分析：

```python
parallel_chain = RunnableParallel(
    internal_medicine=(
        PromptTemplate.from_template("内科角度：{symptoms}")
        | llm
        | StrOutputParser()
    ),
    emergency=(
        PromptTemplate.from_template("急诊角度：{symptoms}")
        | llm
        | StrOutputParser()
    )
)

result = parallel_chain.invoke({"symptoms": "胸痛"})
# 输出: {"internal_medicine": "...", "emergency": "..."}
```

**优势**：
- 并行执行，提高效率
- 多角度分析
- 结果结构化

### 3. 复杂数据流管道
多步骤处理，包含数据传递和转换：

```python
complex_chain = (
    {
        "patient_info": extract_prompt | llm | StrOutputParser(),
        "original": RunnablePassthrough()
    }
    | RunnablePassthrough.assign(
        analysis=analysis_prompt | llm | StrOutputParser()
    )
    | final_prompt
    | llm
    | StrOutputParser()
)
```

**数据流：**
1. 第一步：提取患者信息 + 保留原始数据
2. 第二步：基于患者信息进行分析
3. 第三步：生成最终报告

### 4. 条件路由管道
根据条件选择不同的处理路径：

```python
def route_by_severity(inputs):
    symptoms = inputs["symptoms"]
    if "剧烈" in symptoms or "急性" in symptoms:
        return "emergency"
    else:
        return "routine"

# 不同严重程度的处理管道
emergency_chain = emergency_prompt | llm | StrOutputParser()
routine_chain = routine_prompt | llm | StrOutputParser()

# 根据路由结果选择处理链
def process_by_route(inputs):
    route = route_by_severity(inputs)
    if route == "emergency":
        return emergency_chain.invoke(inputs)
    else:
        return routine_chain.invoke(inputs)
```

### 5. 记忆管道
保持对话上下文：

```python
memory_chain = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x.get("history", [])
    }
    | PromptTemplate.from_template(
        "历史: {chat_history}\n问题: {input}\n回答:"
    )
    | llm
    | StrOutputParser()
)
```

## 🛠️ 实际应用示例

### 医疗诊断工作流

```python
# 完整的医疗诊断 LCEL 工作流
medical_diagnosis_chain = (
    # 第一步：信息提取和标准化
    {
        "patient_info": (
            PromptTemplate.from_template(
                "提取患者信息：{raw_input}\n格式：年龄、性别、症状"
            )
            | llm
            | StrOutputParser()
        ),
        "original_input": RunnablePassthrough()
    }
    
    # 第二步：多角度并行分析
    | RunnablePassthrough.assign(
        multi_analysis=RunnableParallel(
            primary_care=(
                PromptTemplate.from_template(
                    "全科医生视角分析：{patient_info}"
                )
                | llm
                | StrOutputParser()
            ),
            specialist=(
                PromptTemplate.from_template(
                    "专科医生视角分析：{patient_info}"
                )
                | llm
                | StrOutputParser()
            ),
            emergency=(
                PromptTemplate.from_template(
                    "急诊科视角评估：{patient_info}"
                )
                | llm
                | StrOutputParser()
            )
        )
    )
    
    # 第三步：综合诊断报告
    | PromptTemplate.from_template(
        """患者信息：{patient_info}
        
        多角度分析：
        - 全科观点：{multi_analysis[primary_care]}
        - 专科观点：{multi_analysis[specialist]}  
        - 急诊观点：{multi_analysis[emergency]}
        
        请生成综合诊断报告："""
    )
    | llm
    | StrOutputParser()
)

# 使用工作流
result = medical_diagnosis_chain.invoke({
    "raw_input": "35岁女性，持续头痛3天，伴有恶心呕吐"
})
```

## 🎨 LCEL 最佳实践

### 1. 可读性优化
```python
# 好的写法：分层清晰
chain = (
    prompt_template
    | llm
    | StrOutputParser()
)

# 更好的写法：添加注释
chain = (
    prompt_template        # 构建提示
    | llm                 # LLM处理
    | StrOutputParser()   # 输出解析
)
```

### 2. 错误处理
```python
from langchain.schema.runnable import RunnableLambda

def safe_parse(text):
    try:
        return json.loads(text)
    except:
        return {"error": "解析失败", "raw": text}

safe_chain = (
    prompt
    | llm
    | RunnableLambda(safe_parse)
)
```

### 3. 流式处理
```python
# 支持流式输出
async def stream_medical_analysis():
    chain = prompt | llm | StrOutputParser()
    
    async for chunk in chain.astream({"symptoms": "头痛"}):
        print(chunk, end="", flush=True)
```

### 4. 批处理
```python
# 批量处理多个患者
patients = [
    {"symptoms": "头痛"},
    {"symptoms": "发热"},
    {"symptoms": "咳嗽"}
]

results = chain.batch(patients)
```

## 🔧 调试和监控

### 1. 启用详细输出
```python
chain = (
    prompt
    | llm.with_config({"verbose": True})
    | StrOutputParser()
)
```

### 2. 添加中间输出
```python
def debug_print(x):
    print(f"Debug: {x}")
    return x

chain = (
    prompt
    | llm
    | RunnableLambda(debug_print)
    | StrOutputParser()
)
```

### 3. 性能监控
```python
import time

def time_component(component_name):
    def wrapper(x):
        start = time.time()
        result = x
        end = time.time()
        print(f"{component_name}: {end - start:.2f}s")
        return result
    return RunnableLambda(wrapper)

chain = (
    prompt
    | time_component("LLM处理")
    | llm
    | time_component("输出解析")
    | StrOutputParser()
)
```

## 📈 性能对比

| 特性 | 传统链式调用 | LCEL 管道 |
|------|-------------|-----------|
| 语法简洁性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 可读性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 流式支持 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 并行处理 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 错误处理 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 调试便利性 | ⭐⭐ | ⭐⭐⭐⭐ |
| 性能 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🚀 迁移指南

### 从传统语法迁移到 LCEL

#### 1. 简单链迁移
**之前：**
```python
prompt = PromptTemplate(...)
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(inputs)
```

**之后：**
```python
chain = prompt | llm | StrOutputParser()
result = chain.invoke(inputs)
```

#### 2. 顺序链迁移
**之前：**
```python
chain1 = LLMChain(...)
chain2 = LLMChain(...)
sequential = SequentialChain(chains=[chain1, chain2])
```

**之后：**
```python
chain = (
    prompt1 | llm | StrOutputParser()
    | RunnablePassthrough.assign(
        step2=prompt2 | llm | StrOutputParser()
    )
)
```

#### 3. 路由链迁移
**之前：**
```python
router_chain = MultiRouteChain(
    router_chain=router,
    destination_chains=destinations
)
```

**之后：**
```python
def route_and_process(inputs):
    route = router_function(inputs)
    return destination_pipelines[route].invoke(inputs)

chain = RunnableLambda(route_and_process)
```

## 💡 常见问题

### Q: 什么时候使用 LCEL？
A: 
- 新项目建议直接使用 LCEL
- 需要流式处理时
- 要进行并行处理时
- 希望代码更简洁时

### Q: LCEL 兼容性如何？
A: LCEL 是 LangChain 0.1+ 的标准语法，向后兼容传统语法

### Q: 如何处理复杂的条件逻辑？
A: 使用 `RunnableLambda` 包装自定义函数，或组合多个条件管道

### Q: LCEL 支持异步吗？
A: 完全支持，使用 `astream()`, `ainvoke()`, `abatch()` 等异步方法

## 🎯 总结

LCEL 管道操作符提供了：

1. **简洁的语法** - 使用 `|` 连接组件
2. **强大的并行处理** - `RunnableParallel` 支持
3. **灵活的数据流** - `RunnablePassthrough` 和 `assign()`
4. **优秀的流式支持** - 原生支持流式输出
5. **易于调试** - 清晰的数据流向
6. **高性能** - 自动优化执行

这使得 LangChain 工作流的构建变得更加现代化和高效！ 