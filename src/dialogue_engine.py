# src/dialogue_engine.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import random
from core.config import FOLLOW_THRESHOLD  

# ---------------- Game variables ----------------
@dataclass
class GameVars:
    trust: int = 50 
    police_gap: int = 0      # + = Tony further ahead, - = police closer
    flags: Dict[str, Any] = field(default_factory=dict)

    def apply_effects(self, effects: Dict[str, int]):
        if "trust" in effects:
            self.trust = max(0, min(100, self.trust + int(effects["trust"])))
        if "police_gap" in effects:
            self.police_gap += int(effects["police_gap"])

# ---------------- Runner ----------------
class DialogueRunner:
    """
    Supported node types:
      - line: {type,speaker,text,next}
      - choice: {type,prompt,options:[{id,label,lines?,correct?}],choice_speaker?,next}
      - branch_choice_correct: {type, if_correct, if_wrong}
      - decision_follow: {type, if_follow_and_correct, if_follow_and_wrong, if_ignore_and_correct, if_ignore_and_wrong}
      - effects: {type,effects,next}
      - goto: {type,next}
      - wait_scene: {type,event,next}
      - end
    """

    def __init__(self, scene: Dict[str, Any], gvars: GameVars, rng_seed: Optional[int] = None):
        self.scene = scene
        self.nodes: Dict[str, Dict[str, Any]] = scene["nodes"]
        self.current_id: str = scene["start"]
        self.gvars = gvars
        self.selected: Optional[Dict[str, Any]] = None  # last choice option dict
        self._buffer: List[Tuple[str, str]] = []        # (speaker, text)
        self._pending_choice: Optional[Dict[str, Any]] = None
        self.finished = False
        self.random = random.Random(rng_seed)

        # wait_scene state
        self._waiting_event: Optional[str] = None
        self._waiting_next: Optional[str] = None

        self._advance_until_prompt()

    # ---------- Public API ----------
    def is_waiting_for_choice(self) -> bool:
        return self._pending_choice is not None

    def is_finished(self) -> bool:
        return self.finished

    def is_waiting_for_event(self) -> bool:
        return self._waiting_event is not None

    def waiting_event_name(self) -> Optional[str]:
        return self._waiting_event

    def notify_event_done(self, event_name: str):
        if self._waiting_event == event_name:
            self._waiting_event = None
            if self._waiting_next:
                self.current_id = self._waiting_next
                self._waiting_next = None
            self._advance_until_prompt()

    def get_prompt(self) -> Optional[Dict[str, Any]]:
        """Returns current prompt or None (including while waiting for a scene event)."""
        if self.finished:
            return None
        if self._buffer:
            speaker, text = self._buffer[0]
            return {"type": "lines", "speaker": speaker, "text": text}
        if self._pending_choice:
            return {
                "type": "choice",
                "prompt": self._pending_choice.get("prompt", ""),
                "options": [opt.get("label", opt.get("text", "")) for opt in self._pending_choice["options"]],
            }
        self._advance_until_prompt()
        if self._buffer:
            speaker, text = self._buffer[0]
            return {"type": "lines", "speaker": speaker, "text": text}
        if self._pending_choice:
            return {
                "type": "choice",
                "prompt": self._pending_choice.get("prompt", ""),
                "options": [opt.get("label", opt.get("text", "")) for opt in self._pending_choice["options"]],
            }
        return None

    def submit_continue(self):
        if self._buffer:
            self._buffer.pop(0)
            if not self._buffer:
                self._advance_until_prompt()

    def submit_choice(self, index: int):
        """User confirmed a choice (called by the UI). Only here we enqueue option 'lines'."""
        if not self._pending_choice:
            return
        node = self._pending_choice
        options = node["options"]
        index = max(0, min(index, len(options) - 1))
        self.selected = options[index]

        post_lines = self.selected.get("lines")
        if post_lines:
            speaker = node.get("choice_speaker", "Acolyte")
            if isinstance(post_lines, str):
                self._buffer.append((speaker, post_lines))
            else:
                for line in post_lines:
                    self._buffer.append((speaker, line))

        next_id = node.get("next")
        self._pending_choice = None
        if next_id:
            self.current_id = next_id
        self._advance_until_prompt()

    # ---------- Internals ----------
    def _push_lines(self, speaker: str, text: Any):
        if isinstance(text, str):
            self._buffer.append((speaker, text))
        else:
            for t in text:
                self._buffer.append((speaker, t))

    def _advance_until_prompt(self):
        while not self.finished and not self._buffer and not self._pending_choice and not self._waiting_event:
            node = self.nodes[self.current_id]
            ntype = node["type"]

            if ntype == "line":
                self._push_lines(node.get("speaker",""), node["text"])
                self.current_id = node.get("next", self.current_id)

            elif ntype == "choice":
                self._pending_choice = node
                break

            elif ntype == "branch_choice_correct":
                is_correct = bool(self.selected and self.selected.get("correct", False))
                self.current_id = node["if_correct"] if is_correct else node["if_wrong"]

            elif ntype == "decision_follow":
                advice_ok = bool(self.selected and self.selected.get("correct", False))
                follows = self._tony_follows(self.gvars.trust)
                if follows and advice_ok:
                    self.current_id = node["if_follow_and_correct"]
                elif follows and not advice_ok:
                    self.current_id = node["if_follow_and_wrong"]
                elif (not follows) and advice_ok:
                    self.current_id = node["if_ignore_and_correct"]
                else:
                    self.current_id = node["if_ignore_and_wrong"]

            elif ntype == "effects":
                self.gvars.apply_effects(node.get("effects", {}))
                self.current_id = node.get("next", self.current_id)

            elif ntype == "goto":
                self.current_id = node["next"]

            elif ntype == "wait_scene":
                self._waiting_event = node["event"]
                self._waiting_next = node["next"]
                break

            elif ntype == "end":
                self.finished = True
                break

            elif ntype == "branch_condition":
             # Évaluer les branches selon les conditions
                selected = None
                for branch in node.get("branches", []):
                   cond = branch.get("cond")
                   next_id = branch.get("next")

                   if cond == "police" and self.gvars.police_gap < 0:
                      selected = next_id
                      break
                   elif cond == "escape" and self.gvars.trust >= 40 and self.gvars.police_gap >= 0:
                     selected = next_id
                     break

                if selected is None:
                 # fallback : première branche si aucune condition n'est vraie
                    selected = node["branches"][0]["next"]

                self.current_id = selected
                continue

    def _tony_follows(self, trust: int) -> bool:
        # Deterministic threshold
        return trust >= FOLLOW_THRESHOLD
    
