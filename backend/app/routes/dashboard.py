from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import json

from app.models.dashboard import DashboardStats, OSDistribution
from app.config.database import DatabaseManager

# Setup
router = APIRouter()
logger = logging.getLogger(__name__)

# Instância do banco
db_manager = DatabaseManager()

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """
    Retorna estatísticas para o dashboard
    
    Esta rota replica exatamente o que seu frontend React espera:
    - totalComputers
    - recentLogins  
    - inactiveComputers
    - osDistribution
    """
    try:
        logger.info("📊 Buscando estatísticas do dashboard...")
        
        # Verificar se temos cache válido
        cached_stats = await get_cached_dashboard_stats()
        if cached_stats:
            logger.info("⚡ Retornando estatísticas do cache")
            return cached_stats
        
        # Buscar estatísticas do banco
        stats = await calculate_dashboard_stats()
        
        # Salvar no cache
        await save_dashboard_cache(stats)
        
        logger.info("✅ Estatísticas do dashboard calculadas com sucesso")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao carregar estatísticas: {str(e)}")

async def get_cached_dashboard_stats() -> DashboardStats | None:
    """Busca estatísticas do cache se ainda válidas"""
    try:
        query = """
            SELECT total_computers, recent_logins, inactive_computers, 
                   os_distribution, warranty_summary, last_updated
            FROM dashboard_stats 
            WHERE id = 1 AND last_updated > datetime('now', '-10 minutes')
        """
        
        results = db_manager.execute_query(query)
        
        if results:
            result = results[0]
            
            # Parse JSON strings
            os_dist = json.loads(result['os_distribution']) if result['os_distribution'] else []
            warranty_summary = json.loads(result['warranty_summary']) if result['warranty_summary'] else {}
            
            return DashboardStats(
                totalComputers=result['total_computers'],
                recentLogins=result['recent_logins'],
                inactiveComputers=result['inactive_computers'],
                osDistribution=[OSDistribution(**item) for item in os_dist],
                warrantyActive=warranty_summary.get('active', 0),
                warrantyExpired=warranty_summary.get('expired', 0),
                warrantyExpiring30=warranty_summary.get('expiring_30', 0),
                warrantyExpiring60=warranty_summary.get('expiring_60', 0),
                warrantyUnknown=warranty_summary.get('unknown', 0),
                lastUpdated=datetime.fromisoformat(result['last_updated']),
                dataSource="cache"
            )
            
    except Exception as e:
        logger.warning(f"⚠️ Erro ao buscar cache do dashboard: {e}")
        
    return None

async def calculate_dashboard_stats() -> DashboardStats:
    """Calcula estatísticas em tempo real"""
    try:
        # Query principal para estatísticas básicas
        main_query = """
            SELECT 
                COUNT(*) as total_computers,
                COUNT(CASE WHEN disabled = 0 THEN 1 END) as enabled_computers,
                COUNT(CASE WHEN disabled = 1 THEN 1 END) as disabled_computers,
                COUNT(CASE WHEN last_logon > datetime('now', '-7 days') THEN 1 END) as recent_logins,
                COUNT(CASE WHEN last_logon <= datetime('now', '-30 days') OR last_logon IS NULL THEN 1 END) as inactive_computers,
                COUNT(CASE WHEN last_logon IS NULL THEN 1 END) as never_logged_in
            FROM equipamentos
            WHERE name IS NOT NULL AND name != ''
        """
        
        main_results = db_manager.execute_query(main_query)
        main_stats = main_results[0] if main_results else {}
        
        # Query para distribuição de OS
        os_query = """
            SELECT os, COUNT(*) as count
            FROM equipamentos 
            WHERE os IS NOT NULL AND os != '' AND os != 'N/A'
            GROUP BY os
            ORDER BY count DESC
            LIMIT 10
        """
        
        os_results = db_manager.execute_query(os_query)
        os_distribution = [
            OSDistribution(name=row['os'], value=row['count'])
            for row in os_results
        ]
        
        # Query para estatísticas de garantia (se existirem)
        warranty_query = """
            SELECT 
                warranty_status,
                COUNT(*) as count
            FROM equipamentos
            WHERE warranty_status IS NOT NULL
            GROUP BY warranty_status
        """
        
        warranty_results = db_manager.execute_query(warranty_query)
        warranty_summary = {}
        
        for row in warranty_results:
            status = row['warranty_status'].lower() if row['warranty_status'] else 'unknown'
            warranty_summary[status] = row['count']
        
        # Montar resposta
        return DashboardStats(
            totalComputers=main_stats.get('total_computers', 0),
            recentLogins=main_stats.get('recent_logins', 0),
            inactiveComputers=main_stats.get('inactive_computers', 0),
            neverLoggedIn=main_stats.get('never_logged_in', 0),
            enabledComputers=main_stats.get('enabled_computers', 0),
            disabledComputers=main_stats.get('disabled_computers', 0),
            osDistribution=os_distribution,
            warrantyActive=warranty_summary.get('active', 0),
            warrantyExpired=warranty_summary.get('expired', 0),
            warrantyExpiring30=warranty_summary.get('expiring_30', 0),
            warrantyExpiring60=warranty_summary.get('expiring_60', 0),
            warrantyUnknown=warranty_summary.get('unknown', 0),
            dataSource="database",
            cacheExpires=datetime.now() + timedelta(minutes=10)
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao calcular estatísticas: {e}")
        raise

async def save_dashboard_cache(stats: DashboardStats):
    """Salva estatísticas no cache"""
    try:
        # Preparar dados para o cache
        os_dist_json = json.dumps([
            {"name": item.name, "value": item.value} 
            for item in stats.osDistribution
        ])
        
        warranty_summary_json = json.dumps({
            "active": stats.warrantyActive,
            "expired": stats.warrantyExpired,
            "expiring_30": stats.warrantyExpiring30,
            "expiring_60": stats.warrantyExpiring60,
            "unknown": stats.warrantyUnknown
        })
        
        # Salvar no banco (upsert)
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO dashboard_stats 
                (id, total_computers, recent_logins, inactive_computers, 
                 os_distribution, warranty_summary, last_updated)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            """, (
                stats.totalComputers,
                stats.recentLogins, 
                stats.inactiveComputers,
                os_dist_json,
                warranty_summary_json,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.info("💾 Cache do dashboard salvo com sucesso")
            
    except Exception as e:
        logger.warning(f"⚠️ Erro ao salvar cache do dashboard: {e}")

@router.get("/dashboard/refresh")
async def refresh_dashboard_cache():
    """
    Force refresh das estatísticas do dashboard
    """
    try:
        logger.info("🔄 Forçando atualização do cache do dashboard...")
        
        # Limpar cache existente
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dashboard_stats WHERE id = 1")
            conn.commit()
        
        # Recalcular estatísticas
        stats = await calculate_dashboard_stats()
        
        # Salvar novo cache
        await save_dashboard_cache(stats)
        
        return {
            "message": "Cache do dashboard atualizado com sucesso",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar cache: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar cache: {str(e)}")