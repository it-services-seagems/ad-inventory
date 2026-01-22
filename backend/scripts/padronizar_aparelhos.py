#!/usr/bin/env python3
"""
Script para padronizar nomes dos aparelhos no banco de dados
e definir marca Apple para iPhones
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi_app.managers.sql import sql_manager

def padronizar_aparelhos():
    """Padronizar nomes dos aparelhos e marcas"""
    try:
        conn = sql_manager.get_connection()
        cursor = conn.cursor()
        
        print("=== VERIFICANDO DADOS ATUAIS ===")
        
        # Verificar modelos únicos
        print("\n--- MODELOS ÚNICOS ---")
        cursor.execute("""
            SELECT DISTINCT model, COUNT(*) as count 
            FROM dbo.mobiles 
            WHERE model IS NOT NULL AND model != ''
            GROUP BY model 
            ORDER BY model
        """)
        modelos = cursor.fetchall()
        for row in modelos:
            print(f"'{row[0]}' ({row[1]} aparelhos)")
        
        # Verificar marcas únicas
        print("\n--- MARCAS ÚNICAS ---")
        cursor.execute("""
            SELECT DISTINCT brand, COUNT(*) as count 
            FROM dbo.mobiles 
            WHERE brand IS NOT NULL AND brand != ''
            GROUP BY brand 
            ORDER BY brand
        """)
        marcas = cursor.fetchall()
        for row in marcas:
            print(f"'{row[0]}' ({row[1]} aparelhos)")
        
        # Verificar aparelhos com iPhone no modelo
        print("\n--- APARELHOS COM IPHONE NO MODELO ---")
        cursor.execute("""
            SELECT id, model, brand 
            FROM dbo.mobiles 
            WHERE LOWER(model) LIKE '%iphone%'
            ORDER BY model
        """)
        iphones = cursor.fetchall()
        for row in iphones:
            print(f"ID: {row[0]}, Modelo: '{row[1]}', Marca: '{row[2]}'")
        
        print(f"\n=== INICIANDO PADRONIZAÇÃO ===")
        
        # 1. Padronizar modelos - converter para Title Case e remover espaços extras
        print("\n1. Padronizando modelos...")
        cursor.execute("""
            UPDATE dbo.mobiles 
            SET model = LTRIM(RTRIM(
                REPLACE(
                    REPLACE(
                        REPLACE(model, '  ', ' '), -- remover espaços duplos
                        '   ', ' '  -- remover espaços triplos
                    ), 
                    '    ', ' '  -- remover espaços quádruplos
                )
            ))
            WHERE model IS NOT NULL AND model != ''
        """)
        linhas_modelo = cursor.rowcount
        print(f"✓ {linhas_modelo} modelos padronizados (espaços removidos)")
        
        # 1.1. Normalizar case dos modelos - converter tudo para formato consistente
        print("\n1.1. Normalizando case dos modelos...")
        
        # Primeiro, buscar todos os modelos únicos para normalizar
        cursor.execute("SELECT DISTINCT model FROM dbo.mobiles WHERE model IS NOT NULL AND model != ''")
        modelos_atuais = [row[0] for row in cursor.fetchall()]
        
        modelos_normalizados = 0
        for modelo_original in modelos_atuais:
            # Converter para title case básico
            modelo_normalizado = modelo_original.title()
            
            # Correções específicas para manter consistência em termos técnicos
            correções_especificas = {
                'Iphone': 'iPhone',
                'Ipad': 'iPad', 
                'Ipod': 'iPod',
                'Pro Max': 'Pro Max',
                'Se': 'SE',
                'Plus': 'Plus',
                'Mini': 'Mini',
                'Air': 'Air',
                'Pro': 'Pro',
                'Max': 'Max',
                'Ultra': 'Ultra',
                'Gb': 'GB',
                'Tb': 'TB',
                'Mb': 'MB',
                # Samsung
                'Galaxy': 'Galaxy',
                'Note': 'Note',
                # Xiaomi
                'Redmi': 'Redmi',
                'Poco': 'POCO',
                # Motorola
                'Moto': 'Moto',
                # Huawei
                'Mate': 'Mate',
                # LG
                'Lg': 'LG',
                # Sony
                'Xperia': 'Xperia'
            }
            
            # Aplicar correções específicas
            for incorreto, correto in correções_especificas.items():
                modelo_normalizado = modelo_normalizado.replace(incorreto, correto)
            
            # Só atualizar se houver diferença
            if modelo_original != modelo_normalizado:
                cursor.execute("""
                    UPDATE dbo.mobiles 
                    SET model = ?
                    WHERE model = ?
                """, (modelo_normalizado, modelo_original))
                
                if cursor.rowcount > 0:
                    print(f"  ✓ '{modelo_original}' → '{modelo_normalizado}' ({cursor.rowcount} aparelhos)")
                    modelos_normalizados += cursor.rowcount
        
        print(f"✓ {modelos_normalizados} aparelhos tiveram o case do modelo normalizado")
        
        # 2. Padronizar marcas - converter para Title Case e remover espaços extras  
        print("\n2. Padronizando marcas...")
        cursor.execute("""
            UPDATE dbo.mobiles 
            SET brand = LTRIM(RTRIM(
                REPLACE(
                    REPLACE(
                        REPLACE(brand, '  ', ' '), -- remover espaços duplos
                        '   ', ' '  -- remover espaços triplos
                    ), 
                    '    ', ' '  -- remover espaços quádruplos
                )
            ))
            WHERE brand IS NOT NULL AND brand != ''
        """)
        linhas_marca = cursor.rowcount
        print(f"✓ {linhas_marca} marcas padronizadas (espaços removidos)")
        
        # 3. Definir marca Apple para todos os iPhones
        print("\n3. Definindo marca Apple para iPhones...")
        cursor.execute("""
            UPDATE dbo.mobiles 
            SET brand = 'Apple'
            WHERE LOWER(model) LIKE '%iphone%'
        """)
        linhas_apple = cursor.rowcount
        print(f"✓ {linhas_apple} aparelhos iPhone tiveram a marca definida como 'Apple'")
        
        # 4. Padronização específica de modelos comuns
        print("\n4. Padronizações específicas...")
        
        # iPhone variations
        padronizacoes = [
            ("iPhone SE", ["iphone se", "IPHONE SE", "Iphone SE", "iPhone se", "iPhoneSE"]),
            ("iPhone 12", ["iphone 12", "IPHONE 12", "Iphone 12", "iPhone12"]),
            ("iPhone 13", ["iphone 13", "IPHONE 13", "Iphone 13", "iPhone13"]),
            ("iPhone 14", ["iphone 14", "IPHONE 14", "Iphone 14", "iPhone14"]),
            ("iPhone 15", ["iphone 15", "IPHONE 15", "Iphone 15", "iPhone15"]),
            # Samsung variations
            ("Galaxy S21", ["galaxy s21", "GALAXY S21", "Galaxy s21", "GalaxyS21", "samsung galaxy s21"]),
            ("Galaxy S22", ["galaxy s22", "GALAXY S22", "Galaxy s22", "GalaxyS22", "samsung galaxy s22"]),
            ("Galaxy S23", ["galaxy s23", "GALAXY S23", "Galaxy s23", "GalaxyS23", "samsung galaxy s23"]),
            ("Galaxy A54", ["galaxy a54", "GALAXY A54", "Galaxy a54", "GalaxyA54", "samsung galaxy a54"]),
        ]
        
        total_padronizados = 0
        for modelo_padrao, variacoes in padronizacoes:
            for variacao in variacoes:
                cursor.execute("""
                    UPDATE dbo.mobiles 
                    SET model = ?
                    WHERE model = ?
                """, (modelo_padrao, variacao))
                if cursor.rowcount > 0:
                    print(f"  ✓ '{variacao}' → '{modelo_padrao}' ({cursor.rowcount} aparelhos)")
                    total_padronizados += cursor.rowcount
        
        print(f"✓ {total_padronizados} aparelhos tiveram modelos padronizados")
        
        # 5. Definir marcas para modelos conhecidos
        print("\n5. Definindo marcas para modelos conhecidos...")
        marcas_por_modelo = [
            ("Samsung", ["Galaxy%", "galaxy%", "GALAXY%"]),
            ("Xiaomi", ["Redmi%", "Mi %", "POCO%", "redmi%", "mi %", "poco%"]),
            ("Motorola", ["Moto%", "moto%", "MOTO%"]),
            ("Huawei", ["P30%", "P40%", "Mate%", "p30%", "p40%", "mate%"]),
            ("LG", ["LG %", "lg %"]),
            ("Sony", ["Xperia%", "xperia%", "XPERIA%"]),
        ]
        
        total_marcas_definidas = 0
        for marca, padroes in marcas_por_modelo:
            for padrao in padroes:
                cursor.execute("""
                    UPDATE dbo.mobiles 
                    SET brand = ?
                    WHERE LOWER(model) LIKE LOWER(?) 
                    AND (brand IS NULL OR brand = '' OR LTRIM(RTRIM(brand)) = '')
                """, (marca, padrao))
                if cursor.rowcount > 0:
                    print(f"  ✓ Marca '{marca}' definida para modelos com padrão '{padrao}' ({cursor.rowcount} aparelhos)")
                    total_marcas_definidas += cursor.rowcount
        
        print(f"✓ {total_marcas_definidas} aparelhos tiveram marcas definidas")
        
        # Confirmar mudanças
        conn.commit()
        
        print("\n=== VERIFICANDO RESULTADO ===")
        
        # Mostrar modelos únicos após padronização
        print("\n--- MODELOS ÚNICOS APÓS PADRONIZAÇÃO ---")
        cursor.execute("""
            SELECT DISTINCT model, COUNT(*) as count 
            FROM dbo.mobiles 
            WHERE model IS NOT NULL AND model != ''
            GROUP BY model 
            ORDER BY model
        """)
        for row in cursor.fetchall():
            print(f"'{row[0]}' ({row[1]} aparelhos)")
        
        # Mostrar marcas únicas após padronização
        print("\n--- MARCAS ÚNICAS APÓS PADRONIZAÇÃO ---")
        cursor.execute("""
            SELECT DISTINCT brand, COUNT(*) as count 
            FROM dbo.mobiles 
            WHERE brand IS NOT NULL AND brand != ''
            GROUP BY brand 
            ORDER BY brand
        """)
        for row in cursor.fetchall():
            print(f"'{row[0]}' ({row[1]} aparelhos)")
        
        print(f"\n✅ PADRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"   • Modelos padronizados: {linhas_modelo}")
        print(f"   • Modelos com case normalizado: {modelos_normalizados}")
        print(f"   • Marcas padronizadas: {linhas_marca}")
        print(f"   • iPhones com marca Apple: {linhas_apple}")
        print(f"   • Modelos específicos padronizados: {total_padronizados}")
        print(f"   • Marcas definidas automaticamente: {total_marcas_definidas}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro durante padronização: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    padronizar_aparelhos()