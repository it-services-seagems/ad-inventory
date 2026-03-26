#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para buscar usuários logados em máquinas Windows e atualizar no banco de dados.

Estratégia não-invasiva (nenhuma alteração é feita na máquina remota):
  1. Ping rápido para verificar se a máquina está online
  2. `query user /server:<NOME>` — usa protocolo RDP, sem WinRM, rápido (~1-2s)
  3. PsExec + `query user` (read-only) — fallback confiável via Kerberos

Uso:
  python users.py -m NOME_MAQUINA          # uma máquina específica
  python users.py -p SHQ -l 10             # prefixo SHQ, limite 10
  python users.py -l 50                    # 50 primeiras máquinas ativas
  python users.py -v                       # modo verbose (debug)
"""

import os
import sys
import time
import pyodbc
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
import subprocess
import re
from pathlib import Path

# ── Paths & env ──────────────────────────────────────────────────────────────
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir.parent))

load_dotenv(dotenv_path=backend_dir / '.env')

try:
    from fastapi_app.config import SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD, USE_WINDOWS_AUTH
except ImportError:
    SQL_SERVER = os.getenv('SQL_SERVER', 'CLOSQL02')
    SQL_DATABASE = os.getenv('SQL_DATABASE', 'DellReports')
    SQL_USERNAME = os.getenv('SQL_USERNAME')
    SQL_PASSWORD = os.getenv('SQL_PASSWORD')
    USE_WINDOWS_AUTH = os.getenv('USE_WINDOWS_AUTH', 'true').lower() == 'true'

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_DIR = backend_dir / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-7s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'users_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  SQL Manager (lightweight, same connection pattern as the API)
# ═══════════════════════════════════════════════════════════════════════════════
class SQLManager:
    def __init__(self):
        if USE_WINDOWS_AUTH:
            self.conn_str = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={SQL_SERVER};"
                f"DATABASE={SQL_DATABASE};"
                f"Trusted_Connection=yes;"
            )
        else:
            self.conn_str = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={SQL_SERVER};"
                f"DATABASE={SQL_DATABASE};"
                f"UID={SQL_USERNAME};"
                f"PWD={SQL_PASSWORD};"
            )
        with pyodbc.connect(self.conn_str) as conn:
            conn.cursor().execute("SELECT 1")
        logger.info(f"SQL Server conectado: {SQL_SERVER}/{SQL_DATABASE}")

    def execute(self, query, params=None, fetch=True):
        with pyodbc.connect(self.conn_str) as conn:
            cur = conn.cursor()
            cur.execute(query, params or ())
            if fetch:
                cols = [c[0] for c in cur.description] if cur.description else []
                return [dict(zip(cols, row)) for row in cur.fetchall()]
            conn.commit()
            return cur.rowcount


# ═══════════════════════════════════════════════════════════════════════════════
#  User Manager — estratégia não-invasiva
# ═══════════════════════════════════════════════════════════════════════════════
class UserManager:
    def __init__(self):
        self.sql = SQLManager()
        self.ad_username = os.getenv('AD_USERNAME', '')
        self.ad_password = os.getenv('AD_PASSWORD', '')

    # ── buscar máquinas ──────────────────────────────────────────────────────
    def get_computers(self, limit=50, prefix=None, specific=None):
        if specific:
            return self.sql.execute(
                "SELECT id, name, dns_hostname, Usuario_Atual, Usuario_Anterior "
                "FROM computers WHERE name = ? AND is_enabled = 1 AND is_domain_controller = 0",
                (specific,)
            )
        if prefix:
            return self.sql.execute(
                "SELECT TOP (?) id, name, dns_hostname, Usuario_Atual, Usuario_Anterior "
                "FROM computers WHERE name LIKE ? AND is_enabled = 1 AND is_domain_controller = 0 "
                "ORDER BY name",
                (limit, f'{prefix}%')
            )
        return self.sql.execute(
            "SELECT TOP (?) id, name, dns_hostname, Usuario_Atual, Usuario_Anterior "
            "FROM computers WHERE is_enabled = 1 AND is_domain_controller = 0 "
            "AND name NOT LIKE '%DC%' AND name NOT LIKE '%SVR%' ORDER BY name",
            (limit,)
        )

    # ── Helper: rodar subprocess com kill forçado (árvore inteira) ───────
    @staticmethod
    def _run_cmd(args, timeout=8):
        """Roda comando e mata TODA a árvore de processos via taskkill se exceder timeout."""
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

    # ── Ping check ───────────────────────────────────────────────────────────
    @staticmethod
    def _is_online(computer_name):
        """Ping rápido: 1 pacote, timeout 1500ms."""
        try:
            r = subprocess.run(
                ['ping', '-n', '1', '-w', '1500', computer_name],
                capture_output=True, timeout=4,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return r.returncode == 0
        except Exception:
            return False

    # ── Método 1: query user ─────────────────────────────────────────────────
    def _try_query_user(self, computer_name):
        logger.debug(f'  [{computer_name}] query user...')
        stdout, stderr, rc = self._run_cmd(
            ['query', 'user', f'/server:{computer_name}'], timeout=5
        )
        if rc == 'TIMEOUT':
            return (None, 'TIMEOUT_QUERY_USER')
        if isinstance(rc, str):
            return (None, rc)

        output = (stdout or '').strip()
        stderr_text = (stderr or '').strip()

        if not output:
            if 'no user' in stderr_text.lower():
                return (None, 'NO_USER_LOGGED')
            return (None, stderr_text or f'rc={rc}')

        for line in output.splitlines()[1:]:
            parts = line.split()
            if not parts:
                continue
            username = parts[0].lstrip('>')
            upper = line.upper()
            if 'ACTIVE' in upper or 'ATIVO' in upper or 'ACTIV' in upper:
                return (username, None)

        # Nenhuma ativa — retornar primeiro
        lines = output.splitlines()
        if len(lines) > 1:
            first = lines[1].split()
            if first:
                return (first[0].lstrip('>'), None)

        return (None, 'NO_ACTIVE_SESSION')

    # ── Método 2: PsExec + query user ────────────────────────────────────────
    def _try_psexec_query(self, computer_name):
        psexec_env = os.getenv('PSEXEC_PATH')
        repo64 = str(backend_dir / 'psexec' / 'PsExec64.exe')
        repo32 = str(backend_dir / 'psexec' / 'PsExec.exe')
        psexec = psexec_env or (repo64 if os.path.exists(repo64) else repo32)

        if not os.path.exists(psexec):
            return (None, 'PSEXEC_NOT_FOUND')

        # Tentativa 1: Kerberos (sessão atual — sem -u/-p)
        logger.debug(f'  [{computer_name}] PsExec Kerberos...')
        args1 = [psexec, f'\\\\{computer_name}', '-accepteula', '-nobanner', 'query', 'user']
        user, err = self._parse_psexec(args1)
        if user:
            return (user, None)

        # Tentativa 2: credenciais explícitas
        if self.ad_username and self.ad_password:
            logger.debug(f'  [{computer_name}] PsExec credenciais...')
            args2 = [
                psexec, f'\\\\{computer_name}', '-accepteula', '-nobanner',
                '-u', self.ad_username, '-p', self.ad_password,
                'query', 'user'
            ]
            user, err2 = self._parse_psexec(args2)
            if user:
                return (user, None)
            return (None, f'kerberos:{err} | cred:{err2}')

        return (None, err)

    def _parse_psexec(self, args):
        """Roda PsExec e parseia output de 'query user'."""
        stdout_raw, stderr_raw, rc = self._run_cmd(args, timeout=10)

        if rc == 'TIMEOUT':
            return (None, 'TIMEOUT_PSEXEC')
        if isinstance(rc, str):
            return (None, rc)

        stdout = (stdout_raw or '').strip()
        stderr = (stderr_raw or '').strip()
        output = stdout + '\n' + stderr if stdout and stderr else (stdout or stderr)

        logger.debug(f'  PsExec stdout: {repr(stdout[:150])}')
        logger.debug(f'  PsExec stderr: {repr(stderr[:150])}')

        if not output.strip():
            return (None, f'NO_OUTPUT rc={rc}')

        if 'no user' in output.lower():
            return (None, 'NO_USER_LOGGED')

        # Filtrar ruído
        noise = [
            'CONNECTING', 'COPYING', 'STARTING', 'PSEXEC',
            'COPYRIGHT', 'SYSINTERNALS', 'CMD.EXE',
            'PROCESS', 'EXITED', '\\\\', 'SUCCESSFULLY',
            'LOGON', 'IDLE TIME', 'SESSIONNAME', 'USERNAME',
            'USUARIO', 'NOME DA SESS', 'TEMPO OCIOSO',
            'ERROR CODE', 'AUTHENTICATION',
        ]
        data_lines = []
        for line in output.splitlines():
            s = line.strip()
            if not s or s.startswith('---') or s.startswith('==='):
                continue
            upper = s.upper()
            if any(n in upper for n in noise):
                continue
            data_lines.append(s)

        # Sessão ativa
        for line in data_lines:
            upper = line.upper()
            if 'ACTIVE' in upper or 'ATIVO' in upper or 'ACTIV' in upper:
                parts = line.split()
                if parts:
                    return (parts[0].lstrip('>'), None)

        # Qualquer usuário
        for line in data_lines:
            parts = line.split()
            if parts:
                candidate = parts[0].lstrip('>')
                if candidate and len(candidate) > 2 and not candidate.isdigit():
                    return (candidate, None)

        return (None, f'PARSE_FAILED:{output[:100]}')

    # ── Resolver usuário ─────────────────────────────────────────────────────
    def get_logged_user(self, computer_name):
        """Ping → query user → PsExec. Retorna (user, method, error)."""
        logger.debug(f'  [{computer_name}] ping...')
        if not self._is_online(computer_name):
            return (None, None, 'OFFLINE')

        errors = []

        user, err = self._try_query_user(computer_name)
        if user:
            return (user, 'query_user', None)
        if err == 'NO_USER_LOGGED':
            return (None, None, 'NO_USER_LOGGED')
        errors.append(f'quser:{err}')

        user, err = self._try_psexec_query(computer_name)
        if user:
            return (user, 'psexec_query', None)
        if err == 'NO_USER_LOGGED':
            return (None, None, 'NO_USER_LOGGED')
        errors.append(f'psexec:{err}')

        return (None, None, ' | '.join(errors))

    # ── Formatar nome ────────────────────────────────────────────────────────
    @staticmethod
    def format_username(raw_user):
        """'SNM\\philipe.fernandes' ou 'philipe.fernandes' → 'Philipe Fernandes'."""
        if not raw_user:
            return raw_user
        username = raw_user.split('\\')[-1] if '\\' in raw_user else raw_user
        parts = re.split(r'[._]', username)
        return ' '.join(p.capitalize() for p in parts if p)

    # ── Atualizar banco ──────────────────────────────────────────────────────
    def update_user_in_db(self, computer_name, formatted_user):
        try:
            rows = self.sql.execute(
                "SELECT Usuario_Atual FROM computers WHERE name = ?",
                (computer_name,)
            )
            if not rows:
                return False

            db_current = rows[0].get('Usuario_Atual')
            if db_current and db_current == formatted_user:
                return True

            self.sql.execute(
                "UPDATE computers SET Usuario_Atual = ?, Usuario_Anterior = ?, updated_at = GETDATE() WHERE name = ?",
                (formatted_user, db_current, computer_name),
                fetch=False
            )
            return True
        except Exception:
            logger.exception(f'Erro ao atualizar usuario para {computer_name}')
            return False

    # ── Processar uma máquina ────────────────────────────────────────────────
    def process_computer(self, computer):
        name = computer['name']
        t0 = time.time()
        raw_user, method, error = self.get_logged_user(name)
        elapsed = time.time() - t0

        if not raw_user:
            if error == 'OFFLINE':
                logger.info(f"  SKIP {name}: offline ({elapsed:.1f}s)")
            elif error == 'NO_USER_LOGGED':
                logger.info(f"  SKIP {name}: ninguem logado ({elapsed:.1f}s)")
            else:
                logger.warning(f"  FAIL {name}: {error} ({elapsed:.1f}s)")
            return {'computer': name, 'success': False, 'error': error, 'elapsed': elapsed}

        formatted = self.format_username(raw_user)
        saved = self.update_user_in_db(name, formatted)

        if saved:
            logger.info(f"  OK {name}: {raw_user} → {formatted} [{method}] ({elapsed:.1f}s)")
        else:
            logger.warning(f"  FAIL {name}: {raw_user} → DB save falhou ({elapsed:.1f}s)")

        return {
            'computer': name, 'success': saved,
            'raw_user': raw_user, 'formatted_user': formatted,
            'method': method, 'elapsed': elapsed
        }

    # ── Executar (sequencial) ────────────────────────────────────────────────
    def run(self, limit=50, prefix=None, specific=None):
        computers = self.get_computers(limit, prefix, specific)
        if not computers:
            logger.warning("Nenhuma maquina encontrada com os filtros informados")
            return

        total = len(computers)
        logger.info(f"Processando {total} maquinas...")
        t0 = time.time()

        ok = no_user = offline = errors = 0

        for i, computer in enumerate(computers, 1):
            logger.info(f"[{i}/{total}] {computer['name']}...")
            result = self.process_computer(computer)

            if result['success']:
                ok += 1
            elif result.get('error') == 'OFFLINE':
                offline += 1
            elif result.get('error') == 'NO_USER_LOGGED':
                no_user += 1
            elif result.get('error') and 'TIMEOUT' in str(result['error']):
                offline += 1
            else:
                errors += 1

        total_time = time.time() - t0
        logger.info("=" * 60)
        logger.info(f"RELATORIO — {total} maquinas em {total_time:.1f}s")
        logger.info(f"  Atualizados: {ok}  |  Sem usuario: {no_user}  |  Offline: {offline}  |  Erros: {errors}")
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Busca usuario logado em maquinas Windows e atualiza o banco'
    )
    parser.add_argument('-m', '--machine', help='Nome de uma maquina especifica')
    parser.add_argument('-p', '--prefix', help='Prefixo (ex: SHQ, DIA, ESM)')
    parser.add_argument('-l', '--limit', type=int, default=50, help='Limite (padrao: 50)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Debug logs')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        mgr = UserManager()
        mgr.run(limit=args.limit, prefix=args.prefix, specific=args.machine)
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuario")
    except Exception:
        logger.exception("Erro critico")
        sys.exit(1)


if __name__ == "__main__":
    main()
