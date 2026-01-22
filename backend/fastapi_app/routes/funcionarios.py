from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import re
from ..managers.corpore_db import DatabaseConfig
from ..managers import sql_manager

logger = logging.getLogger(__name__)

funcionarios_router = APIRouter()


def extrair_nome_completo_email(email_corporativo: str) -> tuple:
    """
    Extrai e formata o nome completo do email corporativo.
    Ex: ricardo.bicudo@seagems.com.br -> "Ricardo Bicudo"
    
    Returns:
        tuple: (nome_formatado, erro_msg) onde erro_msg é None se sucesso
    """
    if not email_corporativo:
        return None, "Usuário sem email corporativo fornecido"
    
    email_lower = email_corporativo.lower().strip()
    
    # Verificar se tem domínios válidos
    dominios_validos = ['@seagems.com.br', '@sapura.com', '@seagems', '@sapura']
    dominio_encontrado = False
    
    for dominio in dominios_validos:
        if dominio in email_lower:
            dominio_encontrado = True
            break
    
    if not dominio_encontrado:
        return None, "Email deve ser do domínio @seagems ou @sapura"
    
    # Extrair a parte do usuário (antes do @)
    if '@' not in email_lower:
        return None, "Email inválido"
    
    usuario_parte = email_lower.split('@')[0]
    
    if not usuario_parte:
        return None, "Nome de usuário não encontrado no email"
    
    # Converter pontos em espaços e capitalizar cada palavra
    # Ex: ricardo.bicudo -> Ricardo Bicudo
    nome_formatado = usuario_parte.replace('.', ' ').title()
    
    return nome_formatado, None


@funcionarios_router.get('/')
async def listar_funcionarios(
    unidade: Optional[str] = None, 
    search: Optional[str] = None, 
    limit: Optional[int] = Query(None, ge=1), 
    include_demitidos: Optional[int] = Query(0, ge=0, le=1)
):
    """Lista funcionários atuais no sistema CorporeRM usando pyodbc.

    Exclui funcionários cuja situação atual seja 'Demitido'.
    Parâmetros opcionais: unidade (filtro por cidade), search (pesquisa em chapa/nome), limit (limita resultados).
    """
    try:
        # abrir conexão pyodbc para CorporeRM
        conn = DatabaseConfig.get_pyodbc_connection('corporerm')
        cursor = conn.cursor()

        base_query = '''
            SELECT
                CHAPA as matricula,
                NOME as nome,
                DTNASCIMENTO as data_nascimento,
                CPF as cpf,
                CIDADE as unidade,
                FUNCAO as cargo,
                TELEFONE1 as telefone,
                EMAILPESSOAL as email,
                EMAIL_CORPORATIVO as email_corporativo,
                UPPER(ISNULL(SITUACAO_ATUAL_DESCRICAO, '')) as situacao_atual,
                ISNULL(SECAO_ATUAL_DECRICAO, '') as secao_atual_descricao
            FROM [dbo].[VW_FUNCIONARIOS]
        '''

        where_clauses = []
        params = []

        if unidade and unidade.lower() != 'todas':
            where_clauses.append('CIDADE LIKE ?')
            params.append(f'%{unidade}%')

        if search:
            where_clauses.append('(CHAPA LIKE ? OR NOME LIKE ?)')
            params.extend([f'%{search}%', f'%{search}%'])

        # If include_demitidos is not set, exclude demitidos by adding a WHERE clause
        if not include_demitidos:
            where_clauses.append("UPPER(ISNULL(SITUACAO_ATUAL_DESCRICAO, '')) <> 'DEMITIDO'")

        if where_clauses:
            base_query += ' WHERE ' + ' AND '.join(where_clauses)

        # Apply TOP N if limit provided and no search
        final_query = base_query
        if limit and not search:
            final_query = f"SELECT TOP {int(limit)} * FROM ({base_query}) AS subquery"

        logger.debug('Executando query CorporeRM: %s params=%s', final_query, params)
        cursor.execute(final_query, tuple(params) if params else ())

        columns = [col[0] for col in cursor.description]
        results = []
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            # normalize date to YYYY-MM-DD if present
            dt = row_dict.get('data_nascimento')
            if dt is not None:
                try:
                    row_dict['data_nascimento'] = dt.strftime('%Y-%m-%d')
                except Exception:
                    # keep as-is
                    pass
            # include demitido boolean so frontend can mark and block actions
            situacao = (row_dict.get('situacao_atual') or '').upper()
            demitido_flag = True if situacao == 'DEMITIDO' else False
            results.append({
                'matricula': row_dict.get('matricula'),
                'nome': row_dict.get('nome'),
                'data_nascimento': row_dict.get('data_nascimento'),
                'cpf': row_dict.get('cpf'),
                'unidade': row_dict.get('unidade'),
                'cargo': row_dict.get('cargo'),
                'telefone': row_dict.get('telefone'),
                'email': row_dict.get('email'),
                'email_corporativo': row_dict.get('email_corporativo'),
                'demitido': demitido_flag,
                'secao_atual_descricao': row_dict.get('secao_atual_descricao') or ''
            })

        conn.close()
        return JSONResponse({'success': True, 'funcionarios': results, 'count': len(results)})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Erro ao listar funcionários no CorporeRM')
        raise HTTPException(status_code=500, detail=str(e))


@funcionarios_router.post('/vincular-usuario')
async def vincular_usuario_computador(payload: dict):
    """
    Vincula um funcionário a um computador.
    Payload esperado: {
        "computer_name": "NOME_COMPUTADOR", 
        "matricula": "123456",
        "nome": "Nome do Funcionário",
        "email_corporativo": "usuario@seagems.com.br"
    }
    """
    try:
        computer_name = payload.get('computer_name')
        matricula = payload.get('matricula')
        nome = payload.get('nome')
        email_corporativo = payload.get('email_corporativo')
        
        if not all([computer_name, matricula, email_corporativo]):
            raise HTTPException(status_code=400, detail="computer_name, matricula e email_corporativo são obrigatórios")
        
        # Extrair e formatar nome completo do email
        nome_formatado, erro_msg = extrair_nome_completo_email(email_corporativo)
        if erro_msg:
            raise HTTPException(status_code=400, detail=erro_msg)
        
        logger.info(f"Vinculando usuário {nome_formatado} (matricula: {matricula}) ao computador {computer_name}")
        
        # Verificar se o computador existe
        computer_query = "SELECT id, Usuario_Atual, Usuario_Anterior FROM computers WHERE name = ?"
        computer_result = sql_manager.execute_query(computer_query, params=(computer_name,))
        
        if not computer_result:
            raise HTTPException(status_code=404, detail=f"Computador {computer_name} não encontrado")
        
        computer = computer_result[0]
        usuario_atual_anterior = computer.get('Usuario_Atual')
        
        # Verificar se é computador SHQ para atualizar status para "Em uso"
        is_shq_computer = computer_name.upper().startswith('SHQ')
        
        # Atualizar o computador com o novo usuário e status
        if is_shq_computer:
            update_query = """
                UPDATE computers 
                SET Usuario_Atual = ?, 
                    Usuario_Anterior = ?,
                    Status = 'Em uso',
                    updated_at = GETDATE()
                WHERE name = ?
            """
        else:
            update_query = """
                UPDATE computers 
                SET Usuario_Atual = ?, 
                    Usuario_Anterior = ?,
                    updated_at = GETDATE()
                WHERE name = ?
            """
        
        # Se já havia um usuário atual, ele vai para anterior
        novo_usuario_anterior = usuario_atual_anterior if usuario_atual_anterior else computer.get('Usuario_Anterior')
        
        sql_manager.execute_query(
            update_query, 
            params=(nome_formatado, novo_usuario_anterior, computer_name),
            fetch=False
        )
        
        logger.info(f"Usuário vinculado com sucesso: {nome_formatado} -> {computer_name}")
        
        return JSONResponse({
            'success': True, 
            'message': f'Usuário {nome} vinculado ao computador {computer_name}',
            'data': {
                'computer_name': computer_name,
                'usuario_atual': nome_formatado,
                'usuario_anterior': novo_usuario_anterior,
                'status_atualizado': 'Em uso' if is_shq_computer else None,
                'funcionario': {
                    'matricula': matricula,
                    'nome': nome,
                    'email_corporativo': email_corporativo
                }
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Erro ao vincular usuário ao computador')
        raise HTTPException(status_code=500, detail=str(e))


@funcionarios_router.post('/desvincular-usuario')
async def desvincular_usuario_computador(payload: dict):
    """
    Desvincula o usuário atual de um computador.
    Payload esperado: {"computer_name": "NOME_COMPUTADOR"}
    """
    try:
        computer_name = payload.get('computer_name')
        
        if not computer_name:
            raise HTTPException(status_code=400, detail="computer_name é obrigatório")
        
        logger.info(f"Desvinculando usuário do computador {computer_name}")
        
        # Verificar se o computador existe
        computer_query = "SELECT id, Usuario_Atual, Usuario_Anterior FROM computers WHERE name = ?"
        computer_result = sql_manager.execute_query(computer_query, params=(computer_name,))
        
        if not computer_result:
            raise HTTPException(status_code=404, detail=f"Computador {computer_name} não encontrado")
        
        computer = computer_result[0]
        usuario_atual = computer.get('Usuario_Atual')
        
        if not usuario_atual:
            raise HTTPException(status_code=400, detail=f"Computador {computer_name} não possui usuário vinculado")
        
        # Verificar se é computador SHQ para atualizar status para "spare"
        is_shq_computer = computer_name.upper().startswith('SHQ')
        
        # Mover usuário atual para anterior e limpar atual, atualizar status se for SHQ
        if is_shq_computer:
            update_query = """
                UPDATE computers 
                SET Usuario_Atual = NULL,
                    Usuario_Anterior = ?,
                    Status = 'spare',
                    updated_at = GETDATE()
                WHERE name = ?
            """
        else:
            update_query = """
                UPDATE computers 
                SET Usuario_Atual = NULL,
                    Usuario_Anterior = ?,
                    updated_at = GETDATE()
                WHERE name = ?
            """
        
        sql_manager.execute_query(update_query, params=(usuario_atual, computer_name), fetch=False)
        
        logger.info(f"Usuário {usuario_atual} desvinculado do computador {computer_name}")
        
        return JSONResponse({
            'success': True, 
            'message': f'Usuário {usuario_atual} desvinculado do computador {computer_name}',
            'data': {
                'computer_name': computer_name,
                'usuario_desvinculado': usuario_atual,
                'usuario_anterior': usuario_atual,  # O usuário desvinculado agora é o anterior
                'usuario_anterior_original': computer.get('Usuario_Anterior'),  # O que estava como anterior antes
                'status_atualizado': 'spare' if is_shq_computer else None
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Erro ao desvincular usuário do computador')
        raise HTTPException(status_code=500, detail=str(e))