"""AKSI multi-agent swarm — specialized agents with clear tasks.

Agents run offline-first. No secrets in this module.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.resonance import sign_short

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

WIKI_HEADERS = {"User-Agent": "AKSI-Agent/0.7 (research; contact aksilove@internet.ru)"}


@dataclass
class AgentResult:
    agent: str
    task: str
    answer: str
    ok: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)

    def signed(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "task": self.task,
            "answer": self.answer,
            "ok": self.ok,
            "meta": self.meta,
            "signature": sign_short(f"{self.agent}|{self.answer}")[:24],
            "ts": datetime.utcnow().isoformat() + "Z",
        }


class BaseAgent:
    name = "base"
    role = "generic"

    async def run(self, task: str, context: Optional[str] = None) -> AgentResult:
        raise NotImplementedError


class ResearchAgent(BaseAgent):
    name = "research"
    role = "факты и источники"

    async def run(self, task: str, context: Optional[str] = None) -> AgentResult:
        q = re.sub(
            r"^(что такое|почему|расскажи про|who is|what is)\s+",
            "",
            task,
            flags=re.I,
        ).strip() or task
        if httpx is None:
            return AgentResult(self.name, task, "httpx недоступен", False)
        try:
            async with httpx.AsyncClient(timeout=12.0, headers=WIKI_HEADERS) as client:
                r = await client.get(
                    "https://ru.wikipedia.org/w/api.php",
                    params={
                        "action": "opensearch",
                        "search": q[:80],
                        "limit": 1,
                        "namespace": 0,
                        "format": "json",
                    },
                )
                if r.status_code != 200:
                    return AgentResult(
                        self.name, task, f"Research: Wikipedia HTTP {r.status_code}", False
                    )
                try:
                    data = r.json()
                except Exception:
                    return AgentResult(
                        self.name, task, "Research: некорректный ответ Wikipedia", False
                    )
                title = data[1][0] if data and len(data) > 1 and data[1] else None
                if not title:
                    return AgentResult(
                        self.name, task, f"Research: по «{q[:60]}» статья не найдена.", True
                    )
                s = await client.get(
                    f"https://ru.wikipedia.org/api/rest_v1/page/summary/{title}"
                )
                js = s.json() if s.status_code == 200 else {}
                extract = (js.get("extract") or "")[:700]
                url = (js.get("content_urls") or {}).get("desktop", {}).get("page", "")
                ans = f"{js.get('title', title)}. {extract}"
                if url:
                    ans += f"\nИсточник: {url}"
                return AgentResult(
                    self.name, task, ans, True, {"source": "wikipedia", "title": title}
                )
        except Exception as e:
            return AgentResult(self.name, task, f"Research ошибка: {type(e).__name__}", False)


class AnalystAgent(BaseAgent):
    name = "analyst"
    role = "разбор и план"

    async def run(self, task: str, context: Optional[str] = None) -> AgentResult:
        steps = [
            f"1. Вопрос: {task[:120]}",
            "2. Выделить факты vs оценки",
            "3. Проверить источники (Research)",
            "4. Сформулировать ясный вывод",
            "5. Отметить неуверенность, если данных мало",
        ]
        if context:
            steps.insert(1, f"1b. Контекст: {context[:100]}…")
        ans = "Ход Analyst:\n" + "\n".join(steps)
        return AgentResult(self.name, task, ans, True, {"steps": len(steps)})


class CoderAgent(BaseAgent):
    name = "coder"
    role = "код и архитектура"

    async def run(self, task: str, context: Optional[str] = None) -> AgentResult:
        low = task.lower()
        if any(k in low for k in ("fastapi", "backend", "api")):
            ans = (
                "Coder: FastAPI — роуты в app/api, ядро в app/core, секреты только в .env.\n"
                "Запуск: uvicorn main:app --port 8000\n"
                "Чат: POST /api/chat  ·  агенты: POST /api/agents/run · swarm: POST /api/agents/swarm"
            )
        elif any(k in low for k in ("html", "фронт", "сайт", "css")):
            ans = (
                "Coder: публичное лицо — milana808.github.io/aksi/.\n"
                "Backend URL: localStorage.AKSI_API или ?api=https://…"
            )
        elif any(k in low for k in ("python", "код", "функц", "скрипт")):
            ans = (
                "Coder: чистые функции, без секретов в коде.\n"
                "Пример:\n```python\ndef reply(text: str) -> str:\n    return text.strip() or 'пусто'\n```"
            )
        else:
            ans = (
                "Coder: уточните стек (Python/JS/API). "
                "Общий совет — модули, тесты, .env для ключей."
            )
        return AgentResult(self.name, task, ans, True)


class GuardianAgent(BaseAgent):
    name = "guardian"
    role = "кодекс и безопасность"

    BLOCK = [
        re.compile(r"как\s+(сделать|собрать).{0,40}(бомб|взрывчат|отрав)", re.I),
        re.compile(r"how\s+to\s+(make|build).{0,40}(bomb|explosive)", re.I),
    ]

    async def run(self, task: str, context: Optional[str] = None) -> AgentResult:
        for pat in self.BLOCK:
            if pat.search(task or ""):
                return AgentResult(
                    self.name,
                    task,
                    "Guardian: отказ — запрос нарушает Кодекс (вред людям).",
                    False,
                    {"codex": "block"},
                )
        return AgentResult(
            self.name,
            task,
            "Guardian: ок — можно отвечать. Правила: правда, источники, без вреда.",
            True,
            {"codex": "ok"},
        )


class ResonatorAgent(BaseAgent):
    name = "resonator"
    role = "identity и подпись"

    async def run(self, task: str, context: Optional[str] = None) -> AgentResult:
        from app.core.resonance import identity_block

        idb = identity_block()
        ans = (
            f"Resonator: агент АКСИ.\n"
            f"DID: {idb.get('did')}\n"
            f"Contact: {idb.get('contact')}\n"
            f"Seed: {idb.get('seed')}\n"
            f"Задача принята: {task[:80]}"
        )
        return AgentResult(self.name, task, ans, True, {"did": idb.get("did")})


AGENTS: Dict[str, BaseAgent] = {
    "research": ResearchAgent(),
    "analyst": AnalystAgent(),
    "coder": CoderAgent(),
    "guardian": GuardianAgent(),
    "resonator": ResonatorAgent(),
}


def list_agents() -> List[Dict[str, str]]:
    return [{"name": a.name, "role": a.role} for a in AGENTS.values()]


async def run_agent(name: str, task: str, context: Optional[str] = None) -> Dict[str, Any]:
    agent = AGENTS.get(name)
    if not agent:
        return {"ok": False, "error": f"unknown agent: {name}", "known": list(AGENTS)}
    result = await agent.run(task, context)
    return result.signed()


async def run_swarm(task: str, context: Optional[str] = None) -> Dict[str, Any]:
    order = ["guardian", "resonator", "analyst", "research", "coder"]
    results: List[Dict[str, Any]] = []
    blocked = False
    for name in order:
        r = await run_agent(name, task, context)
        results.append(r)
        if name == "guardian" and r.get("ok") is False:
            blocked = True
            break
    summary_parts = [f"[{x['agent']}] {x['answer'][:220]}" for x in results]
    return {
        "ok": not blocked,
        "task": task,
        "agents_run": [x["agent"] for x in results],
        "results": results,
        "summary": "\n\n".join(summary_parts),
        "signature": sign_short(task + str(len(results)))[:24],
    }
