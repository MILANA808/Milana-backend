"""AKSI Cognitive Runtime v2 — evidence-driven mathematical arbitration.

Design:
1) route the request;
2) decompose complex work into explicit subgoals;
3) collect independent public evidence when requested;
4) generate multiple candidate answers through the model gateway;
5) score candidates mathematically using query coverage, evidence support,
   source diversity, agreement and contradiction penalties;
6) return an auditable result with epistemic labels.

The language model is a replaceable generator, not the authority.
"""
from __future__ import annotations

import ast
import math
import re
from collections import Counter
from typing import Any, Dict, List
from urllib.parse import urlparse


def terms(text: str) -> List[str]:
    return [
        x for x in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", (text or "").lower())
        if len(x) > 2
    ][:80]


def overlap(a: str, b: str) -> float:
    A, B = set(terms(a)), set(terms(b))
    return len(A & B) / max(1, len(A | B))


def safe_math(text: str):
    s = (text or "").strip().replace(",", ".")
    s = re.sub(r"(?i)(сколько|посчитай|вычисли|равно|чему равно)", "", s).strip()
    if not re.fullmatch(r"[0-9+*/().%\-\s^]+", s) or not re.search(r"[+*/%^]", s):
        return None
    s = s.replace("^", "**")
    if len(s) > 160 or re.search(r"\d{16,}", s):
        return None
    try:
        node = ast.parse(s, mode="eval")
        allowed = (
            ast.Expression, ast.Constant, ast.UnaryOp, ast.BinOp, ast.Add,
            ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub,
            ast.UAdd, ast.FloorDiv,
        )
        if any(type(n) not in allowed for n in ast.walk(node)):
            return None
        if any(
            isinstance(n, ast.Constant)
            and (not isinstance(n.value, (int, float)) or isinstance(n.value, bool))
            for n in ast.walk(node)
        ):
            return None
        value = eval(compile(node, "<aksi-math>", "eval"), {"__builtins__": {}}, {})
        return value if isinstance(value, (int, float)) and math.isfinite(value) else None
    except Exception:
        return None


def route(q: str) -> Dict[str, Any]:
    n = (q or "").lower()
    if safe_math(q) is not None:
        return {"type": "calculation", "needs_web": False, "complexity": 0}
    if re.search(r"\b(сравни|сравнение|план|спроектируй|исследуй|изучи|найди|проверь|стратег|анализ)\b", n):
        return {"type": "research_reasoning", "needs_web": True, "complexity": 2}
    if re.search(r"\b(кто|что|где|когда|почему|как|какой|какая|какие|сколько|зачем|может ли|правда ли)\b", n):
        return {"type": "question", "needs_web": True, "complexity": 1}
    if re.search(r"\b(придумай|напиши|объясни|помоги|идея|создай|спроектируй)\b", n):
        return {"type": "reasoning", "needs_web": False, "complexity": 1}
    return {"type": "general", "needs_web": False, "complexity": 1}


def decompose(q: str, rt: Dict[str, Any]) -> List[Dict[str, Any]]:
    if rt["type"] == "calculation":
        return [{"id": "calc", "goal": q, "kind": "compute"}]
    if rt["type"] == "research_reasoning":
        return [
            {"id": "scope", "goal": f"Определи предмет и критерии для: {q}", "kind": "scope"},
            {"id": "evidence", "goal": f"Найди проверяемые свидетельства по: {q}", "kind": "evidence"},
            {"id": "synthesis", "goal": f"Синтезируй вывод по: {q}", "kind": "synthesis"},
        ]
    if rt["needs_web"]:
        return [{"id": "fact", "goal": q, "kind": "fact"}]
    return [{"id": "answer", "goal": q, "kind": "answer"}]


def source_domains(evidence: List[Dict[str, Any]]) -> set[str]:
    out = set()
    for item in evidence:
        try:
            host = (urlparse(item.get("url", "")).netloc or "").lower()
            if host:
                out.add(host)
        except Exception:
            pass
    return out


def contradiction_pairs(text: str, evidence: List[Dict[str, Any]]) -> List[str]:
    out = []
    neg_words = re.compile(r"\b(не|нет|невозможно|ложн|false|not)\b", re.I)
    target_neg = bool(neg_words.search(text or ""))
    for item in evidence:
        et = item.get("text", "")
        if overlap(text, et) < 0.20:
            continue
        if bool(neg_words.search(et)) != target_neg:
            out.append(item.get("title") or item.get("source") or "evidence")
    return out[:8]


def candidate_score(
    text: str,
    q: str,
    evidence: List[Dict[str, Any]],
    role: str,
    all_candidates: List[str],
) -> Dict[str, float]:
    if not text:
        return {"total": 0.0, "query": 0.0, "evidence": 0.0, "agreement": 0.0, "diversity": 0.0}
    q_score = overlap(text, q)
    ev_scores = [overlap(text, x.get("text", "")) for x in evidence]
    ev_score = max(ev_scores or [0.0])
    agreement = (
        sum(overlap(text, other) for other in all_candidates if other and other != text)
        / max(1, len([other for other in all_candidates if other and other != text]))
    )
    diversity = min(1.0, len(source_domains(evidence)) / 3.0)
    penalty = 0.0
    if re.search(r"точно|гарантированно|безусловно", text, re.I) and not evidence:
        penalty += 0.12
    contradictions = contradiction_pairs(text, evidence)
    penalty += min(0.36, 0.12 * len(contradictions))
    role_bonus = {"direct": 0.05, "analytical": 0.04, "evidence": 0.02}.get(role, 0.0)
    total = max(
        0.0,
        min(
            1.0,
            0.34 * q_score
            + 0.34 * ev_score
            + 0.20 * agreement
            + 0.07 * diversity
            + role_bonus
            - penalty,
        ),
    )
    return {
        "total": round(total, 4),
        "query": round(q_score, 4),
        "evidence": round(ev_score, 4),
        "agreement": round(agreement, 4),
        "diversity": round(diversity, 4),
    }


async def generate_candidates(
    q: str,
    evidence: List[Dict[str, Any]],
    history: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    context = "\n\n".join(
        f"SOURCE: {x.get('source', '')}\nTITLE: {x.get('title', '')}\n"
        f"URL: {x.get('url', '')}\nTEXT: {x.get('text', '')[:4000]}"
        for x in evidence[:10]
    )
    base = (
        "Ты языковой модуль внутри AKSI Cognitive Runtime. "
        "Ответь непосредственно на запрос. Не выдумывай конкретные факты. "
        "Актуальные факты опирай на EVIDENCE. Творческие и планировочные запросы "
        "отвечай полноценно, не заменяй ответ фразой о нехватке свидетельств. "
        "Разделяй факт, вывод и гипотезу. Не раскрывай внутренние рассуждения.\n"
        f"ЗАПРОС:\n{q}\n\nEVIDENCE:\n{context or 'нет внешних свидетельств'}"
    )
    prompts = [
        ("direct", base + "\nРЕЖИМ: direct. Дай ясный итог и краткие основания."),
        ("analytical", base + "\nРЕЖИМ: analytical. Проверь альтернативы, противоречия и ограничения."),
    ]
    candidates = []
    try:
        from app.core.llm import generate
        for role, prompt in prompts:
            chunks = []
            async for chunk in generate(prompt, session_id="cognitive", history=history[-8:]):
                chunks.append(chunk)
            text = "".join(chunks).strip()
            if text:
                candidates.append({"role": role, "text": text})
    except Exception:
        pass
    return candidates


async def run(
    q: str,
    evidence: List[Dict[str, Any]],
    history: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    history = history or []
    rt = route(q)
    plan = decompose(q, rt)
    calc = safe_math(q)

    if calc is not None:
        text = f"Результат: {calc}"
        return {
            "answer": text,
            "route": rt,
            "plan": plan,
            "candidates": [{"role": "calculator", "score": 1.0, "text": text}],
            "selected": "calculator",
            "confidence": 1.0,
            "contradictions": [],
            "epistemic": "fact",
            "evidence_count": len(evidence),
        }

    candidates = await generate_candidates(q, evidence, history)

    if evidence:
        lead = evidence[0]
        candidates.append({
            "role": "evidence",
            "text": lead.get("text", "").strip(),
        })

    if not candidates:
        labels = "факт/вывод/гипотеза"
        text = (
            f"AKSI обработала запрос «{q}», но генератор ответа сейчас недоступен. "
            f"Доступна структурированная постановка задачи: {labels}; "
            "внешний факт без источника не утверждается."
        )
        candidates.append({"role": "local", "text": text})

    texts = [c["text"] for c in candidates]
    for c in candidates:
        metrics = candidate_score(c["text"], q, evidence, c["role"], texts)
        c["score"] = metrics["total"]
        c["score_breakdown"] = metrics
        c["contradictions"] = contradiction_pairs(c["text"], evidence)

    candidates.sort(key=lambda x: x["score"], reverse=True)
    selected = candidates[0]
    confidence = selected["score"]
    if len(candidates) > 1:
        margin = max(0.0, selected["score"] - candidates[1]["score"])
        confidence = min(0.97, confidence + 0.20 * margin)
    if selected["contradictions"]:
        confidence *= 0.72
    if rt["type"] in {"reasoning", "general"} and not evidence:
        confidence = min(confidence, 0.82)

    if evidence:
        epistemic = "fact+inference"
    elif rt["type"] in {"reasoning", "general"}:
        epistemic = "inference/plan"
    else:
        epistemic = "model_answer"

    return {
        "answer": selected["text"],
        "route": rt,
        "plan": plan,
        "candidates": [
            {
                "role": c["role"],
                "score": round(c["score"], 4),
                "score_breakdown": c["score_breakdown"],
                "contradictions": c["contradictions"],
            }
            for c in candidates
        ],
        "selected": selected["role"],
        "confidence": round(max(0.05, min(0.97, confidence)), 3),
        "contradictions": selected["contradictions"],
        "epistemic": epistemic,
        "evidence_count": len(evidence),
        "source_domains": sorted(source_domains(evidence)),
    }
