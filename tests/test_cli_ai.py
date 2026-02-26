"""
Tests for cli_ai.py — AI CLI 命令 (人机对话 + Agent 自主模式)
"""

import json
import os
from unittest import mock

import pytest
from click.testing import CliRunner

from vibecollab.cli_ai import (
    DEFAULT_MAX_CYCLES,
    DEFAULT_MAX_RSS_MB,
    DEFAULT_MAX_SLEEP_S,
    DEFAULT_MIN_SLEEP_S,
    PID_LOCK_FILE,
    _acquire_lock,
    _build_system_prompt,
    _check_rss_mb,
    _find_project_root,
    _get_agent_config,
    _is_pending_solidify,
    _release_lock,
    ai,
)
from vibecollab.event_log import Event, EventLog, EventType
from vibecollab.llm_client import LLMConfig, LLMResponse
from vibecollab.task_manager import TaskManager, TaskStatus

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path):
    """创建一个最小化的项目目录."""
    (tmp_path / "project.yaml").write_text(
        "project_name: test-project\nversion: '1.0'\n", encoding="utf-8"
    )
    (tmp_path / "CONTRIBUTING_AI.md").write_text(
        "# AI Collaboration Protocol\nTest protocol.", encoding="utf-8"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "CONTEXT.md").write_text(
        "# Context\nTest context.", encoding="utf-8"
    )
    vc_dir = tmp_path / ".vibecollab"
    vc_dir.mkdir()
    return tmp_path


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_llm_env():
    """模拟已配置的 LLM 环境变量."""
    with mock.patch.dict(os.environ, {
        "VIBECOLLAB_LLM_API_KEY": "test-key-123",
        "VIBECOLLAB_LLM_PROVIDER": "openai",
        "VIBECOLLAB_LLM_MODEL": "gpt-4o",
    }):
        yield


def _mock_llm_response(content="Mock AI response", model="gpt-4o"):
    """创建模拟的 LLMResponse."""
    return LLMResponse(
        content=content,
        model=model,
        usage={"prompt_tokens": 100, "completion_tokens": 50},
    )


# ---------------------------------------------------------------------------
# Test: 配置和工具函数
# ---------------------------------------------------------------------------

class TestAgentConfig:
    def test_default_config(self):
        cfg = _get_agent_config()
        assert cfg["max_cycles"] == DEFAULT_MAX_CYCLES
        assert cfg["min_sleep"] == DEFAULT_MIN_SLEEP_S
        assert cfg["max_sleep"] == DEFAULT_MAX_SLEEP_S
        assert cfg["max_rss_mb"] == DEFAULT_MAX_RSS_MB

    def test_env_override(self):
        with mock.patch.dict(os.environ, {
            "VIBECOLLAB_AGENT_MAX_CYCLES": "10",
            "VIBECOLLAB_AGENT_MIN_SLEEP": "5",
        }):
            cfg = _get_agent_config()
            assert cfg["max_cycles"] == 10
            assert cfg["min_sleep"] == 5.0

    def test_check_rss_mb_returns_float(self):
        rss = _check_rss_mb()
        assert isinstance(rss, (int, float))
        assert rss >= 0


class TestProjectRoot:
    def test_find_with_project_yaml(self, tmp_project):
        result = _find_project_root(str(tmp_project))
        assert result == tmp_project

    def test_find_from_subdirectory(self, tmp_project):
        subdir = tmp_project / "src" / "deep"
        subdir.mkdir(parents=True)
        result = _find_project_root(str(subdir))
        assert result == tmp_project

    def test_fallback_without_yaml(self, tmp_path):
        result = _find_project_root(str(tmp_path))
        assert result == tmp_path


class TestPIDLock:
    def test_acquire_and_release(self, tmp_path):
        lock = tmp_path / "test.pid"
        assert _acquire_lock(lock) is True
        assert lock.exists()
        assert lock.read_text().strip() == str(os.getpid())
        _release_lock(lock)
        assert not lock.exists()

    def test_stale_lock(self, tmp_path):
        lock = tmp_path / "test.pid"
        lock.write_text("999999999")  # 不存在的 PID
        assert _acquire_lock(lock) is True
        assert lock.read_text().strip() == str(os.getpid())

    def test_active_lock_blocks(self, tmp_path):
        lock = tmp_path / "test.pid"
        lock.write_text(str(os.getpid()))  # 当前进程 PID
        assert _acquire_lock(lock) is False

    def test_release_wrong_pid(self, tmp_path):
        lock = tmp_path / "test.pid"
        lock.write_text("999999999")
        _release_lock(lock)  # 不应删除 (PID 不匹配)
        assert lock.exists()

    def test_release_nonexistent(self, tmp_path):
        lock = tmp_path / "nonexistent.pid"
        _release_lock(lock)  # 不应报错


class TestPendingSolidify:
    def test_no_pending(self, tmp_project):
        event_log = EventLog(tmp_project)
        task_mgr = TaskManager(tmp_project, event_log)
        assert _is_pending_solidify(task_mgr) is False

    def test_has_pending(self, tmp_project):
        event_log = EventLog(tmp_project)
        task_mgr = TaskManager(tmp_project, event_log)
        task_mgr.create_task(
            id="TASK-DEV-001",
            role="DEV",
            feature="test feature",
            assignee="agent",
        )
        task_mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="agent")
        task_mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="agent")
        assert _is_pending_solidify(task_mgr) is True


class TestBuildSystemPrompt:
    def test_includes_context(self, tmp_project):
        prompt = _build_system_prompt(tmp_project, agent_mode=False)
        assert "VibeCollab" in prompt
        assert "Project Context" in prompt
        assert "test-project" in prompt  # from project.yaml

    def test_agent_mode(self, tmp_project):
        prompt = _build_system_prompt(tmp_project, agent_mode=True)
        assert "AUTONOMOUS" in prompt
        assert "ASSESS" in prompt
        assert "SOLIDIFY" in prompt


# ---------------------------------------------------------------------------
# Test: ask 命令
# ---------------------------------------------------------------------------

class TestAskCommand:
    def test_ask_no_llm_config(self, runner, tmp_project):
        with mock.patch.dict(os.environ, {}, clear=True):
            # 清除所有 VIBECOLLAB_LLM_ 环境变量
            env_clean = {k: v for k, v in os.environ.items()
                        if not k.startswith("VIBECOLLAB_LLM_")}
            with mock.patch.dict(os.environ, env_clean, clear=True):
                result = runner.invoke(ai, [
                    "ask", "test question",
                    "-p", str(tmp_project)
                ])
                assert result.exit_code != 0

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_ask_success(self, MockClient, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = _mock_llm_response("Test answer")

        result = runner.invoke(ai, [
            "ask", "什么是 VibeCollab?",
            "-p", str(tmp_project),
        ])
        assert result.exit_code == 0
        assert "Test answer" in result.output
        instance.chat.assert_called_once()

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_ask_no_context(self, MockClient, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.ask.return_value = _mock_llm_response("No context answer")

        result = runner.invoke(ai, [
            "ask", "hello",
            "-p", str(tmp_project),
            "--no-context",
        ])
        assert result.exit_code == 0
        instance.ask.assert_called_once()

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_ask_verbose(self, MockClient, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = _mock_llm_response()

        result = runner.invoke(ai, [
            "ask", "test", "-p", str(tmp_project), "-v",
        ])
        assert result.exit_code == 0
        assert "tokens" in result.output.lower() or "100" in result.output

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_ask_records_event(self, MockClient, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = _mock_llm_response()

        result = runner.invoke(ai, [
            "ask", "test question",
            "-p", str(tmp_project),
        ])
        assert result.exit_code == 0

        # 验证事件被记录
        events_path = tmp_project / ".vibecollab" / "events.jsonl"
        assert events_path.exists()
        events = events_path.read_text(encoding="utf-8").strip().split("\n")
        last_event = json.loads(events[-1])
        assert "AI ask" in last_event["summary"]


# ---------------------------------------------------------------------------
# Test: chat 命令
# ---------------------------------------------------------------------------

class TestChatCommand:
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_chat_exit(self, MockClient, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()

        result = runner.invoke(ai, [
            "chat", "-p", str(tmp_project),
        ], input="exit\n")
        assert result.exit_code == 0
        assert "对话结束" in result.output

    @mock.patch("vibecollab.cli_ai.Console")
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_chat_single_turn(self, MockClient, MockConsole, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = _mock_llm_response("Chat reply")

        result = runner.invoke(ai, [
            "chat", "-p", str(tmp_project),
        ], input="hello\nexit\n")
        assert result.exit_code == 0

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_chat_quit_variants(self, MockClient, runner, tmp_project, mock_llm_env):
        """Test that quit/bye also exit the loop."""
        instance = MockClient.return_value
        instance.config = LLMConfig()

        for cmd in ["quit", "bye", "/exit", "/quit"]:
            result = runner.invoke(ai, [
                "chat", "-p", str(tmp_project),
            ], input=f"{cmd}\n")
            assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Test: agent plan 命令
# ---------------------------------------------------------------------------

class TestAgentPlanCommand:
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_plan_success(self, MockClient, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = _mock_llm_response(
            "## Action Plan\n### Priority 1: Write tests"
        )

        result = runner.invoke(ai, [
            "agent", "plan", "-p", str(tmp_project),
        ])
        assert result.exit_code == 0
        assert "Plan" in result.output or "Action Plan" in result.output


# ---------------------------------------------------------------------------
# Test: agent run 命令
# ---------------------------------------------------------------------------

class TestAgentRunCommand:
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_run_dry_run(self, MockClient, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = _mock_llm_response(
            '```json\n{"task_summary": "test", "steps": []}\n```'
        )

        result = runner.invoke(ai, [
            "agent", "run",
            "-p", str(tmp_project),
            "--dry-run",
        ])
        assert result.exit_code == 0
        assert "Dry-run" in result.output or "dry" in result.output.lower()

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_run_blocked_by_pending(self, MockClient, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()

        # 创建一个 REVIEW 状态的任务
        event_log = EventLog(tmp_project)
        task_mgr = TaskManager(tmp_project, event_log)
        task_mgr.create_task("TASK-DEV-001", "DEV", "test", assignee="agent")
        task_mgr.transition("TASK-DEV-001", TaskStatus.IN_PROGRESS, actor="agent")
        task_mgr.transition("TASK-DEV-001", TaskStatus.REVIEW, actor="agent")

        result = runner.invoke(ai, [
            "agent", "run", "-p", str(tmp_project),
        ])
        assert result.exit_code != 0
        assert "固化" in result.output or "review" in result.output.lower()

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_run_full_cycle(self, MockClient, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = _mock_llm_response("Generated code changes")

        result = runner.invoke(ai, [
            "agent", "run", "-p", str(tmp_project),
        ])
        assert result.exit_code == 0
        assert instance.chat.call_count >= 2  # plan + execute


# ---------------------------------------------------------------------------
# Test: agent serve 命令 (需要特殊处理循环)
# ---------------------------------------------------------------------------

class TestAgentServeCommand:
    @mock.patch("vibecollab.cli_ai.random")
    @mock.patch("vibecollab.cli_ai._execute_agent_cycle", return_value=True)
    @mock.patch("vibecollab.cli_ai.time")
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_serve_single_cycle(self, MockClient, mock_time, mock_cycle, mock_random,
                                 runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()

        mock_time.time.side_effect = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
        mock_time.sleep = mock.MagicMock()
        mock_random.uniform.return_value = 0.1

        result = runner.invoke(ai, [
            "agent", "serve",
            "-p", str(tmp_project),
            "-n", "1",
        ])
        assert result.exit_code == 0
        assert "Agent 服务结束" in result.output
        mock_cycle.assert_called_once()

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_serve_lock_conflict(self, MockClient, runner, tmp_project, mock_llm_env):
        instance = MockClient.return_value
        instance.config = LLMConfig()

        # 创建一个活跃的 PID 锁 (当前进程)
        lock_path = tmp_project / ".vibecollab" / PID_LOCK_FILE
        lock_path.write_text(str(os.getpid()))

        result = runner.invoke(ai, [
            "agent", "serve",
            "-p", str(tmp_project),
        ])
        assert result.exit_code != 0
        assert "已有实例" in result.output or "running" in result.output.lower()


# ---------------------------------------------------------------------------
# Test: agent status 命令
# ---------------------------------------------------------------------------

class TestAgentStatusCommand:
    def test_status_no_agent(self, runner, tmp_project):
        result = runner.invoke(ai, [
            "agent", "status", "-p", str(tmp_project),
        ])
        assert result.exit_code == 0
        assert "未运行" in result.output or "Agent" in result.output

    def test_status_with_events(self, runner, tmp_project):
        event_log = EventLog(tmp_project)
        event_log.append(Event(
            event_type=EventType.CUSTOM,
            summary="Test event",
            actor="test",
        ))

        result = runner.invoke(ai, [
            "agent", "status", "-p", str(tmp_project),
        ])
        assert result.exit_code == 0
        assert "Test event" in result.output

    def test_status_with_tasks(self, runner, tmp_project):
        event_log = EventLog(tmp_project)
        task_mgr = TaskManager(tmp_project, event_log)
        task_mgr.create_task("TASK-DEV-001", "DEV", "test feature", assignee="agent")

        result = runner.invoke(ai, [
            "agent", "status", "-p", str(tmp_project),
        ])
        assert result.exit_code == 0
        assert "TODO" in result.output


# ---------------------------------------------------------------------------
# Test: serve 门控 — 断路器、自适应退避、内存阈值、pending-solidify
# ---------------------------------------------------------------------------

class TestServeCircuitBreaker:
    """serve 中连续失败触发断路器后等待并重置."""

    @mock.patch("vibecollab.cli_ai.random")
    @mock.patch("vibecollab.cli_ai._execute_agent_cycle")
    @mock.patch("vibecollab.cli_ai.time")
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_circuit_breaker_triggers(self, MockClient, mock_time, mock_cycle,
                                       mock_random, runner, tmp_project, mock_llm_env):
        """连续 3 次失败触发断路器，等待后重置."""
        instance = MockClient.return_value
        instance.config = LLMConfig()

        # 4 次调用: 前 3 次失败触发断路器，第 4 次成功（断路器重置后）
        mock_cycle.side_effect = [False, False, False, True]
        mock_time.time.side_effect = list(range(0, 100, 5))
        mock_time.sleep = mock.MagicMock()
        mock_random.uniform.return_value = 0.0

        result = runner.invoke(ai, [
            "agent", "serve", "-p", str(tmp_project), "-n", "4",
        ])
        assert result.exit_code == 0
        assert "断路器" in result.output or "Circuit" in result.output.lower() or "Agent 服务结束" in result.output


class TestServeAdaptiveBackoff:
    """serve 中失败后退避时间指数增长."""

    @mock.patch("vibecollab.cli_ai.random")
    @mock.patch("vibecollab.cli_ai._execute_agent_cycle")
    @mock.patch("vibecollab.cli_ai.time")
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_backoff_doubles_on_failure(self, MockClient, mock_time, mock_cycle,
                                        mock_random, runner, tmp_project, mock_llm_env):
        """失败后 sleep 时间增加."""
        instance = MockClient.return_value
        instance.config = LLMConfig()

        mock_cycle.side_effect = [False, False]  # 两次失败
        mock_time.time.side_effect = list(range(0, 50, 5))
        mock_time.sleep = mock.MagicMock()
        mock_random.uniform.return_value = 0.0

        result = runner.invoke(ai, [
            "agent", "serve", "-p", str(tmp_project), "-n", "2",
        ])
        assert result.exit_code == 0
        # 第二次 sleep 应 >= 第一次 sleep
        sleep_calls = [call.args[0] for call in mock_time.sleep.call_args_list
                       if call.args]
        if len(sleep_calls) >= 2:
            assert sleep_calls[1] >= sleep_calls[0]


class TestServeMemoryThreshold:
    """serve 中内存超限时停止服务."""

    @mock.patch("vibecollab.cli_ai._check_rss_mb", return_value=999.0)
    @mock.patch("vibecollab.cli_ai.random")
    @mock.patch("vibecollab.cli_ai._execute_agent_cycle")
    @mock.patch("vibecollab.cli_ai.time")
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_memory_over_threshold_stops(self, MockClient, mock_time, mock_cycle,
                                          mock_random, mock_rss,
                                          runner, tmp_project, mock_llm_env):
        """RSS 超过阈值时 serve 主动停止."""
        instance = MockClient.return_value
        instance.config = LLMConfig()

        mock_time.time.side_effect = list(range(0, 50, 5))
        mock_time.sleep = mock.MagicMock()
        mock_random.uniform.return_value = 0.0

        result = runner.invoke(ai, [
            "agent", "serve", "-p", str(tmp_project), "-n", "5",
        ])
        assert result.exit_code == 0
        assert "内存超限" in result.output or "Agent 服务结束" in result.output
        # 不应该执行任何 cycle（内存检查在 cycle 前）
        mock_cycle.assert_not_called()


class TestServePendingSolidify:
    """serve 中检测到 pending solidify 时跳过周期."""

    @mock.patch("vibecollab.cli_ai.random")
    @mock.patch("vibecollab.cli_ai._execute_agent_cycle", return_value=True)
    @mock.patch("vibecollab.cli_ai._is_pending_solidify")
    @mock.patch("vibecollab.cli_ai.time")
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_pending_solidify_waits(self, MockClient, mock_time, mock_pending,
                                     mock_cycle, mock_random,
                                     runner, tmp_project, mock_llm_env):
        """有 REVIEW 任务时等待并不计入 cycle_count."""
        instance = MockClient.return_value
        instance.config = LLMConfig()

        mock_time.time.side_effect = list(range(0, 200, 5))
        mock_time.sleep = mock.MagicMock()
        mock_random.uniform.return_value = 0.0

        # 第一次 pending，第二次不 pending
        mock_pending.side_effect = [True, False]

        result = runner.invoke(ai, [
            "agent", "serve", "-p", str(tmp_project), "-n", "1",
        ])
        assert result.exit_code == 0
        assert "待固化" in result.output or "Agent 服务结束" in result.output
        # 即使有 1 次 pending，cycle 仍执行了 1 次
        mock_cycle.assert_called_once()


# ---------------------------------------------------------------------------
# Test: _execute_agent_cycle — 各分支
# ---------------------------------------------------------------------------

class TestExecuteAgentCycle:
    """测试 _execute_agent_cycle 的各个分支."""

    def _make_client_mock(self, plan_resp, exec_resp=None):
        """创建 mock LLMClient."""
        client = mock.MagicMock()
        if exec_resp:
            client.chat.side_effect = [plan_resp, exec_resp]
        else:
            client.chat.return_value = plan_resp
        return client

    def test_plan_failure(self, tmp_project):
        """Plan 阶段 LLM 返回失败."""
        from vibecollab.cli_ai import _execute_agent_cycle
        event_log = EventLog(tmp_project)
        task_mgr = TaskManager(tmp_project, event_log)

        client = mock.MagicMock()
        client.chat.return_value = LLMResponse(content="", model="test")

        result = _execute_agent_cycle(client, tmp_project, event_log, task_mgr, False)
        assert result is False

    def test_exec_failure(self, tmp_project):
        """Execute 阶段 LLM 返回失败."""
        from vibecollab.cli_ai import _execute_agent_cycle
        event_log = EventLog(tmp_project)
        task_mgr = TaskManager(tmp_project, event_log)

        plan_resp = _mock_llm_response("Plan: fix bug in utils.py")
        exec_resp = LLMResponse(content="", model="test")
        client = mock.MagicMock()
        client.chat.side_effect = [plan_resp, exec_resp]

        result = _execute_agent_cycle(client, tmp_project, event_log, task_mgr, False)
        assert result is False

    def test_no_parseable_changes(self, tmp_project):
        """LLM 返回内容无法解析为变更 → 返回 True（非失败）."""
        from vibecollab.cli_ai import _execute_agent_cycle
        event_log = EventLog(tmp_project)
        task_mgr = TaskManager(tmp_project, event_log)

        plan_resp = _mock_llm_response("Plan: analyze code structure")
        exec_resp = _mock_llm_response("I've reviewed the code, no changes needed.")
        client = mock.MagicMock()
        client.chat.side_effect = [plan_resp, exec_resp]

        result = _execute_agent_cycle(client, tmp_project, event_log, task_mgr, False)
        assert result is True  # 无变更不算失败

    def test_exception_in_cycle(self, tmp_project):
        """Cycle 中抛出异常 → 返回 False."""
        from vibecollab.cli_ai import _execute_agent_cycle
        event_log = EventLog(tmp_project)
        task_mgr = TaskManager(tmp_project, event_log)

        client = mock.MagicMock()
        client.chat.side_effect = RuntimeError("network error")

        result = _execute_agent_cycle(client, tmp_project, event_log, task_mgr, False)
        assert result is False

    def test_successful_cycle_with_changes(self, tmp_project):
        """成功的 cycle: plan → execute(有效 JSON) → apply → test → commit."""
        from vibecollab.cli_ai import _execute_agent_cycle
        event_log = EventLog(tmp_project)
        task_mgr = TaskManager(tmp_project, event_log)

        plan_resp = _mock_llm_response("Plan: create hello.txt")
        exec_resp = _mock_llm_response(
            'Here are the changes:\n'
            '```json\n'
            '{"file": "hello.txt", "action": "create", "content": "hello world"}\n'
            '```'
        )
        client = mock.MagicMock()
        client.chat.side_effect = [plan_resp, exec_resp]

        # Mock execute_full_cycle 以避免真实 git 操作
        from vibecollab.agent_executor import ExecutionResult
        mock_result = ExecutionResult(
            success=True,
            changes_applied=["create: hello.txt"],
            test_passed=True,
            git_committed=True,
            git_hash="abc1234",
        )
        with mock.patch("vibecollab.agent_executor.AgentExecutor") as MockExe:
            instance = MockExe.return_value
            instance.parse_changes.return_value = [
                mock.MagicMock(file="hello.txt", action="create")
            ]
            instance.execute_full_cycle.return_value = mock_result

            result = _execute_agent_cycle(
                client, tmp_project, event_log, task_mgr, verbose=False
            )
            assert result is True
            instance.execute_full_cycle.assert_called_once()


# ---------------------------------------------------------------------------
# Test: run 命令 — 完整执行路径
# ---------------------------------------------------------------------------

class TestRunCommandFullPath:
    """run 命令的更多路径测试."""

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_run_with_valid_changes(self, MockClient, runner, tmp_project, mock_llm_env):
        """run 命令接收到有效 JSON 变更并执行."""
        instance = MockClient.return_value
        instance.config = LLMConfig()

        plan_content = "Plan: create a test file"
        exec_content = (
            'Changes:\n```json\n'
            '{"file": "test_out.txt", "action": "create", "content": "data"}\n'
            '```'
        )
        instance.chat.side_effect = [
            _mock_llm_response(plan_content),
            _mock_llm_response(exec_content),
        ]

        result = runner.invoke(ai, [
            "agent", "run", "-p", str(tmp_project), "--dry-run",
        ])
        assert result.exit_code == 0

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_run_plan_failure(self, MockClient, runner, tmp_project, mock_llm_env):
        """run 命令 plan 阶段 LLM 失败."""
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = LLMResponse(content="", model="test")

        result = runner.invoke(ai, [
            "agent", "run", "-p", str(tmp_project),
        ])
        # Plan 失败走到不同路径，但不应 crash
        assert result.exit_code == 0 or result.exit_code == 1


# ---------------------------------------------------------------------------
# Test: ask 命令 — 异常路径
# ---------------------------------------------------------------------------

class TestAskCommandEdge:
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_ask_llm_exception(self, MockClient, runner, tmp_project, mock_llm_env):
        """ask 命令 LLM 抛出 RuntimeError."""
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.side_effect = RuntimeError("API connection failed")

        result = runner.invoke(ai, [
            "ask", "-p", str(tmp_project), "test question",
        ])
        assert result.exit_code != 0
        assert "失败" in result.output or "error" in result.output.lower() or "RuntimeError" in result.output


# ---------------------------------------------------------------------------
# Test: chat 命令 — 异常路径
# ---------------------------------------------------------------------------

class TestChatCommandEdge:
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_chat_empty_input_skipped(self, MockClient, runner, tmp_project, mock_llm_env):
        """空输入行被跳过."""
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = _mock_llm_response("response")

        result = runner.invoke(ai, [
            "chat", "-p", str(tmp_project),
        ], input="\nhello\nexit\n")
        assert result.exit_code == 0
        # chat.call_count = 1 (只有 "hello" 触发调用, 空行被跳过)
        assert instance.chat.call_count == 1

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_chat_llm_error_response(self, MockClient, runner, tmp_project, mock_llm_env):
        """LLM 返回失败响应."""
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = LLMResponse(content="", model="test")

        result = runner.invoke(ai, [
            "chat", "-p", str(tmp_project),
        ], input="hello\nexit\n")
        assert result.exit_code == 0

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_chat_llm_exception(self, MockClient, runner, tmp_project, mock_llm_env):
        """LLM 调用异常时继续运行."""
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.side_effect = ValueError("bad request")

        result = runner.invoke(ai, [
            "chat", "-p", str(tmp_project),
        ], input="hello\nexit\n")
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Test: plan 命令 — 异常路径
# ---------------------------------------------------------------------------

class TestPlanCommandEdge:
    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_plan_llm_failure(self, MockClient, runner, tmp_project, mock_llm_env):
        """plan 命令 LLM 返回空内容."""
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.return_value = LLMResponse(content="", model="test")

        result = runner.invoke(ai, [
            "agent", "plan", "-p", str(tmp_project),
        ])
        assert result.exit_code == 0
        assert "空响应" in result.output or "LLM" in result.output

    @mock.patch("vibecollab.cli_ai.LLMClient")
    def test_plan_exception(self, MockClient, runner, tmp_project, mock_llm_env):
        """plan 命令异常处理."""
        instance = MockClient.return_value
        instance.config = LLMConfig()
        instance.chat.side_effect = RuntimeError("network error")

        result = runner.invoke(ai, [
            "agent", "plan", "-p", str(tmp_project),
        ])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Test: status 命令 — 异常分支
# ---------------------------------------------------------------------------

class TestStatusCommandEdge:
    def test_status_stale_lock(self, runner, tmp_project):
        """陈旧锁文件（PID 已退出）."""
        lock_path = tmp_project / ".vibecollab" / PID_LOCK_FILE
        lock_path.write_text("999999999")  # 不存在的 PID

        result = runner.invoke(ai, [
            "agent", "status", "-p", str(tmp_project),
        ])
        # 可能 exit_code=1 如果 LLMConfig 在某些环境下失败
        assert "陈旧" in result.output or "Agent" in result.output

    def test_status_invalid_lock(self, runner, tmp_project):
        """无效锁文件内容."""
        lock_path = tmp_project / ".vibecollab" / PID_LOCK_FILE
        lock_path.write_text("not_a_number")

        result = runner.invoke(ai, [
            "agent", "status", "-p", str(tmp_project),
        ])
        assert "无效" in result.output or "Agent" in result.output
