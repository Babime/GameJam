from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import random, math
from core.config import (
    FOLLOW_THRESHOLD,
    FOLLOW_SIGMOID_K, FOLLOW_PROB_FLOOR, FOLLOW_PROB_CEIL
)

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
      - branch_choice_3way: {type, if_correct, if_wrong, if_neutral}
      - decision_follow: {type, if_follow_and_correct, if_follow_and_wrong}
      - decision_follow_3way: {type, if_follow_and_correct, if_follow_and_wrong, if_ignore_and_correct, if_ignore_and_wrong}
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

            elif ntype == "branch_choice_3way":
                # self.selected["correct"] peut être True / False / "neutral"
                tag = (self.selected or {}).get("correct", False)
                if tag is True:
                    self.current_id = node["if_correct"]
                elif tag == "neutral":
                    self.current_id = node["if_neutral"]
                else:
                    self.current_id = node["if_wrong"]

            elif ntype == "decision_follow_3way":
                # follow/ignore selon la confiance, puis branche 3 voies
                tag = (self.selected or {}).get("correct", False)  # True / False / "neutral"
                follows = self._tony_follows(self.gvars.trust)

                if follows:
                    if tag is True:
                        self.current_id = node["if_follow_correct"]
                    elif tag == "neutral":
                        self.current_id = node["if_follow_neutral"]
                    else:
                        self.current_id = node["if_follow_wrong"]
                else:
                    if tag is True:
                        self.current_id = node["if_ignore_correct"]
                    elif tag == "neutral":
                        self.current_id = node["if_ignore_neutral"]
                    else:
                        self.current_id = node["if_ignore_wrong"]

            else:
                raise ValueError(f"Unsupported node type: {ntype}")

    def _tony_follows(self, trust: int) -> bool:
        """
        Soft decision: probability to follow grows with trust, centered at FOLLOW_THRESHOLD.
        Uses a clamped logistic so there’s always a small chance to do the opposite.
        """
        x = trust - FOLLOW_THRESHOLD
        p = 1.0 / (1.0 + math.exp(-FOLLOW_SIGMOID_K * x))         # 0..1 around 0.5 at threshold
        p = FOLLOW_PROB_FLOOR + (FOLLOW_PROB_CEIL - FOLLOW_PROB_FLOOR) * p  # clamp tails
        return self.random.random() < p