#!/usr/bin/env python3
"""Local, offline workflow ledger. It records evidence; it does not run an LLM.

All paths in packets are project-relative. State is authoritative; timeline is
a regenerable view. Reviewer identities are declarations, not authentication.
"""
import argparse
import contextlib
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone

STAGES = ("01-planning", "02-development", "03-qa", "04-wiki")
OWNERS = {STAGES[0]: ("gpt",), STAGES[1]: ("claude",),
          STAGES[2]: ("gpt",), STAGES[3]: ("hermes", "claude")}
REVIEWERS = {STAGES[0]: ("claude",), STAGES[1]: ("gpt",),
             STAGES[2]: ("gpt", "claude"), STAGES[3]: ("gpt",)}
LABELS = dict(waiting="대기", running="진행", review="검토", revision="수정", blocked="차단", complete="완료")


class WorkflowError(ValueError):
    pass


def need(value, message):
    if not value:
        raise WorkflowError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(root, relative, exists=True):
    need(isinstance(relative, str) and relative.strip(), "빈 경로")
    path = Path(relative)
    need(not path.is_absolute() and not re.match(r"^[A-Za-z]:", relative), "프로젝트 상대경로가 필요합니다")
    target = (root / path).resolve()
    need(target.is_relative_to(root.resolve()), "프로젝트 밖 경로는 사용할 수 없습니다")
    if exists:
        need(target.is_file(), f"파일 없음: {relative}")
    return target


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".workflow-", dir=path.parent)
    try:
        options = {} if isinstance(content, bytes) else {"encoding": "utf-8", "newline": "\n"}
        with os.fdopen(fd, "wb" if isinstance(content, bytes) else "w", **options) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def clean_packet(packet):
    need(isinstance(packet, dict), "입력 JSON은 객체여야 합니다")
    # Only explicitly supplied packets are recorded; never read environment or auth files.
    text = json_text(packet)
    check_secret_text(text)
    return packet


def check_secret_text(text):
    need(not re.search(r"\b(?:sk-[A-Za-z0-9_-]{16,}|Bearer\s+\S+|ghp_[A-Za-z0-9]{20,})", text, re.I),
         "인증정보로 보이는 문자열이 있습니다. 제거한 자료만 제출하세요")
    need(not re.search(r'"(?:password|api_key|access_token|refresh_token|client_secret|authorization|secret)"\s*:', text, re.I),
         "인증정보 필드는 기록할 수 없습니다")


class Ledger:
    def __init__(self, root, run_id):
        self.root = Path(root).resolve()
        need(re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", run_id), "실행 ID는 영문 소문자·숫자·하이픈·밑줄 1~64자")
        self.run = inside(self.root, f"docs/workflows/{run_id}", exists=False)
        self.run_id = run_id
        self.path = self.run / "state.json"

    @contextlib.contextmanager
    def locked(self):
        self.run.mkdir(parents=True, exist_ok=True)
        lock = self.run / ".lock"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise WorkflowError("다른 작업이 실행 중이거나 잠금이 남아 있습니다. 프로세스 종료를 확인 후 잠금을 복구하세요")
        try:
            with os.fdopen(fd, "w") as stream:
                stream.write(str(os.getpid()))
            yield
        finally:
            lock.unlink(missing_ok=True)

    def load(self):
        need(self.path.is_file(), "실행 기록 없음: init부터 실행하세요")
        return read_json(self.path)

    def save(self, state):
        self.write(self.path, json_text(state))
        self.render(state)

    def write(self, path, content):
        safe = inside(self.root, path.relative_to(self.root).as_posix(), exists=False)
        atomic(safe, content)

    def render(self, state):
        lines = [f"# {state['title']} — 실행 이력", "", "state.json에서 생성한 사건·판정 색인. 원문 전체의 사본이 아닙니다.", ""]
        for event in state["events"]:
            lines.append(f"- {event['at']} · {event['stage']} · {event['action']} · [기록]({event['raw']})")
        self.write(self.run / "timeline.md", "\n".join(lines) + "\n")

    def evidence(self, paths):
        need(isinstance(paths, list) and paths, "증거 파일이 필요합니다")
        result = []
        for name in paths:
            file = inside(self.root, name)
            need(file.stat().st_size > 0, f"빈 증거 파일: {name}")
            need(file.stat().st_size <= 20 * 1024 * 1024, "증거 파일은 20MB 이하로 분리하세요")
            content = file.read_bytes()
            check_secret_text(content.decode("utf-8", errors="replace"))
            hashed = hashlib.sha256(content).hexdigest()
            snapshot = self.run / "evidence" / (hashed + file.suffix)
            self.write(snapshot, content)
            result.append({"path": file.relative_to(self.root).as_posix(), "sha256": hashed,
                           "snapshot": snapshot.relative_to(self.root).as_posix()})
        return result

    def unchanged(self, entries):
        for entry in entries:
            file = inside(self.root, entry["path"])
            need(digest(file) == entry["sha256"], f"검증 후 파일 변경: {entry['path']}")

    def init(self, packet):
        clean_packet(packet)
        required = ("title", "goal", "audience", "why", "approach", "scope", "out_of_scope", "spec_version", "approval", "criteria")
        for key in required:
            need(packet.get(key), f"필수 요구명세 누락: {key}")
        need(isinstance(packet["criteria"], dict) and all(packet["criteria"].values()), "criteria는 ID와 완료 조건의 객체입니다")
        need(all(re.fullmatch(r"[A-Z][A-Z0-9_-]*", k) for k in packet["criteria"]), "완료 조건 ID 형식 오류")
        approval = self.evidence([packet["approval"]])
        spec_hash = hashlib.sha256(json_text(packet).encode()).hexdigest()
        with self.locked():
            if self.path.exists():
                state = self.load()
                need(state["request_hash"] == spec_hash, "같은 실행 ID의 요구사항이 다릅니다. 새 실행 ID를 사용하세요")
                self.verify(state)
                return state
            for folder in ("00-request", *STAGES, "raw"):
                (self.run / folder).mkdir(exist_ok=True)
            spec = self.run / "00-request" / "request.json"
            self.write(spec, json_text(packet))
            state = {"schema_version": 1, "run_id": self.run_id, "title": packet["title"],
                     "spec_version": packet["spec_version"], "request_hash": spec_hash,
                     "criteria": packet["criteria"], "baseline": approval + self.evidence([spec.relative_to(self.root).as_posix()]),
                     "stages": {s: {"status": "waiting", "attempt": 0, "reviews": 0,
                                     "defects": {}, "history": []} for s in STAGES},
                     "events": [], "operations": {}}
            self.event(state, "00-request", "init", packet, "init")
            self.save(state)
            return state

    def event(self, state, stage, action, packet, op):
        filename = f"raw/{len(state['events']) + 1:04d}-{action}.json"
        self.write(self.run / filename, json_text(packet))
        state["events"].append({"at": now(), "stage": stage, "action": action, "raw": filename,
                                "sha256": digest(self.run / filename), "operation": op})

    def verify(self, state, stages=STAGES):
        self.unchanged(state["baseline"])
        def snapshots(value):
            if isinstance(value, dict):
                if "snapshot" in value and "sha256" in value:
                    file = inside(self.root, value["snapshot"])
                    need(digest(file) == value["sha256"], "보존된 증거 스냅샷이 변경되었습니다")
                for item in value.values():
                    snapshots(item)
            elif isinstance(value, list):
                for item in value:
                    snapshots(item)
        snapshots(state)
        for name in stages:
            stage = state["stages"][name]
            if stage["status"] in ("review", "complete"):
                self.unchanged(stage["submission"]["artifacts"])
                if stage.get("review"):
                    self.unchanged(stage["review"]["evidence"])
        for event in state["events"]:
            file = inside(self.root, (self.run / event["raw"]).relative_to(self.root).as_posix())
            need(digest(file) == event["sha256"], "원문 기록이 변경되었습니다")

    def act(self, action, stage_name, packet, op):
        clean_packet(packet)
        need(stage_name in STAGES, "단계 이름 오류")
        need(re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", op), "operation ID 형식 오류")
        fingerprint = hashlib.sha256(json_text([action, stage_name, packet]).encode()).hexdigest()
        with self.locked():
            state = self.load()
            if op in state["operations"]:
                need(state["operations"][op] == fingerprint, "operation ID가 다른 작업에 사용되었습니다")
                self.verify(state)
                return state
            self.verify(state, STAGES[:STAGES.index(stage_name)] if action == "reopen" else STAGES)
            stage = state["stages"][stage_name]
            status = stage["status"]
            if action == "start":
                need(status in ("waiting", "revision"), "대기·수정 단계만 시작할 수 있습니다")
                index = STAGES.index(stage_name)
                need(all(state["stages"][s]["status"] == "complete" for s in STAGES[:index]), "선행 단계 미완료")
                for field in ("session", "provider", "model", "task"):
                    need(packet.get(field), f"작업자 정보 누락: {field}")
                need(packet["provider"] in OWNERS[stage_name], "단계 담당 제공자가 다릅니다")
                if stage_name == "03-qa":
                    dev = state["stages"]["02-development"]
                    need(packet["session"] not in (dev["owner"]["session"], dev["review"]["session"]), "QA는 제작·검토와 별도 세션이어야 합니다")
                if stage_name == "04-wiki" and packet["provider"] == "claude":
                    need(packet.get("fallback_reason"), "Hermes 미연결 대체 사유가 필요합니다")
                stage["owner"] = packet
                stage["attempt"] += 1
                if stage.get("submission"):
                    stage.setdefault("revision_rounds", []).append({"submission": stage["submission"], "review": stage.get("review")})
                stage.pop("submission", None)
                stage.pop("review", None)
                stage["status"] = "running"
            elif action == "submit":
                need(status == "running", "진행 단계만 제출할 수 있습니다")
                need(packet.get("session") == stage["owner"]["session"], "제작 세션 불일치")
                need(packet.get("spec_version") == state["spec_version"], "명세 버전 불일치")
                need(packet.get("summary") and packet.get("self_test"), "변경 요약과 자체 시험 결과가 필요합니다")
                need(isinstance(packet.get("limitations"), list), "미검증·제한 목록이 필요합니다(없으면 빈 목록)")
                artifacts = self.evidence(packet.get("artifacts"))
                if stage_name == "03-qa":
                    self.check_scenarios(state, packet)
                    artifacts += self.evidence([p for s in packet["scenarios"] for p in s["evidence"]])
                stage["submission"] = {**packet, "artifacts": artifacts}
                stage["status"] = "review"
            elif action == "review":
                need(status == "review", "검토 상태가 아닙니다")
                self.unchanged(stage["submission"]["artifacts"])
                need(packet.get("provider") in REVIEWERS[stage_name], "검토 제공자가 다릅니다")
                need(packet.get("session") and packet["session"] != stage["owner"]["session"], "자기 승인 금지: 별도 검토 세션 필요")
                if stage_name == "03-qa":
                    dev = state["stages"]["02-development"]
                    rounds = [dev] + dev.get("archived_rounds", [])
                    excluded = {r.get("owner", {}).get("session") for r in rounds}
                    excluded.update(r.get("review", {}).get("session") for r in rounds)
                    need(packet["session"] not in excluded, "QA 검토는 제작·개발 검토와 다른 세션이어야 합니다")
                need(packet.get("verdict") in ("pass", "fail"), "판정은 pass 또는 fail")
                need(packet.get("model") and packet.get("summary"), "검토 모델·판정 근거 누락")
                need(packet.get("spec_version") == state["spec_version"], "검토 명세 버전 불일치")
                need(set(packet.get("criteria", [])) == set(state["criteria"]), "모든 완료 조건을 검토해야 합니다")
                need(isinstance(packet.get("defects"), list), "defects 목록이 필요합니다")
                need(isinstance(packet.get("suggestions"), list), "선택적 제안 목록이 필요합니다")
                need((packet["verdict"] == "pass") == (len(packet["defects"]) == 0), "필수 결함이 있으면 통과할 수 없습니다")
                if stage_name == "03-qa" and packet["verdict"] == "pass":
                    need(all(s["passed"] for s in stage["submission"]["scenarios"]), "실패 QA는 통과할 수 없습니다. 결함을 반환하거나 제작 단계를 reopen하세요")
                evidence = self.evidence(packet.get("evidence"))
                stage["reviews"] += 1
                defect_ids = set()
                for defect in packet["defects"]:
                    need(isinstance(defect, dict), "결함은 객체여야 합니다")
                    need(all(defect.get(k) for k in ("id", "reason", "reproduce")), "결함 ID·이유·재현 방법 누락")
                    need(defect["id"] not in defect_ids, "중복 결함 ID")
                    defect_ids.add(defect["id"])
                    stage["defects"][defect["id"]] = stage["defects"].get(defect["id"], 0) + 1
                review = {**packet, "evidence": evidence, "artifacts": copy.deepcopy(stage["submission"]["artifacts"])}
                stage["review"] = review
                stage["history"].append(review)
                if stage["reviews"] > 3 or any(n >= 3 for n in stage["defects"].values()):
                    stage["status"] = "blocked"
                    stage["blocked_from"] = "review" if packet["verdict"] == "pass" else "revision"
                    stage["escalation"] = True
                    stage["reason"] = "반복 결함 또는 검토 횟수 초과: 마스터 재평가 필요"
                elif packet["verdict"] == "fail":
                    stage["status"] = "revision"
            elif action == "complete":
                need(status == "review" and stage.get("review", {}).get("verdict") == "pass", "통과한 독립 검토가 필요합니다")
                need(packet.get("role") == "master" and packet.get("session") and packet.get("reason"), "마스터의 완료 근거가 필요합니다")
                self.unchanged(stage["review"]["artifacts"] + stage["review"]["evidence"])
                stage["status"] = "complete"
            elif action == "block":
                need(status in ("waiting", "running", "review", "revision"), "현재 단계는 차단할 수 없습니다")
                need(packet.get("reason"), "차단 사유 필요")
                stage.update(status="blocked", blocked_from=status, reason=packet["reason"])
            elif action == "reopen":
                need(status != "waiting", "시작하지 않은 단계는 다시 열 수 없습니다")
                need(packet.get("role") == "master" and packet.get("session") and packet.get("reason"), "마스터의 재작업 근거 필요")
                need(not any(state["stages"][s].get("escalation") for s in STAGES[STAGES.index(stage_name):]), "반복 결함 재평가 후 다시 여세요")
                for name in STAGES[STAGES.index(stage_name):]:
                    old = state["stages"][name]
                    archive = old.get("archived_rounds", [])
                    if old["status"] != "waiting":
                        archive = archive + [{k: v for k, v in old.items() if k != "archived_rounds"}]
                    state["stages"][name] = {"status": "revision" if name == stage_name else "waiting",
                        "attempt": old["attempt"], "reviews": old["reviews"], "defects": old["defects"], "history": [], "archived_rounds": archive}
            elif action in ("resume", "reassess"):
                need(status == "blocked", "차단된 단계만 재개합니다. 진행 중이면 status의 다음 행동을 따르세요")
                need(packet.get("role") == "master" and packet.get("session") and packet.get("reason"), "마스터의 재개 근거 필요")
                if stage.get("escalation"):
                    need(action == "reassess" and packet.get("resolution"), "반복 결함은 reassess와 해결 방안이 필요합니다")
                    stage["reviews"] = 0
                    stage["defects"] = {}
                    stage["escalation"] = False
                stage["status"] = stage.pop("blocked_from")
                stage.pop("reason", None)
            else:
                raise WorkflowError("지원하지 않는 작업")
            state["operations"][op] = fingerprint
            self.event(state, stage_name, action, packet, op)
            self.save(state)
            return state

    def check_scenarios(self, state, packet):
        scenarios = packet.get("scenarios", [])
        need(isinstance(scenarios, list) and all(isinstance(s, dict) for s in scenarios), "scenarios는 객체 배열이어야 합니다")
        need(scenarios and {s.get("kind") for s in scenarios} >= {"normal", "expected_error"}, "정상·예상 오류 시나리오 필요")
        covered = set()
        for scenario in scenarios:
            need(all(scenario.get(k) for k in ("id", "criterion", "conditions", "expected", "actual", "evidence")), "QA 조건·예상·실제·증거 누락")
            need(scenario["criterion"] in state["criteria"], "알 수 없는 QA 완료 조건")
            need(isinstance(scenario.get("passed"), bool), "QA 결과 passed는 true 또는 false여야 합니다")
            self.evidence(scenario["evidence"])
            covered.add(scenario["criterion"])
        need(covered == set(state["criteria"]), "QA 완료 조건 누락")

    def summary(self):
        state = self.load()
        problems = []
        try:
            self.verify(state)
        except (WorkflowError, OSError) as error:
            problems.append(str(error))
        pending = next((s for s in STAGES if state["stages"][s]["status"] != "complete"), None)
        return {"run_id": self.run_id, "title": state["title"],
                "complete": pending is None and not problems,
                "next_stage": pending, "integrity_problems": problems,
                "stages": {s: LABELS[v["status"]] for s, v in state["stages"].items()},
                "limitations": {s: v.get("submission", {}).get("limitations", []) for s, v in state["stages"].items()},
                "previous_limitations": {s: [r["submission"].get("limitations", []) for r in v.get("revision_rounds", [])] for s, v in state["stages"].items()},
                "blocked": {s: v["reason"] for s, v in state["stages"].items() if v.get("reason")},
                "evidence": {s: v.get("submission", {}).get("artifacts", []) for s, v in state["stages"].items()},
                "identity_limit": "담당·세션은 신고 정보이며 실제 모델 호출이나 신원을 이 도구가 인증하지 않습니다.",
                "automation_limit": "로컬 상태 도구입니다. LLM 사이 자동 전달·실행·판정은 아직 연결하지 않았습니다."}


def doctor(root):
    root = Path(root).resolve()
    tools = {}
    for name in ("herdr", "codex", "claude", "hermes", "docker", "python"):
        local = root / ".local" / "bin" / name / (name + (".exe" if os.name == "nt" else ""))
        found = str(local) if local.is_file() else shutil.which(name)
        tools[name] = {"found": bool(found), "path": found, "authenticated": "not_checked", "working": "not_checked"}
    return {"tools": tools, "api_fallback_checked": False, "note": "파일 탐지만 수행. 인증·과금·Docker 실행은 별도 검증이 필요합니다."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("command", choices=("init", "status", "report", "doctor", "timeline", "start", "submit", "review", "complete", "block", "resume", "reassess", "reopen"))
    parser.add_argument("--id")
    parser.add_argument("--stage", choices=STAGES)
    parser.add_argument("--packet", help="프로젝트 상대경로 JSON 입력")
    parser.add_argument("--op", help="재시도 중복 방지 ID: 같은 명령 재시도에는 같은 ID")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = doctor(args.root)
        else:
            need(args.id, "--id 필요")
            ledger = Ledger(args.root, args.id)
            if args.command in ("status", "report"):
                result = ledger.summary()
            elif args.command == "timeline":
                with ledger.locked():
                    state = ledger.load()
                    ledger.render(state)
                result = ledger.summary()
            else:
                need(args.packet, "--packet 필요")
                packet = read_json(inside(ledger.root, args.packet))
                if args.command == "init":
                    ledger.init(packet)
                else:
                    need(args.stage and args.op, "--stage와 --op 필요")
                    ledger.act(args.command, args.stage, packet, args.op)
                result = ledger.summary()
        print(json_text(result))
        return 1 if result.get("integrity_problems") else 0
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as error:
        print(json_text({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
