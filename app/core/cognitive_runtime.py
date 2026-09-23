"""AKSI Cognitive Runtime v1 — mathematical arbitration around optional language models.

The runtime does not claim to replace a neural language model. It provides the
controller: routing, candidate generation, evidence scoring, contradiction
checks, confidence calibration, and a durable structured result.
"""
from __future__ import annotations
import ast, math, re
from typing import Any, Dict, List

def terms(text: str) -> List[str]:
    return [x for x in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", (text or "").lower()) if len(x) > 2][:40]

def overlap(a: str, b: str) -> float:
    A=set(terms(a)); B=set(terms(b))
    return len(A&B)/max(1, len(A|B))

def safe_math(text: str):
    s=(text or "").strip().replace(",", ".")
    s=re.sub(r"(?i)(сколько|посчитай|вычисли|равно|чему равно)","",s).strip()
    if not re.fullmatch(r"[0-9+*/().%\-\s^]+", s) or not re.search(r"[+*/%^]",s):
        return None
    s=s.replace("^","**")
    try:
        node=ast.parse(s, mode="eval")
        allowed=(ast.Expression,ast.Constant,ast.UnaryOp,ast.BinOp,ast.Add,ast.Sub,ast.Mult,ast.Div,
                 ast.Pow,ast.Mod,ast.USub,ast.UAdd,ast.FloorDiv)
        if any(type(n) not in allowed for n in ast.walk(node)): return None
        if any(isinstance(n,ast.Constant) and (not isinstance(n.value,(int,float)) or isinstance(n.value,bool)) for n in ast.walk(node)): return None
        v=eval(compile(node,"<aksi-math>","eval"),{"__builtins__":{}},{})
        return v if isinstance(v,(int,float)) and math.isfinite(v) else None
    except Exception:
        return None

def route(q: str) -> Dict[str,Any]:
    n=(q or "").lower()
    if safe_math(q) is not None: return {"type":"calculation","needs_web":False}
    if re.search(r"\b(кто|что|где|когда|почему|как|какой|какая|какие|сколько|зачем|может ли|правда ли)\b",n):
        return {"type":"question","needs_web":True}
    if re.search(r"\b(сравни|план|придумай|спроектируй|напиши|объясни|помоги|идея|стратег)",n):
        return {"type":"reasoning","needs_web":False}
    return {"type":"general","needs_web":False}

def score_candidate(text: str, q: str, evidence: List[Dict[str,Any]], role: str) -> float:
    if not text: return 0.0
    ev=max([overlap(text, x.get("text","")) for x in evidence] or [0.0])
    qov=overlap(text,q)
    penalties=0.0
    if re.search(r"https?://|источник:", text, re.I) and not evidence: penalties += .15
    if re.search(r"точно|гарантированно|безусловно",text,re.I) and not evidence: penalties += .12
    role_bonus=.05 if role=="direct" else .03
    return max(0.0,min(1.0,.48*qov+.47*ev+role_bonus-penalties))

def contradictions(text: str, evidence: List[Dict[str,Any]]) -> List[str]:
    out=[]
    neg=re.search(r"\bне\b|невозмож|ложн",text.lower()) is not None
    for e in evidence:
        et=e.get("text","")
        en=re.search(r"\bне\b|невозмож|ложн",et.lower()) is not None
        if neg != en and overlap(text,et)>.28:
            out.append(e.get("title") or e.get("source") or "evidence")
    return out[:5]

async def run(q: str, evidence: List[Dict[str,Any]], history: List[Dict[str,Any]]|None=None) -> Dict[str,Any]:
    history=history or []
    rt=route(q)
    calc=safe_math(q)
    if calc is not None:
        return {"answer":f"Результат: {calc}","route":rt,"candidates":[{"role":"calculator","score":1.0,"text":f"Результат: {calc}"}],"selected":"calculator","confidence":1.0,"contradictions":[]}
    context="\n\n".join(
        f"SOURCE: {x.get('source','')}\nTITLE: {x.get('title','')}\nURL: {x.get('url','')}\nTEXT: {x.get('text','')[:3500]}"
        for x in evidence[:8]
    )
    base=(
        "Ты языковой модуль внутри AKSI Cognitive Runtime. "
        "Ответь непосредственно на запрос. Не выдумывай конкретные факты. "
        "Если вопрос требует актуальных данных, используй только данные из EVIDENCE и отделяй факт от вывода. "
        "Если запрос творческий, гипотетический, планировочный или объяснительный — отвечай полноценно, не заменяй ответ фразой о нехватке свидетельств. "
        "Не раскрывай внутренние рассуждения; дай только краткие основания и итог. "
        "Запрос:\n"+q+"\n\nEVIDENCE:\n"+(context or "нет внешних свидетельств")
    )
    candidates=[]
    try:
        from app.core.llm import generate
        prompts=[
            base+"\nРЕЖИМ: direct. Сначала дай ясный ответ, затем 2-4 кратких основания.",
            base+"\nРЕЖИМ: analytical. Построй независимое объяснение, явно разделив факт, вывод и предположение."
        ]
        for i,p in enumerate(prompts):
            out=[]
            async for chunk in generate(p,session_id="cognitive",history=history[-8:]):
                out.append(chunk)
            txt="".join(out).strip()
            if txt:
                role="direct" if i==0 else "analytical"
                candidates.append({"role":role,"text":txt,"score":score_candidate(txt,q,evidence,role)})
    except Exception:
        pass
    if evidence:
        lead=evidence[0]
        candidates.append({"role":"evidence","text":lead.get("text","").strip(),"score":score_candidate(lead.get("text",""),q,evidence,"evidence")})
    if not candidates:
        ts=terms(q)
        local=(f"Рабочая модель AKSI для запроса «{q}»: ключевые понятия — {', '.join(ts) if ts else 'не выделены'}. "
               "Это структурированная гипотеза, а не установленный внешний факт.")
        candidates.append({"role":"local","text":local,"score":.18})
    for c in candidates:
        c["contradictions"]=contradictions(c["text"],evidence)
        c["score"]=max(0,c["score"]-.12*len(c["contradictions"]))
    candidates.sort(key=lambda x:x["score"],reverse=True)
    selected=candidates[0]
    conf=min(.97,max(.05,selected["score"]*(1.0 if not selected["contradictions"] else .72)))
    return {
        "answer":selected["text"],
        "route":rt,
        "candidates":[{k:c[k] for k in ("role","score","contradictions")} for c in candidates],
        "selected":selected["role"],
        "confidence":round(conf,3),
        "contradictions":selected["contradictions"],
        "evidence_count":len(evidence)
    }
