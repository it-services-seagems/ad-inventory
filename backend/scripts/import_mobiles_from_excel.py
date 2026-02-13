#!/usr/bin/env python3
"""Importador simples de Excel -> dbo.mobiles

Comportamento simplificado:
- Lê a planilha (sheet opcional)
- Normaliza nomes de colunas (minusculas, espaços -> _)
- Faz correspondência case-insensitive/underscore-normalizada com as colunas da tabela `mobiles`
- Insere todas as linhas correspondentes (dry-run por padrão; use --commit para aplicar)
"""

import argparse
import sys
from pathlib import Path
import os

# Ensure repository root is on sys.path so `from backend.fastapi_app...` works
# When this script is run from backend/scripts, repo_root should be two levels up.
try:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
except Exception:
    pass


def normalize(name: str) -> str:
    return ''.join(ch.lower() if ch.isalnum() else '_' for ch in (name or '').strip())


def ensure_pandas():
    try:
        import pandas as pd  # noqa: F401
    except Exception:
        print('Pandas (and openpyxl) are required. Install with: pip install pandas openpyxl')
        sys.exit(1)


def main():
    ensure_pandas()
    import pandas as pd

    parser = argparse.ArgumentParser(description='Importa planilha Excel para dbo.mobiles (simpel)')
    parser.add_argument('excel', help='Caminho para o arquivo .xlsx/.xls')
    parser.add_argument('--sheet', default=0, help='Nome ou índice da sheet (default: 0)')
    parser.add_argument('--commit', action='store_true', help='Aplicar alterações no banco (por padrão é dry-run)')
    parser.add_argument('--fill-missing-model', default=None, help='Valor para preencher quando `model` estiver ausente (opcional)')
    parser.add_argument('--fail-on-missing', action='store_true', help='Falhar se encontrar linhas com colunas NOT NULL faltando (por padrão pula essas linhas)')
    args = parser.parse_args()

    excel_path = Path(args.excel)
    if not excel_path.exists():
        print('Arquivo não encontrado:', excel_path)
        sys.exit(1)

    try:
        df = pd.read_excel(excel_path, sheet_name=args.sheet, engine='openpyxl')
    except Exception as e:
        print('Erro ao ler Excel:', e)
        sys.exit(1)

    # Normalize dataframe column names and build map orig -> normalized
    df_cols = list(df.columns)
    df_norm_map = {c: normalize(c) for c in df_cols}

    # Import sql_manager
    try:
        from backend.fastapi_app.managers.sql import sql_manager
    except Exception as e:
        print('Erro ao importar sql_manager. Execute o script a partir da raiz do repositório e com o ambiente correto.')
        print('Detalhe:', e)
        sys.exit(1)

    # Inspect target table columns
    conn = sql_manager.get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT TOP 0 * FROM dbo.mobiles')
        table_cols = [c[0] for c in cur.description] if cur.description else []
    except Exception as e:
        print('Erro ao inspecionar dbo.mobiles:', e)
        conn.close()
        sys.exit(1)

    table_norm_map = {normalize(c): c for c in table_cols}
    print('Colunas na tabela mobiles:', table_cols)

    # Detect NOT NULL columns (except identity PK id)
    try:
        cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='mobiles' AND IS_NULLABLE='NO'")
        not_null_cols = [r[0] for r in cur.fetchall()]
    except Exception:
        not_null_cols = []
    not_null_cols = [c for c in not_null_cols if c.lower() != 'id']
    if not_null_cols:
        print('Colunas NOT NULL na tabela (serão verificadas):', not_null_cols)

    # Match dataframe columns to table columns using normalized names
    matched = {}
    used_table_cols = set()

    # synonyms to map common Portuguese headings to english column names
    synonyms = {
        'modelo': 'model',
        'modelo_atual': 'model',
        'imei': 'imei',
        'imei_atual': 'imei',
        'marca': 'brand',
        'departamento': 'departamento',
        'tipo': 'tipo',
        'numero': 'number',
        'número': 'number',  # com acento
        'numero_aparelho': 'number',
        'número_aparelho': 'number',
        'numero_telefone': 'number',
        'número_telefone': 'number',
        'telefone': 'number',
        'number': 'number',
        'eid': 'eid'
    }

    # map common employee/user headings
    employee_synonyms = {
        'usuario': 'funcionario_nome',
        'usuário': 'funcionario_nome',
        'usuario_atual': 'funcionario_nome',
        'funcionario': 'funcionario_nome',
        'funcionário': 'funcionario_nome',
        'nome': 'funcionario_nome',
        'matricula': 'funcionario_matricula',
        'chapa': 'funcionario_matricula'
    }
    # merge into synonyms for matching
    synonyms.update(employee_synonyms)

    # first pass: exact normalized match
    for orig_col, norm in df_norm_map.items():
        if norm in table_norm_map and table_norm_map[norm] not in used_table_cols:
            matched[orig_col] = table_norm_map[norm]
            used_table_cols.add(table_norm_map[norm])

    # second pass: synonyms (normalized excel contains synonym key)
    for orig_col, norm in df_norm_map.items():
        if orig_col in matched:
            continue
        for syn_key, target in synonyms.items():
            if syn_key in norm and target in table_cols and target not in used_table_cols:
                matched[orig_col] = target
                used_table_cols.add(target)
                break

    # third pass: substring matching (excel_norm contains table_norm or vice-versa)
    for orig_col, norm in df_norm_map.items():
        if orig_col in matched:
            continue
        for tnorm, tcol in table_norm_map.items():
            if tcol in used_table_cols:
                continue
            if tnorm in norm or norm in tnorm:
                matched[orig_col] = tcol
                used_table_cols.add(tcol)
                break

    if not matched:
        print('Nenhuma coluna do Excel corresponde às colunas da tabela. Colunas Excel:', df_cols)
        conn.close()
        return

    print('Mapeamento encontrado (Excel -> tabela):')
    for k, v in matched.items():
        print(f'  {k} -> {v}')

    # Attempt to build a lookup of funcionarios (nome -> matricula) by calling local API
    def fetch_funcionarios_lookup():
        try:
            import requests
            import os
        except Exception:
            return {}
        # Endpoints to try (env var wins)
        bases = []
        env_base = os.environ.get('IMPORTER_API_BASE')
        if env_base:
            bases.append(env_base.rstrip('/'))
        bases.extend([
            'http://127.0.0.1:42057',
            'http://localhost:42057',
            'http://10.15.3.30:42057'
        ])

        for base in bases:
            try:
                resp = requests.get(f"{base}/api/funcionarios/", params={'limit': 10000}, timeout=5)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                items = data.get('funcionarios') if isinstance(data, dict) else []
                lookup = {}
                for f in items:
                    nome = (f.get('nome') or '').strip()
                    matricula = f.get('matricula')
                    if nome:
                        lookup[normalize(nome)] = matricula
                if lookup:
                    return lookup
            except Exception:
                continue
        return {}

    funcionarios_lookup = fetch_funcionarios_lookup()

    # Prepare rows
    inserts = []
    skipped = 0
    skipped_examples = []
    for row_idx, row in df.iterrows():
        rec = {}
        for excel_col, table_col in matched.items():
            val = row.get(excel_col)
            if pd.isna(val):
                val = None
            rec[table_col] = val

        # Normalize/clean funcionario_nome (remove trailing ' - ...') and attempt matricula lookup
        if 'funcionario_nome' in rec and rec.get('funcionario_nome') is not None:
            try:
                fn = str(rec['funcionario_nome']).strip()
                # remove suffix like ' - Guarita Rio das Ostras'
                fn_clean = fn.split(' - ')[0].strip()
                rec['funcionario_nome'] = fn
                if (not rec.get('funcionario_matricula')) and funcionarios_lookup:
                    matric = funcionarios_lookup.get(normalize(fn_clean))
                    if matric:
                        rec['funcionario_matricula'] = matric
            except Exception:
                pass
        # If user asked to fill missing model, do it before validation
        if args.fill_missing_model is not None and 'model' in rec and (rec.get('model') is None):
            rec['model'] = args.fill_missing_model

        # Validate NOT NULL columns
        missing_required = [c for c in not_null_cols if rec.get(c) is None]
        if missing_required:
            skipped += 1
            if len(skipped_examples) < 5:
                skipped_examples.append({'row': int(row_idx), 'missing': missing_required, 'values': {k: rec.get(k) for k in missing_required}})
            if args.fail_on_missing:
                print(f"Linha {row_idx} faltando colunas obrigatórias: {missing_required}. Abortando por --fail-on-missing")
                conn.close()
                sys.exit(1)
            # otherwise skip the row
            continue

        inserts.append(rec)

    print(f'Linhas carregadas do Excel: {len(inserts)}')
    if len(inserts) == 0:
        conn.close()
        return

    preview_n = min(5, len(inserts))
    print('Preview:')
    for r in inserts[:preview_n]:
        print(r)

    print(f'Linhas a inserir após validação: {len(inserts)} (puladas: {skipped})')
    if skipped_examples:
        print('Exemplos de linhas puladas:')
        for ex in skipped_examples:
            print(ex)

    if not args.commit:
        print('\nDry-run. Rode com --commit para aplicar as inserções.')
        conn.close()
        return

    try:
        inserted = 0
        for rec in inserts:
            cols = ', '.join(rec.keys())
            placeholders = ', '.join(['?'] * len(rec))
            q = f'INSERT INTO dbo.mobiles ({cols}) VALUES ({placeholders})'
            params = tuple(rec.values())
            cur.execute(q, params)
            inserted += 1
        conn.commit()
        print(f'Inserção concluída: {inserted} linhas inseridas.')
    except Exception as e:
        conn.rollback()
        print('Erro durante inserção:', e)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
