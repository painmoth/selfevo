"""
简单的单用户会话存储（落盘到 JSON）。

数据结构：
{
  "sessions": {
     "<session_id>": {
        "id": "...",
        "title": "...",
        "created_at": 1700000000.0,
        "updated_at": 1700000000.0,
        "messages": [
           {"role":"user"|"assistant", "content":"...", "ts": 1700000000.0}
        ]
     }
  }
}
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


def _now() -> float:
    return time.time()


@dataclass
class StoredMessage:
    role: str
    content: str
    ts: float


class SessionStore:
    def __init__(self, store_path: str):
        self.store_path = store_path
        self._ensure_parent_dir()
        self._data: Dict[str, Any] = {"sessions": {}}
        self._load()

    def _ensure_parent_dir(self):
        parent = os.path.dirname(os.path.abspath(self.store_path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

    def _load(self):
        if not os.path.exists(self.store_path):
            self._persist()
            return
        try:
            with open(self.store_path, "r", encoding="utf-8") as f:
                self._data = json.load(f) or {"sessions": {}}
            if "sessions" not in self._data:
                self._data["sessions"] = {}
        except Exception:
            # 如果文件损坏，保留一个备份并重置
            try:
                bad_path = self.store_path + ".bad"
                os.replace(self.store_path, bad_path)
            except Exception:
                pass
            self._data = {"sessions": {}}
            self._persist()

    def _persist(self):
        tmp_path = self.store_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.store_path)

    def create_session(self, session_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        now = _now()
        title = title or "新对话"
        self._data["sessions"][session_id] = {
            "id": session_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "messages": [],
        }
        self._persist()
        return self._data["sessions"][session_id]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get("sessions", {}).get(session_id)

    def upsert_session(self, session_id: str) -> Dict[str, Any]:
        s = self.get_session(session_id)
        if s is None:
            return self.create_session(session_id=session_id)
        return s

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._data.get("sessions", {}):
            del self._data["sessions"][session_id]
            self._persist()
            return True
        return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        sessions = list(self._data.get("sessions", {}).values())
        sessions.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        # 不返回 messages（减小体积）
        return [
            {
                "id": s["id"],
                "title": s.get("title", "新对话"),
                "created_at": s.get("created_at", 0),
                "updated_at": s.get("updated_at", 0),
                "message_count": len(s.get("messages", [])),
            }
            for s in sessions
        ]

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        s = self.get_session(session_id)
        if not s:
            return []
        return s.get("messages", [])

    def append_message(self, session_id: str, role: str, content: str) -> None:
        s = self.upsert_session(session_id)
        now = _now()
        s.setdefault("messages", []).append({"role": role, "content": content, "ts": now})
        s["updated_at"] = now
        # 自动用第一条 user 消息作为标题
        if (s.get("title") in (None, "", "新对话")) and role == "user":
            s["title"] = content.strip()[:20] or "新对话"
        self._persist()

    def reset_messages(self, session_id: str) -> bool:
        s = self.get_session(session_id)
        if not s:
            return False
        s["messages"] = []
        s["updated_at"] = _now()
        s["title"] = "新对话"
        self._persist()
        return True

    def rename_session(self, session_id: str, title: str) -> bool:
        s = self.get_session(session_id)
        if not s:
            return False
        title = (title or "").strip()
        if not title:
            return False
        s["title"] = title[:60]
        s["updated_at"] = _now()
        self._persist()
        return True
