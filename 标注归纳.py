# 标注归并LLM Prompts

## 1. 分批处理主Prompt

你是一个专业的数据标注归并专家。我需要你帮我将相似的场景标注进行归并统一。

### 背景信息
- 这是第 {batch_num}/{total_batches} 批数据
- 数据来源：用户行为场景标注
- 目标：将语义相似的标注归并为统一的标准标注

### 已有标准标注（请优先使用）
{existing_standard_labels}

### 本批次待处理标注
{current_batch_labels}

### 归并规则
1. **优先复用**：如果新标注与已有标准标注语义相同，必须映射到已有标准标注
2. **语义判断**：基于场景的本质含义进行归并，而不是字面相似度
3. **保持简洁**：标准标注应该简洁明确，易于理解
4. **避免重复**：不要创建与已有标准标注语义重复的新标注

### 输出格式
请严格按照以下JSON格式输出：json
{
  "mappings": [
    {"original": "机场候机", "standard": "机场等待"},
    {"original": "在机场等飞机", "standard": "机场等待"},
    {"original": "购物中心逛街", "standard": "购物"}
  ],
  "new_standards": ["机场等待", "购物"],
  "reasoning": "简要说明归并逻辑"
}

### 场景示例
- "开车上班" 和 "驾车通勤" → 统一为 "开车通勤"
- "在家看电视" 和 "家里看剧" → 统一为 "在家娱乐"
- "超市买菜" 和 "菜市场购物" → 统一为 "购买食材"

请开始处理：

## 2. 全局统一Prompt

你需要对不同批次产生的标准标注进行最终统一，解决批次间的不一致问题。

### 任务说明
在分批处理过程中，不同批次可能对相同场景产生了不同的标准标注，需要你进行最终统一。

### 所有标准标注列表
{all_standard_labels}

### 统一原则
1. **语义优先**：语义相同的必须统一
2. **频次参考**：优先选择使用频次更高的标注作为最终标准
3. **表达清晰**：选择最清晰易懂的表达方式
4. **覆盖全面**：确保涵盖所有场景类型

### 输出格式json
{
  "unified_mappings": [
    {"from": "机场候机", "to": "机场等待"},
    {"from": "机场等飞机", "to": "机场等待"},
    {"from": "航站楼等待", "to": "机场等待"}
  ],
  "final_standards": ["机场等待", "购物", "在家娱乐", "开车通勤"],
  "merged_groups": [
    {
      "final_standard": "机场等待",
      "merged_from": ["机场候机", "机场等飞机", "航站楼等待"],
      "reason": "都是在机场等待的场景"
    }
  ]
}

请开始统一：

## 3. 质量检查Prompt

请对标注归并结果进行质量检查，识别可能的问题。

### 检查数据
归并映射表：
{mapping_table}

最终标准标注：
{final_standards}

### 检查维度
1. **语义一致性**：映射是否合理，有无语义跨度过大的归并
2. **标准完整性**：标准标注是否涵盖了所有主要场景类型
3. **表达规范性**：标准标注的表达是否规范统一
4. **潜在冲突**：是否存在一个原标注可能映射到多个标准标注的情况

### 输出格式json
{
  "quality_score": 85,
  "issues": [
    {
      "type": "semantic_mismatch",
      "description": "'睡觉休息' 被归并到 '在家娱乐'，语义不匹配",
      "suggestion": "建议创建 '休息睡眠' 标准标注"
    }
  ],
  "recommendations": [
    "建议将 '工作会议' 和 '开会讨论' 进一步细分",
    "考虑增加 '运动健身' 大类标注"
  ],
  "statistics": {
    "total_mappings": 1247,
    "final_standards": 156,
    "reduction_rate": "87.5%"
  }
}

## 4. 增量学习Prompt

基于之前批次的处理经验，为新标注预测最可能的标准标注。

### 历史学习数据
已处理的标注映射：
{historical_mappings}

高频标准标注：
{frequent_standards}

### 待预测标注
{new_labels}

### 预测规则
1. **模式识别**：基于历史数据识别标注模式
2. **语义相似**：寻找语义最相似的已有映射
3. **置信度评估**：给出预测的置信度
4. **兜底处理**：低置信度的标注标记为需要人工处理

### 输出格式json
{
  "predictions": [
    {
      "original": "商场购物中心",
      "predicted_standard": "购物",
      "confidence": 0.95,
      "reasoning": "与已有 '购物中心' 语义相同"
    },
    {
      "original": "公园散步锻炼",
      "predicted_standard": "户外运动",
      "confidence": 0.75,
      "reasoning": "与 '公园跑步' 场景相似"
    }
  ],
  "need_manual_review": ["特殊场景标注1", "歧义标注2"],
  "new_patterns": ["发现新的居家办公相关标注模式"]
}

## 5. 调试分析Prompt

请分析标注归并过程中的异常情况，帮助优化处理流程。

### 异常数据
{anomaly_data}

### 分析维度
1. **标注质量**：原始标注的质量问题
2. **归并逻辑**：归并过程中的逻辑问题
3. **边界案例**：难以分类的边界情况
4. **系统性问题**：可能影响整体质量的系统性问题

### 输出要求
- 识别问题类型和原因
- 提供具体的优化建议
- 给出处理这类问题的通用策略

#json
{
  "problem_analysis": [
    {
      "problem_type": "ambiguous_labels",
      "examples": ["在路上", "外出中"],
      "root_cause": "原始标注过于模糊",
      "impact": "难以准确归并",
      "solution": "建议要求更具体的场景描述"
    }
  ],
  "optimization_suggestions": [
    "增加上下文信息辅助判断",
    "建立标注规范指南",
    "设置置信度阈值过滤"
  ]
}

## 6. 使用示例

### Python调用示例

def create_batch_prompt(batch_num, total_batches, existing_standards, current_labels):
    """生成批次处理prompt"""
    
    # 格式化已有标准标注
    if existing_standards:
        standards_text = "\n".join([f"- {label}" for label in existing_standards[:50]])
        if len(existing_standards) > 50:
            standards_text += f"\n... 等共{len(existing_standards)}个标准标注"
    else:
        standards_text = "暂无（这是第一批）"
    
    # 格式化当前批次标注
    labels_text = "\n".join([f"- {label}" for label in current_labels])
    
    prompt = f"""你是一个专业的数据标注归并专家。我需要你帮我将相似的场景标注进行归并统一。

### 背景信息
- 这是第 {batch_num}/{total_batches} 批数据
- 数据来源：用户行为场景标注
- 目标：将语义相似的标注归并为统一的标准标注

### 已有标准标注（请优先使用）
{standards_text}

### 本批次待处理标注
{labels_text}

### 归并规则
1. **优先复用**：如果新标注与已有标准标注语义相同，必须映射到已有标准标注
2. **语义判断**：基于场景的本质含义进行归并，而不是字面相似度
3. **保持简洁**：标准标注应该简洁明确，易于理解
4. **避免重复**：不要创建与已有标准标注语义重复的新标注

### 输出格式
请严格按照以下JSON格式输出：
```json
{{
  "mappings": [
    {{"original": "原标注", "standard": "标准标注"}}
  ],
  "new_standards": ["新增的标准标注"],
  "reasoning": "简要说明归并逻辑"
}}
```

请开始处理："""
    
    return prompt

# 使用示例
prompt = create_batch_prompt(
    batch_num=3,
    total_batches=25,
    existing_standards=["机场等待", "购物", "在家娱乐"],
    current_labels=["机场候机", "商场逛街", "家里看电视"]
)