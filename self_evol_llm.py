import openai
import os
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Any

def create_llm_client(provider: str, api_key: str, base_url: Optional[str] = None, model: str = "gpt-4o") -> Any:
    """
    根据配置创建LLM客户端
    
    Args:
        provider: LLM提供商 (openai, openrouter等)
        api_key: API密钥
        base_url: API基础URL（可选，某些提供商需要）
        model: 模型名称
    
    Returns:
        OpenAI客户端实例
    """
    provider_lower = provider.lower()
    
    if provider_lower == "openai":
        return openai.OpenAI(api_key=api_key)
    elif provider_lower == "openrouter":
        # OpenRouter使用OpenAI兼容的API
        return openai.OpenAI(
            api_key=api_key,
            base_url=base_url or "https://openrouter.ai/api/v1"
        )
    elif provider_lower == "anthropic":
        # 如果将来需要支持Anthropic，可以在这里添加
        # 注意：Anthropic可能需要不同的客户端库
        raise ValueError("Anthropic暂未支持，请使用openai或openrouter")
    else:
        # 默认使用OpenAI格式，但允许自定义base_url
        if base_url:
            return openai.OpenAI(api_key=api_key, base_url=base_url)
        else:
            # 如果没有指定base_url，尝试使用OpenAI
            return openai.OpenAI(api_key=api_key)

class ManuscriptAgent:
    def __init__(self, client: Any, model: str, debug_log_level: int = 0):
        self.client = client
        self.model = model
        self.memory_file = "memory.md"
        self.prompt_file = "system_prompt.txt"
        self.conversation_history: List[Dict[str, str]] = []
        self.debug_log_level = debug_log_level
        # 文件缓存：存储文件内容和修改时间
        self._prompt_cache: Optional[str] = None
        self._prompt_mtime: float = 0
        self._memory_cache: Optional[str] = None
        self._memory_mtime: float = 0
        self.ensure_files()

    def ensure_files(self):
        """初始化存储文件"""
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, "w", encoding="utf-8") as f:
                f.write("# Agent Experience Memory\n\n")
        if not os.path.exists(self.prompt_file):
            with open(self.prompt_file, "w", encoding="utf-8") as f:
                f.write("You are an expert coder and helpful assistant. Solve problems step by step.")

    def get_current_prompt(self) -> str:
        """获取当前系统提示词（带缓存）"""
        if not os.path.exists(self.prompt_file):
            return "You are an expert coder and helpful assistant. Solve problems step by step."
        
        # 检查文件修改时间
        current_mtime = os.path.getmtime(self.prompt_file)
        if self._prompt_cache is None or current_mtime > self._prompt_mtime:
            # 文件被修改或首次读取，重新读取
            with open(self.prompt_file, "r", encoding="utf-8") as f:
                self._prompt_cache = f.read()
            self._prompt_mtime = current_mtime
        return self._prompt_cache

    def get_memory_context(self) -> str:
        """获取记忆上下文（带缓存）"""
        if not os.path.exists(self.memory_file):
            return ""
        
        # 检查文件修改时间
        current_mtime = os.path.getmtime(self.memory_file)
        if self._memory_cache is None or current_mtime > self._memory_mtime:
            # 文件被修改或首次读取，重新读取
            with open(self.memory_file, "r", encoding="utf-8") as f:
                self._memory_cache = f.read()
            self._memory_mtime = current_mtime
        return self._memory_cache
    
    def _invalidate_memory_cache(self):
        """使记忆缓存失效（在更新记忆后调用）"""
        self._memory_cache = None
        self._memory_mtime = 0
    
    def _invalidate_prompt_cache(self):
        """使提示词缓存失效（在更新提示词后调用）"""
        self._prompt_cache = None
        self._prompt_mtime = 0

    def update_memory(self, issue: str, solution: str, feedback: Optional[str] = None):
        """将经验写入本地 Markdown"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.memory_file, "a", encoding="utf-8") as f:
            f.write(f"### {timestamp}\n")
            f.write(f"- **Issue**: {issue}\n")
            f.write(f"- **Solution**: {solution}\n")
            if feedback:
                f.write(f"- **User Feedback**: {feedback}\n")
            f.write("\n")
        # 清除缓存，下次读取时会重新加载
        self._invalidate_memory_cache()

    def evolve_prompt(self, feedback_report: str):
        """
        核心进化逻辑：根据用户反馈进化 System Prompt
        """
        current_p = self.get_current_prompt()
        memory_context = self.get_memory_context()
        
        evolution_query = f"""
Current System Prompt:
{current_p}

Recent User Feedback:
{feedback_report}

Historical Memory (for context):
{memory_context[:1000]}...

Task: Please rewrite the System Prompt to better address the user's feedback and improve future interactions. 
Integrate the new insights as 'Core Principles'. Return ONLY the new prompt, without any explanation or markdown formatting.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": evolution_query}]
        )
        new_prompt = response.choices[0].message.content.strip()
        
        # 移除可能的markdown代码块标记
        if new_prompt.startswith("```"):
            lines = new_prompt.split("\n")
            new_prompt = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        
        with open(self.prompt_file, "w", encoding="utf-8") as f:
            f.write(new_prompt)
        # 清除缓存，下次读取时会重新加载
        self._invalidate_prompt_cache()
        print("\n>>> [进化完成] System Prompt 已根据反馈更新。\n")

    def chat(self, user_input: str) -> str:
        """执行对话任务"""
        total_start = time.time()
        timings = {}
        
        # 阶段1: 读取提示词和记忆
        stage_start = time.time()
        system_p = self.get_current_prompt()
        memory_context = self.get_memory_context()
        timings["读取文件"] = (time.time() - stage_start) * 1000  # 转换为毫秒
        
        # 阶段2: 构建系统消息
        stage_start = time.time()
        system_message = system_p
        if memory_context:
            system_message += f"\n\n[Historical Experience Memory]\n{memory_context[:2000]}"
        timings["构建系统消息"] = (time.time() - stage_start) * 1000
        
        # 阶段3: 更新对话历史
        stage_start = time.time()
        if not self.conversation_history or self.conversation_history[0]["role"] != "system":
            self.conversation_history = [{"role": "system", "content": system_message}]
        else:
            # 检查记忆是否更新，如果更新了才重新设置系统消息
            # 通过比较当前系统消息是否包含最新的记忆来判断
            current_system_msg = self.conversation_history[0]["content"]
            if current_system_msg != system_message:
                # 记忆或提示词已更新，更新系统消息
                self.conversation_history[0]["content"] = system_message
        
        # 添加用户消息
        self.conversation_history.append({"role": "user", "content": user_input})
        timings["更新对话历史"] = (time.time() - stage_start) * 1000
        
        # 根据调试级别打印调试信息
        if self.debug_log_level > 0:
            print("\n" + "="*60)
            print(f"[调试信息] 最终发送给LLM的完整Prompt (Level {self.debug_log_level}):")
            print("="*60)
            
            if self.debug_log_level >= 1:
                # Level 1: 基本信息 - 检查系统消息是否包含历史记忆
                system_msg = self.conversation_history[0] if self.conversation_history and self.conversation_history[0]["role"] == "system" else None
                if system_msg:
                    if "[Historical Experience Memory]" in system_msg["content"]:
                        print("[确认] 系统消息中已包含历史记忆")
                    else:
                        print("[警告] 系统消息中未找到历史记忆标记")
            
            if self.debug_log_level >= 2:
                # Level 2: 打印完整消息列表（截断长内容）
                for i, msg in enumerate(self.conversation_history, 1):
                    role_name = {"system": "系统", "user": "用户", "assistant": "助手"}.get(msg["role"], msg["role"])
                    content = msg["content"]
                    print(f"\n[{i}] Role: {role_name} ({msg['role']})")
                    print("-"*60)
                    if len(content) > 1000:
                        print(content[:1000] + "...")
                        print(f"... (总长度: {len(content)} 字符)")
                    else:
                        print(content)
            
            if self.debug_log_level >= 3:
                # Level 3: 打印完整消息列表（不截断）
                for i, msg in enumerate(self.conversation_history, 1):
                    role_name = {"system": "系统", "user": "用户", "assistant": "助手"}.get(msg["role"], msg["role"])
                    content = msg["content"]
                    print(f"\n[{i}] Role: {role_name} ({msg['role']})")
                    print("-"*60)
                    print(content)
            
            print("="*60 + "\n")
        
        # 阶段4: 调用LLM API
        stage_start = time.time()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history
        )
        timings["LLM API调用"] = (time.time() - stage_start) * 1000
        
        # 阶段5: 处理响应
        stage_start = time.time()
        assistant_response = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": assistant_response})
        timings["处理响应"] = (time.time() - stage_start) * 1000
        
        # 总耗时
        timings["总耗时"] = (time.time() - total_start) * 1000
        
        # 在 DEBUG_LOG_LEVEL >= 1 时打印耗时信息
        if self.debug_log_level >= 1:
            print("\n" + "="*60)
            print("[性能统计] 各阶段耗时:")
            print("="*60)
            for stage, duration in timings.items():
                if stage == "总耗时":
                    print(f"{stage}: {duration:.2f} ms")
                else:
                    print(f"  - {stage}: {duration:.2f} ms")
            print("="*60 + "\n")
        
        return assistant_response

    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []


class FeedbackAgent:
    """独立的反馈收集Agent"""
    def __init__(self, client: Any, model: str):
        self.client = client
        self.model = model
    
    def collect_feedback(self, task: str, response: str) -> Dict[str, str]:
        """
        收集用户反馈：满意度打分和文字描述
        返回: {"satisfaction": "1-10", "description": "用户文字描述"}
        """
        print("\n" + "="*60)
        print("[反馈收集 Agent]")
        print("="*60)
        print(f"\n任务: {task}")
        print(f"\nAgent 回复:\n{response[:500]}{'...' if len(response) > 500 else ''}\n")
        
        # 收集满意度打分
        while True:
            try:
                satisfaction = input("请为本次回复打分 (1-10，10为最满意): ").strip()
                satisfaction_int = int(satisfaction)
                if 1 <= satisfaction_int <= 10:
                    break
                else:
                    print("请输入1-10之间的数字")
            except ValueError:
                print("请输入有效的数字")
        
        # 收集文字描述
        print("\n请描述您对本次回复的反馈（可以直接回车跳过）:")
        description = input("> ").strip()
        
        return {
            "satisfaction": satisfaction,
            "description": description if description else "无文字反馈"
        }
    
    def generate_feedback_report(self, task: str, response: str, satisfaction: str, description: str) -> str:
        """
        使用LLM生成结构化的反馈报告，用于进化Prompt
        """
        feedback_query = f"""
用户任务: {task}
Agent回复: {response}
用户满意度: {satisfaction}/10
用户文字反馈: {description}

请分析这次交互，指出：
1. Agent回复的优点
2. Agent回复的不足或需要改进的地方
3. 如果满意度低于7分，请分析可能的原因
4. 给出改进建议

请用中文回答，格式清晰。
"""
        
        feedback_analysis = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": feedback_query}]
        )
        
        return feedback_analysis.choices[0].message.content


def load_config(config_file: str = "agent.conf") -> Dict[str, str]:
    """
    从配置文件读取环境变量
    支持格式: KEY="VALUE" 或 KEY='VALUE' 或 KEY=VALUE
    """
    config = {}
    if not os.path.exists(config_file):
        return config
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith("#"):
                    continue
                
                # 匹配 KEY="VALUE" 或 KEY='VALUE' 或 KEY=VALUE
                # 先尝试匹配带引号的格式
                match = re.match(r'^(\w+)\s*=\s*"([^"]*)"$', line)
                if not match:
                    match = re.match(r"^(\w+)\s*=\s*'([^']*)'$", line)
                if not match:
                    # 匹配不带引号的格式
                    match = re.match(r'^(\w+)\s*=\s*(.*)$', line)
                
                if match:
                    key = match.group(1)
                    value = match.group(2).strip()
                    config[key] = value
    except Exception as e:
        print(f"警告: 读取配置文件 {config_file} 时出错: {e}")
    
    return config


def main():
    """主程序入口：交互式命令行对话"""
    # 优先从配置文件读取
    config = load_config("agent.conf")
    
    # 读取LLM提供商配置（默认openai）
    llm_provider = config.get("LLM_PROVIDER", "openai").lower()
    
    # 读取API密钥（支持多种配置方式）
    api_key = config.get("LLM_API_KEY", "")
    if not api_key:
        # 向后兼容：尝试读取OPENAI_API_KEY
        api_key = config.get("OPENAI_API_KEY", "")
    
    # 如果配置文件中没有，尝试从环境变量读取
    if not api_key:
        if llm_provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
        else:
            api_key = os.getenv("OPENAI_API_KEY")
    
    # 如果还是没有，提示用户输入
    if not api_key:
        provider_name = "OpenRouter" if llm_provider == "openrouter" else "OpenAI"
        api_key = input(f"请输入 {provider_name} API Key: ").strip()
        if not api_key:
            print("错误: 需要提供 API Key")
            print(f"提示: 可以在 agent.conf 文件中设置 LLM_API_KEY=\"your_key\"")
            return
    
    # 读取模型配置
    model = config.get("LLM_MODEL", config.get("MODEL", "gpt-4o"))
    
    # 读取API基础URL（可选，某些提供商需要）
    base_url = config.get("LLM_BASE_URL", "")
    if not base_url and llm_provider == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
    
    # 读取调试日志级别配置
    debug_log_level_str = config.get("DEBUG_LOG_LEVEL", "0")
    try:
        debug_log_level = int(debug_log_level_str)
        if debug_log_level < 0 or debug_log_level > 3:
            print(f"警告: DEBUG_LOG_LEVEL 应该在 0-3 之间，当前值 {debug_log_level}，将使用默认值 0")
            debug_log_level = 0
    except ValueError:
        print(f"警告: DEBUG_LOG_LEVEL 配置无效: {debug_log_level_str}，将使用默认值 0")
        debug_log_level = 0
    
    # 创建LLM客户端
    try:
        client = create_llm_client(
            provider=llm_provider,
            api_key=api_key,
            base_url=base_url if base_url else None,
            model=model
        )
        print(f"[配置] LLM提供商: {llm_provider.upper()}, 模型: {model}")
        if base_url:
            print(f"[配置] API地址: {base_url}")
    except Exception as e:
        print(f"错误: 创建LLM客户端失败: {e}")
        return
    
    # 初始化Agent
    agent = ManuscriptAgent(client=client, model=model, debug_log_level=debug_log_level)
    feedback_agent = FeedbackAgent(client=client, model=model)
    
    print("\n" + "="*60)
    print("[自我进化 Agent] - 交互式对话系统")
    print("="*60)
    print("\n输入 'quit' 或 'exit' 退出")
    print("输入 'reset' 重置对话历史")
    print("输入 'feedback' 查看上次对话的反馈")
    print("-"*60 + "\n")
    
    last_task = None
    last_response = None
    
    while True:
        try:
            user_input = input("你: ").strip()
            
            if not user_input:
                continue
            
            # 处理特殊命令
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n再见！")
                break
            elif user_input.lower() == 'reset':
                agent.reset_conversation()
                print("对话历史已重置\n")
                continue
            elif user_input.lower() == 'feedback':
                if last_task and last_response:
                    feedback = feedback_agent.collect_feedback(last_task, last_response)
                    feedback_report = feedback_agent.generate_feedback_report(
                        last_task, last_response, 
                        feedback["satisfaction"], feedback["description"]
                    )
                    print("\n[反馈分析报告]:")
                    print("-"*60)
                    print(feedback_report)
                    print("-"*60)
                    
                    # 如果满意度低，触发进化
                    if int(feedback["satisfaction"]) < 7:
                        print("\n[警告] 满意度较低，触发进化机制...")
                        agent.evolve_prompt(feedback_report)
                        agent.update_memory(
                            last_task, 
                            f"User satisfaction: {feedback['satisfaction']}/10",
                            feedback["description"]
                        )
                else:
                    print("没有可用的对话记录\n")
                continue
            
            # 正常对话
            print("\nAgent: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response + "\n")
            
            # 保存当前对话用于反馈
            last_task = user_input
            last_response = response
            
            # 询问是否需要反馈
            ask_feedback = input("是否需要反馈本次回复？(y/n，默认n): ").strip().lower()
            if ask_feedback == 'y':
                feedback = feedback_agent.collect_feedback(user_input, response)
                feedback_report = feedback_agent.generate_feedback_report(
                    user_input, response,
                    feedback["satisfaction"], feedback["description"]
                )
                
                print("\n[反馈分析报告]:")
                print("-"*60)
                print(feedback_report)
                print("-"*60)
                
                # 记录反馈到记忆
                agent.update_memory(
                    user_input,
                    f"User satisfaction: {feedback['satisfaction']}/10. Response: {response[:200]}...",
                    feedback["description"]
                )
                
                # 如果满意度低，触发进化
                if int(feedback["satisfaction"]) < 7:
                    print("\n[警告] 满意度较低，触发进化机制...")
                    agent.evolve_prompt(feedback_report)
        
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n[错误] {e}\n")


if __name__ == "__main__":
    main()
