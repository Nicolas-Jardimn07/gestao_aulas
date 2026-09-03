"""
Camada de banco de dados do projeto Acordes de Lagoinha.

Usa SQLite (um único arquivo em data/acordes.db) para que o gestor e os
professores, mesmo em máquinas diferentes rodando o mesmo app, leiam e
gravem sempre nas mesmas turmas, aulas e alunos — sem depender de rede
externa, então é rápido mesmo com muitos registros.
"""
import os
import json
import sqlite3
import threading
import uuid
import hashlib
import binascii
from datetime import datetime

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "acordes.db")

os.makedirs(DATA_DIR, exist_ok=True)

_LOCK = threading.Lock()


@st.cache_resource(show_spinner=False)
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def new_id():
    return uuid.uuid4().hex[:12]


SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('professor','gestor')),
    salt TEXT,
    pass_hash TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS turmas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    community TEXT,
    target_hours_min REAL DEFAULT 20,
    target_students_min INTEGER DEFAULT 15,
    target_students_max INTEGER DEFAULT 20,
    created_by TEXT,
    created_at TEXT,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS turma_members (
    turma_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    PRIMARY KEY (turma_id, account_id)
);

CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    turma_id TEXT NOT NULL,
    name TEXT NOT NULL,
    birth_date TEXT,
    guardian_name TEXT,
    address TEXT,
    school TEXT,
    image_auth TEXT DEFAULT 'pendente',
    image_auth_note TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS classes (
    id TEXT PRIMARY KEY,
    turma_id TEXT NOT NULL,
    date TEXT,
    start_time TEXT,
    end_time TEXT,
    hours REAL,
    professors TEXT,
    diary_acordes TEXT,
    diary_exercicios TEXT,
    diary_repertorio TEXT,
    diary_dinamicas TEXT,
    access TEXT,
    access_other TEXT,
    locked INTEGER DEFAULT 0,
    created_by TEXT,
    created_at TEXT,
    last_edited_by TEXT,
    last_edited_at TEXT
);

CREATE TABLE IF NOT EXISTS attendance (
    id TEXT PRIMARY KEY,
    class_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    present INTEGER,
    justification TEXT
);

CREATE TABLE IF NOT EXISTS final_events (
    id TEXT PRIMARY KEY,
    turma_id TEXT UNIQUE NOT NULL,
    date TEXT,
    location TEXT,
    time TEXT,
    repertoire TEXT,
    participant_ids TEXT,
    audience TEXT,
    accessibility TEXT,
    video_note TEXT,
    locked INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    turma_id TEXT,
    account_id TEXT,
    account_name TEXT,
    role TEXT,
    action TEXT,
    at TEXT
);

CREATE TABLE IF NOT EXISTS project_reports (
    turma_id TEXT PRIMARY KEY,
    proponente TEXT,
    termo_numero TEXT,
    vigencia_inicio TEXT,
    vigencia_fim TEXT,
    valor_repassado TEXT,
    data_entrega TEXT,
    resumo TEXT,
    acoes_planejadas_status TEXT,
    acoes_desenvolvidas TEXT,
    gerou_produtos TEXT,
    produtos_gerados TEXT,
    produtos_disponibilizacao TEXT,
    resultados_texto TEXT,
    resultados_checkboxes TEXT,
    equipe_mudancas TEXT,
    equipe_mudancas_obs TEXT,
    modo_acesso TEXT,
    plataformas TEXT,
    links_plataformas TEXT,
    forma_presencial TEXT,
    municipio_estado TEXT,
    locais_realizacao TEXT,
    divulgacao TEXT,
    topicos_adicionais TEXT
);

CREATE TABLE IF NOT EXISTS team_members (
    id TEXT PRIMARY KEY,
    turma_id TEXT NOT NULL,
    nome TEXT,
    funcao TEXT,
    cpf_cnpj TEXT,
    negra_indigena TEXT,
    deficiencia TEXT
);

CREATE TABLE IF NOT EXISTS metas (
    id TEXT PRIMARY KEY,
    turma_id TEXT NOT NULL,
    descricao TEXT,
    status TEXT,
    observacao TEXT,
    justificativa TEXT,
    ordem INTEGER DEFAULT 0
);
"""


def init_db():
    conn = get_conn()
    with _LOCK:
        conn.executescript(SCHEMA)
        conn.commit()
    seed_default_accounts()


# ------------------------------------------------------------------ #
# Contas / autenticação
# ------------------------------------------------------------------ #
def seed_default_accounts():
    conn = get_conn()
    existing = conn.execute("SELECT COUNT(*) c FROM accounts").fetchone()["c"]
    if existing:
        return
    defaults = [
        ("Kéviny", "professor"),
        ("Talison", "professor"),
        ("Nícolas", "gestor"),
    ]
    with _LOCK:
        for name, role in defaults:
            conn.execute(
                "INSERT INTO accounts (id,name,role,salt,pass_hash,created_at) VALUES (?,?,?,?,?,?)",
                (new_id(), name, role, None, None, now_iso()),
            )
        conn.commit()


def get_accounts(role=None):
    conn = get_conn()
    if role:
        rows = conn.execute("SELECT * FROM accounts WHERE role=? ORDER BY name", (role,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM accounts ORDER BY role DESC, name").fetchall()
    return [dict(r) for r in rows]


def get_account(account_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
    return dict(row) if row else None


def create_account(name, role):
    conn = get_conn()
    aid = new_id()
    with _LOCK:
        conn.execute(
            "INSERT INTO accounts (id,name,role,salt,pass_hash,created_at) VALUES (?,?,?,?,?,?)",
            (aid, name.strip(), role, None, None, now_iso()),
        )
        conn.commit()
    return aid


def _hash_password(password, salt_hex=None):
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return binascii.hexlify(salt).decode(), binascii.hexlify(digest).decode()


def set_password(account_id, password):
    salt_hex, hash_hex = _hash_password(password)
    conn = get_conn()
    with _LOCK:
        conn.execute("UPDATE accounts SET salt=?, pass_hash=? WHERE id=?", (salt_hex, hash_hex, account_id))
        conn.commit()


def verify_login(account_id, password):
    acc = get_account(account_id)
    if not acc or not acc["pass_hash"]:
        return False
    _, hash_hex = _hash_password(password, acc["salt"])
    return hash_hex == acc["pass_hash"]


def reset_password(account_id):
    conn = get_conn()
    with _LOCK:
        conn.execute("UPDATE accounts SET salt=NULL, pass_hash=NULL WHERE id=?", (account_id,))
        conn.commit()


def delete_account(account_id):
    conn = get_conn()
    with _LOCK:
        conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        conn.execute("DELETE FROM turma_members WHERE account_id=?", (account_id,))
        conn.commit()


# ------------------------------------------------------------------ #
# Turmas
# ------------------------------------------------------------------ #
def get_turmas():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM turmas WHERE active=1 ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_turma(turma_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM turmas WHERE id=?", (turma_id,)).fetchone()
    return dict(row) if row else None


def create_turma(name, community, hmin, smin, smax, created_by, member_ids=None):
    conn = get_conn()
    tid = new_id()
    with _LOCK:
        conn.execute(
            """INSERT INTO turmas (id,name,community,target_hours_min,target_students_min,
               target_students_max,created_by,created_at,active) VALUES (?,?,?,?,?,?,?,?,1)""",
            (tid, name.strip(), community.strip(), hmin, smin, smax, created_by, now_iso()),
        )
        for aid in (member_ids or []):
            conn.execute(
                "INSERT OR IGNORE INTO turma_members (turma_id,account_id) VALUES (?,?)", (tid, aid)
            )
        conn.commit()
    return tid


def update_turma(turma_id, **fields):
    if not fields:
        return
    conn = get_conn()
    cols = ", ".join(f"{k}=?" for k in fields.keys())
    with _LOCK:
        conn.execute(f"UPDATE turmas SET {cols} WHERE id=?", (*fields.values(), turma_id))
        conn.commit()


def get_turma_members(turma_id):
    conn = get_conn()
    rows = conn.execute(
        """SELECT a.* FROM accounts a
           JOIN turma_members m ON m.account_id=a.id
           WHERE m.turma_id=? ORDER BY a.name""",
        (turma_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def set_turma_members(turma_id, account_ids):
    conn = get_conn()
    with _LOCK:
        conn.execute("DELETE FROM turma_members WHERE turma_id=?", (turma_id,))
        for aid in account_ids:
            conn.execute("INSERT INTO turma_members (turma_id,account_id) VALUES (?,?)", (turma_id, aid))
        conn.commit()


def get_turmas_for_account(account_id):
    conn = get_conn()
    rows = conn.execute(
        """SELECT t.* FROM turmas t
           JOIN turma_members m ON m.turma_id=t.id
           WHERE m.account_id=? AND t.active=1 ORDER BY t.created_at DESC""",
        (account_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------ #
# Alunos
# ------------------------------------------------------------------ #
def get_students(turma_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM students WHERE turma_id=? ORDER BY name", (turma_id,)).fetchall()
    return [dict(r) for r in rows]


def get_active_students(turma_id):
    return [s for s in get_students(turma_id) if s["active"]]


def get_student(student_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    return dict(row) if row else None


def create_student(turma_id, **fields):
    conn = get_conn()
    sid = new_id()
    with _LOCK:
        conn.execute(
            """INSERT INTO students (id,turma_id,name,birth_date,guardian_name,address,school,
               image_auth,image_auth_note,active,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sid, turma_id, fields.get("name"), fields.get("birth_date"), fields.get("guardian_name"),
                fields.get("address"), fields.get("school"), fields.get("image_auth", "pendente"),
                fields.get("image_auth_note"), int(fields.get("active", True)), now_iso(),
            ),
        )
        conn.commit()
    return sid


def update_student(student_id, **fields):
    if not fields:
        return
    conn = get_conn()
    cols = ", ".join(f"{k}=?" for k in fields.keys())
    with _LOCK:
        conn.execute(f"UPDATE students SET {cols} WHERE id=?", (*fields.values(), student_id))
        conn.commit()


# ------------------------------------------------------------------ #
# Aulas / diário / frequência
# ------------------------------------------------------------------ #
def get_classes(turma_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM classes WHERE turma_id=? ORDER BY date DESC, start_time DESC", (turma_id,)
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["professors"] = json.loads(d["professors"] or "[]")
        d["access"] = json.loads(d["access"] or "[]")
        out.append(d)
    return out


def get_class(class_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["professors"] = json.loads(d["professors"] or "[]")
    d["access"] = json.loads(d["access"] or "[]")
    return d


def create_class(turma_id, date, start_time, end_time, hours, professors, diary, access,
                  access_other, attendance_records, created_by):
    conn = get_conn()
    cid = new_id()
    with _LOCK:
        conn.execute(
            """INSERT INTO classes (id,turma_id,date,start_time,end_time,hours,professors,
               diary_acordes,diary_exercicios,diary_repertorio,diary_dinamicas,access,access_other,
               locked,created_by,created_at,last_edited_by,last_edited_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0,?,?,?,?)""",
            (
                cid, turma_id, date, start_time, end_time, hours, json.dumps(professors),
                diary.get("acordes", ""), diary.get("exercicios", ""), diary.get("repertorio", ""),
                diary.get("dinamicas", ""), json.dumps(access), access_other, created_by, now_iso(),
                created_by, now_iso(),
            ),
        )
        for rec in attendance_records:
            conn.execute(
                "INSERT INTO attendance (id,class_id,student_id,present,justification) VALUES (?,?,?,?,?)",
                (new_id(), cid, rec["student_id"], int(rec["present"]), rec.get("justification", "")),
            )
        conn.commit()
    return cid


def update_class(class_id, date, start_time, end_time, hours, professors, diary, access,
                  access_other, attendance_records, edited_by):
    conn = get_conn()
    with _LOCK:
        conn.execute(
            """UPDATE classes SET date=?, start_time=?, end_time=?, hours=?, professors=?,
               diary_acordes=?, diary_exercicios=?, diary_repertorio=?, diary_dinamicas=?,
               access=?, access_other=?, last_edited_by=?, last_edited_at=? WHERE id=?""",
            (
                date, start_time, end_time, hours, json.dumps(professors), diary.get("acordes", ""),
                diary.get("exercicios", ""), diary.get("repertorio", ""), diary.get("dinamicas", ""),
                json.dumps(access), access_other, edited_by, now_iso(), class_id,
            ),
        )
        conn.execute("DELETE FROM attendance WHERE class_id=?", (class_id,))
        for rec in attendance_records:
            conn.execute(
                "INSERT INTO attendance (id,class_id,student_id,present,justification) VALUES (?,?,?,?,?)",
                (new_id(), class_id, rec["student_id"], int(rec["present"]), rec.get("justification", "")),
            )
        conn.commit()


def set_class_locked(class_id, locked):
    conn = get_conn()
    with _LOCK:
        conn.execute("UPDATE classes SET locked=? WHERE id=?", (int(locked), class_id))
        conn.commit()


def get_attendance(class_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM attendance WHERE class_id=?", (class_id,)).fetchall()
    return [dict(r) for r in rows]


def get_attendance_for_turma(turma_id):
    """Frequência de TODAS as aulas da turma em uma única consulta (evita 1 consulta por aula)."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT a.* FROM attendance a
           JOIN classes c ON c.id = a.class_id
           WHERE c.turma_id=?""",
        (turma_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------ #
# Recital / evento final
# ------------------------------------------------------------------ #
def get_final_event(turma_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM final_events WHERE turma_id=?", (turma_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["participant_ids"] = json.loads(d["participant_ids"] or "[]")
    return d


def upsert_final_event(turma_id, date, location, time_, repertoire, participant_ids, audience,
                        accessibility, video_note):
    conn = get_conn()
    existing = get_final_event(turma_id)
    with _LOCK:
        if existing:
            conn.execute(
                """UPDATE final_events SET date=?, location=?, time=?, repertoire=?, participant_ids=?,
                   audience=?, accessibility=?, video_note=? WHERE turma_id=?""",
                (date, location, time_, repertoire, json.dumps(participant_ids), audience,
                 accessibility, video_note, turma_id),
            )
            eid = existing["id"]
        else:
            eid = new_id()
            conn.execute(
                """INSERT INTO final_events (id,turma_id,date,location,time,repertoire,participant_ids,
                   audience,accessibility,video_note,locked) VALUES (?,?,?,?,?,?,?,?,?,?,0)""",
                (eid, turma_id, date, location, time_, repertoire, json.dumps(participant_ids), audience,
                 accessibility, video_note),
            )
        conn.commit()
    return eid


def set_event_locked(turma_id, locked):
    conn = get_conn()
    with _LOCK:
        conn.execute("UPDATE final_events SET locked=? WHERE turma_id=?", (int(locked), turma_id))
        conn.commit()


# ------------------------------------------------------------------ #
# Auditoria
# ------------------------------------------------------------------ #
def log_action(turma_id, account_id, account_name, role, action):
    conn = get_conn()
    with _LOCK:
        conn.execute(
            "INSERT INTO audit_log (id,turma_id,account_id,account_name,role,action,at) VALUES (?,?,?,?,?,?,?)",
            (new_id(), turma_id, account_id, account_name, role, action, now_iso()),
        )
        conn.commit()


def get_audit(turma_id=None, limit=400):
    conn = get_conn()
    if turma_id:
        rows = conn.execute(
            "SELECT * FROM audit_log WHERE turma_id=? ORDER BY at DESC LIMIT ?", (turma_id, limit)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------ #
# Relatório Final (Anexo VI)
# ------------------------------------------------------------------ #
REPORT_JSON_FIELDS = ("produtos_gerados", "resultados_checkboxes", "plataformas", "locais_realizacao")


def get_project_report(turma_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM project_reports WHERE turma_id=?", (turma_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    for f in REPORT_JSON_FIELDS:
        d[f] = json.loads(d[f]) if d[f] else []
    return d


def upsert_project_report(turma_id, **fields):
    for f in REPORT_JSON_FIELDS:
        if f in fields and not isinstance(fields[f], str):
            fields[f] = json.dumps(fields[f])
    conn = get_conn()
    existing = conn.execute("SELECT turma_id FROM project_reports WHERE turma_id=?", (turma_id,)).fetchone()
    with _LOCK:
        if existing:
            cols = ", ".join(f"{k}=?" for k in fields.keys())
            conn.execute(f"UPDATE project_reports SET {cols} WHERE turma_id=?", (*fields.values(), turma_id))
        else:
            keys = ["turma_id"] + list(fields.keys())
            placeholders = ", ".join("?" for _ in keys)
            conn.execute(
                f"INSERT INTO project_reports ({', '.join(keys)}) VALUES ({placeholders})",
                (turma_id, *fields.values()),
            )
        conn.commit()


def get_team_members(turma_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM team_members WHERE turma_id=? ORDER BY nome", (turma_id,)).fetchall()
    return [dict(r) for r in rows]


def add_team_member(turma_id, nome, funcao, cpf_cnpj, negra_indigena, deficiencia):
    conn = get_conn()
    mid = new_id()
    with _LOCK:
        conn.execute(
            """INSERT INTO team_members (id,turma_id,nome,funcao,cpf_cnpj,negra_indigena,deficiencia)
               VALUES (?,?,?,?,?,?,?)""",
            (mid, turma_id, nome, funcao, cpf_cnpj, negra_indigena, deficiencia),
        )
        conn.commit()
    return mid


def delete_team_member(member_id):
    conn = get_conn()
    with _LOCK:
        conn.execute("DELETE FROM team_members WHERE id=?", (member_id,))
        conn.commit()


def get_metas(turma_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM metas WHERE turma_id=? ORDER BY ordem, rowid", (turma_id,)).fetchall()
    return [dict(r) for r in rows]


def add_meta(turma_id, descricao, status, observacao, justificativa):
    conn = get_conn()
    mid = new_id()
    ordem = len(get_metas(turma_id))
    with _LOCK:
        conn.execute(
            """INSERT INTO metas (id,turma_id,descricao,status,observacao,justificativa,ordem)
               VALUES (?,?,?,?,?,?,?)""",
            (mid, turma_id, descricao, status, observacao, justificativa, ordem),
        )
        conn.commit()
    return mid


def update_meta(meta_id, **fields):
    if not fields:
        return
    conn = get_conn()
    cols = ", ".join(f"{k}=?" for k in fields.keys())
    with _LOCK:
        conn.execute(f"UPDATE metas SET {cols} WHERE id=?", (*fields.values(), meta_id))
        conn.commit()


def delete_meta(meta_id):
    conn = get_conn()
    with _LOCK:
        conn.execute("DELETE FROM metas WHERE id=?", (meta_id,))
        conn.commit()
