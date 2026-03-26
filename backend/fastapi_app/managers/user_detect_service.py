"""
Serviço de detecção automática de usuários logados.

Roda automaticamente a cada 1 hora durante horário comercial (seg-sex, 7h-19h).
Também expõe funções para uso manual via API.
"""

import os
import re
import subprocess
import threading
import time
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Caminho para o diretório backend/
_backend_dir = Path(__file__).resolve().parent.parent.parent


# ═══════════════════════════════════════════════════════════════════════════════
# Funções de detecção (extraídas de routes/computers.py)
# ═══════════════════════════════════════════════════════════════════════════════

def _run_cmd(args, timeout=8):
    """Roda comando com kill forçado da árvore inteira via taskkill."""
    proc = None
    try:
        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        return (stdout or '', stderr or '', proc.returncode)
    except subprocess.TimeoutExpired:
        if proc:
            try:
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                    capture_output=True, timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        return (None, None, 'TIMEOUT')
    except FileNotFoundError:
        return (None, None, 'NOT_FOUND')
    except Exception as e:
        if proc:
            try:
                proc.kill()
            except Exception:
                pass
        return (None, None, str(e))


def _is_online(computer_name):
    try:
        r = subprocess.run(
            ['ping', '-n', '1', '-w', '1500', computer_name],
            capture_output=True, timeout=4,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return r.returncode == 0
    except Exception:
        return False


def _try_query_user(computer_name):
    stdout, stderr, rc = _run_cmd(['query', 'user', f'/server:{computer_name}'], timeout=5)
    if isinstance(rc, str):
        if rc == 'TIMEOUT':
            return (None, 'TIMEOUT')
        return (None, rc)
    output = (stdout or '').strip()
    if not output:
        stderr_text = (stderr or '').strip()
        if 'no user' in stderr_text.lower():
            return (None, 'NO_USER_LOGGED')
        return (None, stderr_text or f'rc={rc}')
    for line in output.splitlines()[1:]:
        parts = line.split()
        if not parts:
            continue
        username = parts[0].lstrip('>')
        upper = line.upper()
        if 'ACTIVE' in upper or 'ATIVO' in upper:
            return (username, None)
    lines = output.splitlines()
    if len(lines) > 1:
        first = lines[1].split()
        if first:
            return (first[0].lstrip('>'), None)
    return (None, 'NO_ACTIVE_SESSION')


def _try_psexec(computer_name):
    psexec_env = os.getenv('PSEXEC_PATH')
    repo64 = str(_backend_dir / 'psexec' / 'PsExec64.exe')
    repo32 = str(_backend_dir / 'psexec' / 'PsExec.exe')
    psexec = psexec_env or (repo64 if os.path.exists(repo64) else repo32)
    if not os.path.exists(psexec):
        return (None, 'PSEXEC_NOT_FOUND')

    args = [psexec, f'\\\\{computer_name}', '-accepteula', '-nobanner', 'query', 'user']
    stdout_raw, stderr_raw, rc = _run_cmd(args, timeout=10)
    if isinstance(rc, str):
        return (None, rc)
    stdout = (stdout_raw or '').strip()
    stderr = (stderr_raw or '').strip()
    output = stdout + '\n' + stderr if stdout and stderr else (stdout or stderr)
    if not output.strip():
        return (None, 'NO_OUTPUT')
    if 'no user' in output.lower():
        return (None, 'NO_USER_LOGGED')
    noise = [
        'CONNECTING', 'COPYING', 'STARTING', 'PSEXEC', 'COPYRIGHT',
        'SYSINTERNALS', 'CMD.EXE', 'PROCESS', 'EXITED', '\\\\',
        'SUCCESSFULLY', 'LOGON', 'IDLE TIME', 'SESSIONNAME', 'USERNAME',
        'USUARIO', 'NOME DA SESS', 'TEMPO OCIOSO', 'ERROR CODE', 'AUTHENTICATION',
    ]
    data_lines = []
    for line in output.splitlines():
        s = line.strip()
        if not s or s.startswith('---') or s.startswith('==='):
            continue
        if any(n in s.upper() for n in noise):
            continue
        data_lines.append(s)
    for line in data_lines:
        upper = line.upper()
        if 'ACTIVE' in upper or 'ATIVO' in upper:
            parts = line.split()
            if parts:
                return (parts[0].lstrip('>'), None)
    for line in data_lines:
        parts = line.split()
        if parts:
            c = parts[0].lstrip('>')
            if c and len(c) > 2 and not c.isdigit():
                return (c, None)
    return (None, 'PARSE_FAILED')


def format_detect_username(raw_user):
    """Formata nome de usuário: domínio\\user.name → User Name"""
    if not raw_user:
        return raw_user
    username = raw_user.split('\\')[-1] if '\\' in raw_user else raw_user
    parts = re.split(r'[._]', username)
    return ' '.join(p.capitalize() for p in parts if p)


def detect_user(computer_name):
    """Ping → query user → PsExec. Retorna dict com resultado."""
    t0 = time.time()
    if not _is_online(computer_name):
        return {'status': 'offline', 'computer_name': computer_name, 'elapsed': round(time.time() - t0, 1)}

    errors = []
    user, err = _try_query_user(computer_name)
    if user:
        return _build_detect_result(computer_name, user, 'query_user', t0)
    if err == 'NO_USER_LOGGED':
        return {'status': 'no_user', 'computer_name': computer_name, 'elapsed': round(time.time() - t0, 1)}
    errors.append(f'quser:{err}')

    user, err = _try_psexec(computer_name)
    if user:
        return _build_detect_result(computer_name, user, 'psexec', t0)
    if err == 'NO_USER_LOGGED':
        return {'status': 'no_user', 'computer_name': computer_name, 'elapsed': round(time.time() - t0, 1)}
    errors.append(f'psexec:{err}')

    return {
        'status': 'error',
        'computer_name': computer_name,
        'error': ' | '.join(errors),
        'elapsed': round(time.time() - t0, 1)
    }


def _build_detect_result(computer_name, raw_user, method, t0):
    from ..managers import sql_manager

    formatted = format_detect_username(raw_user)
    try:
        rows = sql_manager.execute_query(
            "SELECT Usuario_Atual FROM computers WHERE name = ?",
            params=(computer_name,)
        )
        if rows:
            db_current = rows[0].get('Usuario_Atual')
            if db_current != formatted:
                sql_manager.execute_query(
                    "UPDATE computers SET Usuario_Atual = ?, Usuario_Anterior = ?, updated_at = GETDATE() WHERE name = ?",
                    params=(formatted, db_current, computer_name)
                )
    except Exception as e:
        logger.warning(f'Erro ao salvar usuario {formatted} para {computer_name}: {e}')

    return {
        'status': 'ok',
        'computer_name': computer_name,
        'raw_user': raw_user,
        'usuario_atual': formatted,
        'method': method,
        'saved': True,
        'elapsed': round(time.time() - t0, 1)
    }


def run_bulk_detect_onshore():
    """Detecta usuários de todas as máquinas onshore (SHQ*). Pode ser chamada como task ou agendada."""
    from ..managers import sql_manager

    try:
        rows = sql_manager.execute_query(
            "SELECT name FROM computers "
            "WHERE is_enabled = 1 AND is_domain_controller = 0 "
            "AND name LIKE 'SHQ%' "
            "AND name NOT LIKE '%DC%' AND name NOT LIKE '%SVR%' "
            "ORDER BY name"
        )
        total = len(rows)
        ok = offline = no_user = errors = 0
        logger.info(f'[detect-users] Iniciando para {total} máquinas onshore...')

        for i, row in enumerate(rows, 1):
            name = row['name']
            result = detect_user(name)
            s = result.get('status')
            if s == 'ok':
                ok += 1
                logger.info(f'  [{i}/{total}] OK {name}: {result.get("usuario_atual")} [{result.get("method")}] ({result.get("elapsed")}s)')
            elif s == 'offline':
                offline += 1
            elif s == 'no_user':
                no_user += 1
            else:
                errors += 1
                logger.warning(f'  [{i}/{total}] FAIL {name}: {result.get("error")} ({result.get("elapsed")}s)')

        logger.info(f'[detect-users] DONE — {total} máquinas: ok={ok} offline={offline} sem_user={no_user} erros={errors}')
        return {'total': total, 'ok': ok, 'offline': offline, 'no_user': no_user, 'errors': errors}
    except Exception:
        logger.exception('[detect-users] Erro crítico')
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Agendamento automático — horário comercial (seg-sex, 7h-19h)
# ═══════════════════════════════════════════════════════════════════════════════

class UserDetectScheduler:
    """Executa detecção de usuários a cada 1h durante horário comercial."""

    INTERVAL_SECONDS = 3600          # 1 hora entre execuções
    BUSINESS_HOUR_START = 7          # 07:00
    BUSINESS_HOUR_END = 19           # 19:00
    BUSINESS_DAYS = range(0, 5)      # seg=0 … sex=4

    def __init__(self):
        self._thread = None
        self._running = False
        self._last_run = None

    @property
    def last_run(self):
        return self._last_run

    @property
    def is_running(self):
        return self._running

    def _is_business_hours(self):
        now = datetime.now()
        return (
            now.weekday() in self.BUSINESS_DAYS
            and self.BUSINESS_HOUR_START <= now.hour < self.BUSINESS_HOUR_END
        )

    def start(self):
        if self._running:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info(
            '🕐 UserDetectScheduler iniciado — roda seg-sex %dh às %dh, a cada %d min',
            self.BUSINESS_HOUR_START, self.BUSINESS_HOUR_END,
            self.INTERVAL_SECONDS // 60
        )

    def stop(self):
        self._running = False

    def _loop(self):
        self._running = True
        # Espera inicial de 5 min para dar tempo do servidor estabilizar
        time.sleep(300)
        while self._running:
            try:
                if self._is_business_hours():
                    logger.info('[UserDetectScheduler] Horário comercial — iniciando detecção...')
                    self._last_run = datetime.now()
                    run_bulk_detect_onshore()
                else:
                    logger.debug('[UserDetectScheduler] Fora do horário comercial, pulando.')
                time.sleep(self.INTERVAL_SECONDS)
            except Exception:
                logger.exception('[UserDetectScheduler] Erro no loop')
                time.sleep(300)


# Singleton
user_detect_scheduler = UserDetectScheduler()
