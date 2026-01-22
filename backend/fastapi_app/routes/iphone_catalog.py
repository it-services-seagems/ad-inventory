"""
Rota para consultar catálogo de iPhones
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import json
from ..connections import require_sql_manager

router = APIRouter()

@router.get("/catalog")
def get_iphone_catalog():
    """Retorna todos os modelos do catálogo de iPhones"""
    sql_manager = require_sql_manager()
    
    try:
        query = """
        SELECT 
            id,
            model,
            generation,
            released_year,
            support_end_year,
            colors,
            storages_gb
        FROM dbo.iphone_catalog
        ORDER BY generation, model
        """
        
        result = sql_manager.execute_query(query)
        
        # Processar JSON strings para arrays
        catalog = []
        for row in result:
            try:
                colors = json.loads(row.get('colors', '[]')) if row.get('colors') else []
                storages = json.loads(row.get('storages_gb', '[]')) if row.get('storages_gb') else []
            except (json.JSONDecodeError, TypeError):
                colors = []
                storages = []
            
            catalog.append({
                'id': row.get('id'),
                'model': row.get('model', ''),
                'generation': row.get('generation'),
                'released_year': row.get('released_year'),
                'support_end_year': row.get('support_end_year'),
                'colors': colors,
                'storages_gb': storages
            })
        
        return {
            'success': True,
            'catalog': catalog,
            'total': len(catalog)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar catálogo: {str(e)}")


@router.get("/search")
def search_iphone_model(q: str = Query(..., description="Modelo a pesquisar")):
    """Busca modelo específico no catálogo com matching inteligente"""
    sql_manager = require_sql_manager()
    
    try:
        # Normalizar query de busca
        query_normalized = q.strip().lower()
        
        # Buscar todos os modelos para fazer matching
        query = """
        SELECT 
            model,
            generation,
            released_year,
            support_end_year,
            colors,
            storages_gb,
            (CASE 
                WHEN LOWER(model) = ? THEN 100
                WHEN LOWER(model) LIKE ? THEN 90
                WHEN LOWER(model) LIKE ? THEN 80
                WHEN LOWER(model) LIKE ? THEN 70
                ELSE 0 
            END) as score
        FROM dbo.iphone_catalog
        WHERE LOWER(model) LIKE ?
        ORDER BY score DESC, generation DESC
        """
        
        like_exact = f"%{query_normalized}%"
        like_start = f"{query_normalized}%"
        like_end = f"%{query_normalized}"
        
        result = sql_manager.execute_query(query, [
            query_normalized,  # exact match
            like_start,        # starts with
            like_end,          # ends with  
            like_exact,        # contains
            like_exact         # WHERE clause
        ])
        
        matches = []
        for row in result:
            if row.get('score', 0) > 0:
                try:
                    colors = json.loads(row.get('colors', '[]')) if row.get('colors') else []
                    storages = json.loads(row.get('storages_gb', '[]')) if row.get('storages_gb') else []
                except (json.JSONDecodeError, TypeError):
                    colors = []
                    storages = []
                
                matches.append({
                    'model': row.get('model', ''),
                    'generation': row.get('generation'),
                    'released_year': row.get('released_year'),
                    'support_end_year': row.get('support_end_year'),
                    'colors': colors,
                    'storages_gb': storages,
                    'score': row.get('score', 0)
                })
        
        return {
            'success': True,
            'query': q,
            'matches': matches,
            'total_matches': len(matches),
            'best_match': matches[0] if matches else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


@router.post("/suggest-match")
def suggest_model_match(model_text: str):
    """Sugere o melhor modelo baseado em texto livre"""
    sql_manager = require_sql_manager()
    
    try:
        # Lógica de matching inteligente
        text = model_text.strip().lower()
        
        # Remover caracteres especiais e espaços extras
        import re
        text_clean = re.sub(r'[^\w\s]', ' ', text)
        text_clean = ' '.join(text_clean.split())
        
        # Extrair números (geração, armazenamento)
        numbers = re.findall(r'\d+', text_clean)
        
        # Patterns comuns
        patterns = []
        
        # iPhone + número
        if 'iphone' in text:
            for num in numbers:
                if len(num) <= 2:  # Geração
                    patterns.append(f"iPhone {num}")
                    patterns.append(f"iPhone {num} Pro")
                    patterns.append(f"iPhone {num} Pro Max")
                    patterns.append(f"iPhone {num} Mini")
        
        # SE variations
        if any(x in text for x in ['se', 's.e', 's e']):
            patterns.extend([
                "iPhone SE (1ª geração)",
                "iPhone SE (2ª geração)", 
                "iPhone SE (3ª geração)"
            ])
        
        # XR, XS variations
        if any(x in text for x in ['xr', 'x r']):
            patterns.append("iPhone XR")
        if any(x in text for x in ['xs', 'x s']):
            patterns.append("iPhone XS")
            patterns.append("iPhone XS Max")
        if text.count('x') == 1 and 'xs' not in text and 'xr' not in text:
            patterns.append("iPhone X")
        
        if not patterns:
            # Fallback: buscar por similaridade geral
            patterns = [text_clean]
        
        # Buscar os padrões no banco
        suggestions = []
        
        for pattern in patterns:
            query = """
            SELECT TOP 3
                model,
                generation,
                released_year,
                colors,
                storages_gb,
                (CASE 
                    WHEN LOWER(model) = LOWER(?) THEN 100
                    WHEN LOWER(model) LIKE LOWER(?) THEN 85
                    ELSE 0
                END) as score
            FROM dbo.iphone_catalog
            WHERE LOWER(model) LIKE LOWER(?)
            AND (CASE 
                WHEN LOWER(model) = LOWER(?) THEN 100
                WHEN LOWER(model) LIKE LOWER(?) THEN 85
                ELSE 0
            END) > 0
            ORDER BY score DESC, generation DESC
            """
            
            like_pattern = f"%{pattern}%"
            
            result = sql_manager.execute_query(query, [
                pattern,       # exact match check
                like_pattern,  # like match check  
                like_pattern,  # WHERE clause
                pattern,       # score exact
                like_pattern   # score like
            ])
            
            for row in result:
                if row not in suggestions:
                    try:
                        colors = json.loads(row.get('colors', '[]')) if row.get('colors') else []
                        storages = json.loads(row.get('storages_gb', '[]')) if row.get('storages_gb') else []
                    except (json.JSONDecodeError, TypeError):
                        colors = []
                        storages = []
                    
                    suggestions.append({
                        'model': row.get('model', ''),
                        'generation': row.get('generation'),
                        'released_year': row.get('released_year'),
                        'colors': colors,
                        'storages_gb': storages,
                        'score': row.get('score', 0),
                        'matched_pattern': pattern
                    })
        
        # Ordenar por score e remover duplicatas
        unique_suggestions = {}
        for suggestion in suggestions:
            model = suggestion['model']
            if model not in unique_suggestions or suggestion['score'] > unique_suggestions[model]['score']:
                unique_suggestions[model] = suggestion
        
        final_suggestions = sorted(unique_suggestions.values(), key=lambda x: x['score'], reverse=True)
        
        return {
            'success': True,
            'original_text': model_text,
            'suggestions': final_suggestions[:5],  # Top 5
            'best_match': final_suggestions[0] if final_suggestions else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na sugestão: {str(e)}")