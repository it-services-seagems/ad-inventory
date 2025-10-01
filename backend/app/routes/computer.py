
import logging

logger = logging.getLogger(__name__)


@app.route('/api/computers', methods=['GET'])
def get_computers():
    
    # diagnostic storage for better error mapping
    diagnostic = {'ldap_error': None, 'ps_error': None}

    try:
        use_sql = request.args.get('source', 'sql').lower() == 'sql'
        
        if use_sql:
            computers = sql_manager.get_computers_from_sql()
            return jsonify(computers)
        else:
            computers = ad_manager.get_computers()
            return jsonify(computers)
            
    except Exception as e:
        
        try:
            
            computers = ad_manager.get_computers()
            return jsonify(computers)
        except Exception as ad_error:
            
            return jsonify({'error': 'Erro interno do servidor', 'details': str(e)}), 500

@app.route('/api/computers/sync', methods=['POST'])
def sync_computers():
    
    try:
        sync_service.sync_ad_to_sql()
        return jsonify({
            'status': 'success',
            'message': 'Sincronização concluída',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/computers/<computer_name>/warranty', methods=['GET'])
def get_computer_warranty(computer_name):

    try:
        warranty_info = dell_api.get_warranty_info(computer_name)
        
        if warranty_info and 'error' not in warranty_info:
            frontend_response = {
                'serviceTag': warranty_info.get('serviceTag', computer_name),
                'productLineDescription': warranty_info.get('modelo', 'N/A'),
                'systemDescription': warranty_info.get('modelo', 'N/A'),
                'warrantyEndDate': warranty_info.get('dataExpiracao', 'N/A'),
                'warrantyStatus': 'Active' if warranty_info.get('status') == 'Em garantia' else 'Expired',
                'entitlements': warranty_info.get('entitlements', []),
                'dataSource': warranty_info.get('dataSource', 'unknown')
            }
            return jsonify(frontend_response)
        else:
            return jsonify({'error': 'Warranty information not found'}), 404
            
    except Exception as e:
        
        return jsonify({'error': 'Warranty information not found'}), 500
@app.route('/api/computers/<computer_name>/toggle-status', methods=['POST', 'OPTIONS'])
def toggle_computer_status(computer_name):

    # OPTIONS / CORS preflight support
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK', 'computer': computer_name})
        origin = request.headers.get('Origin')
        response.headers.add("Access-Control-Allow-Origin", origin if origin else "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,Accept,X-Requested-With")
        response.headers.add('Access-Control-Allow-Methods', "POST,OPTIONS")
        response.headers.add('Access-Control-Max-Age', "3600")
        return response

    try:
        # Basic validation
        if not computer_name or not computer_name.strip():
            return jsonify({'success': False, 'message': 'Nome da máquina é obrigatório'}), 400

        try:
            data = request.get_json(force=True) or {}
        except Exception as json_error:
            return jsonify({'success': False, 'message': 'Dados JSON inválidos ou ausentes', 'error': str(json_error)}), 400

        action = (data.get('action') or '').lower()
        if action not in ['enable', 'disable']:
            return jsonify({'success': False, 'message': 'Ação deve ser "enable" ou "disable"', 'received_action': action}), 400

        computer_name = computer_name.strip()
        use_powershell = bool(data.get('use_powershell', False))

        # Try methods in requested order: prefer PowerShell if explicitly requested; otherwise try LDAP then PowerShell fallback
        result = None
        last_exception = None

        if use_powershell:
            try:
                result = ad_computer_manager.toggle_computer_status_powershell(computer_name, action)
            except Exception as ps_err:
                diagnostic['ps_error'] = str(ps_err)
                # Try LDAP as fallback
                try:
                    result = ad_computer_manager.toggle_computer_status(computer_name, action)
                except Exception as ldap_err:
                    diagnostic['ldap_error'] = str(ldap_err)
                    raise Exception('Ambos os métodos falharam')
        else:
            try:
                result = ad_computer_manager.toggle_computer_status(computer_name, action)
            except Exception as ldap_err:
                diagnostic['ldap_error'] = str(ldap_err)
                # Try PowerShell fallback
                try:
                    result = ad_computer_manager.toggle_computer_status_powershell(computer_name, action)
                except Exception as ps_err:
                    diagnostic['ps_error'] = str(ps_err)
                    raise Exception('Ambos os métodos falharam')

        # Normalize result
        if not isinstance(result, dict):
            result = {'success': False, 'message': 'Resposta do gerenciador AD inesperada', 'raw': str(result)}

        # If status changed, attempt SQL update (best-effort)
        if result.get('success') and not result.get('already_in_desired_state'):
            try:
                is_enabled = action == 'enable'
                new_uac = result.get('operation', {}).get('new_status', {}).get('userAccountControl')
                try:
                    sql_manager.update_computer_status_in_sql(computer_name, is_enabled, new_uac)
                except Exception as sql_err:
                    # Log SQL update failure but do not fail the main operation
                    try:
                        sql_manager.log_computer_operation(
                            computer_name=computer_name,
                            operation=f'toggle_status_{action}_sql_update',
                            status='error',
                            details=str(sql_err)
                        )
                    except Exception:
                        pass
            except Exception:
                # ignore non-fatal errors here
                pass

        # Log the toggle attempt
        try:
            sql_manager.log_computer_operation(
                computer_name=computer_name,
                operation=f'toggle_status_{action}',
                status='success' if result.get('success') else 'failed',
                details=json.dumps(result, default=str)
            )
        except Exception:
            pass

        status_code = 200 if result.get('success') else 500

        response_payload = {
            'success': bool(result.get('success')), 
            'message': result.get('message') or ('Operação executada' if result.get('success') else 'Falha na operação'),
            'already_in_desired_state': bool(result.get('already_in_desired_state', False)),
            'details': result.get('operation', {}),
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(response_payload), status_code

    except Exception as e:
        # Try to log the error
        try:
            sql_manager.log_computer_operation(
                computer_name=computer_name,
                operation=f'toggle_status_error',
                status='error',
                error_message=str(e)
            )
        except Exception:
            pass
        # Map diagnostics to meaningful client errors (sanitize internal details)
        combined = ' '.join(filter(None, [diagnostic.get('ldap_error'), diagnostic.get('ps_error')]))
        lower_combined = (combined or str(e)).lower()

        # Computer not found in AD -> 404
        if 'não encontrada' in lower_combined or 'not found' in lower_combined:
            status_code = 404
            error_type = 'ComputerNotFound'
            message = 'Computador não encontrado no Active Directory'
            details = diagnostic.get('ldap_error') or str(e)

        # PowerShell ActiveDirectory module missing -> 503 (service issue)
        elif "module 'activedirectory'" in lower_combined or "specified module 'activedirectory' was not loaded" in lower_combined or 'no valid module file' in lower_combined:
            status_code = 503
            error_type = 'PowerShellModuleMissing'
            message = 'PowerShell ActiveDirectory module não disponível no servidor. Instale RSAT/ActiveDirectory ou habilite o módulo.'
            details = diagnostic.get('ps_error') or str(e)

        # Authentication / permission issues
        elif 'autenticação' in lower_combined or 'authentication' in lower_combined:
            status_code = 401
            error_type = 'AuthenticationError'
            message = 'Erro de autenticação ao acessar o Active Directory'
            details = combined or str(e)
        elif 'permissão' in lower_combined or 'permission' in lower_combined or 'access' in lower_combined:
            status_code = 403
            error_type = 'PermissionDenied'
            message = 'Permissão negada para modificar objeto no Active Directory'
            details = combined or str(e)
        else:
            status_code = 500
            error_type = 'InternalError'
            message = 'Erro interno ao processar a requisição'
            details = combined or str(e)

        payload = {
            'success': False,
            'message': message,
            'error': {
                'type': error_type,
                'computer_name': computer_name,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
        }

        return jsonify(payload), status_code

@app.route('/api/computers/<computer_name>/status', methods=['GET'])
def get_computer_status(computer_name):
    
    try:
        computer_info = ad_computer_manager.find_computer(computer_name)
        
        return jsonify({
            'success': True,
            'computer': {
                'name': computer_info['name'],
                'dn': computer_info['dn'],
                'enabled': not computer_info['disabled'],
                'disabled': computer_info['disabled'],
                'userAccountControl': computer_info['userAccountControl'],
                'description': computer_info['description'],
                'operatingSystem': computer_info['operatingSystem']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        
        if 'não encontrada' in str(e).lower() or 'not found' in str(e).lower():
            return jsonify({
                'success': False,
                'message': f'Computador {computer_name} não encontrado',
                'error': {'type': 'ComputerNotFound'}
            }), 404
        else:
            return jsonify({
                'success': False,
                'message': f'Erro ao consultar status: {str(e)}',
                'error': {'type': 'InternalError'}
            }), 500

@app.route('/api/computers/<computer_name>/details', methods=['GET'])
def get_computer_details(computer_name):
    
    try:
        
        query = """
        SELECT 
            c.*,
            o.name as organization_name,
            o.code as organization_code,
            os.name as os_name,
            os.version as os_version,
            os.family as os_family
        FROM computers c
        LEFT JOIN organizations o ON c.organization_id = o.id
        LEFT JOIN operating_systems os ON c.operating_system_id = os.id
        WHERE c.name = ? AND c.is_domain_controller = 0
        """
        
        result = sql_manager.execute_query(query, [computer_name])
        
        if not result:
            return jsonify({
                'error': f'Computador {computer_name} não encontrado',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        computer = result[0]
        

        details = {
            'name': computer['name'],
            'dn': computer['distinguished_name'],
            'enabled': computer['is_enabled'],
            'disabled': not computer['is_enabled'],
            'description': computer['description'] or '',
            'dnsHostName': computer['dns_hostname'] or '',
            'ipAddress': computer['ip_address'] or '',
            'macAddress': computer['mac_address'] or '',
            'userAccountControl': computer['user_account_control'] or 0,
            'primaryGroupID': computer['primary_group_id'] or 515,
            'lastLogon': computer['last_logon_timestamp'].isoformat() if computer['last_logon_timestamp'] else None,
            'created': computer['created_date'].isoformat() if computer['created_date'] else None,
            'lastSyncAd': computer['last_sync_ad'].isoformat() if computer['last_sync_ad'] else None,
            'organization': {
                'name': computer['organization_name'] or '',
                'code': computer['organization_code'] or ''
            },
            'operatingSystem': {
                'name': computer['os_name'] or 'N/A',
                'version': computer['os_version'] or 'N/A',
                'family': computer['os_family'] or 'N/A'
            },
            'source': 'sql',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(details)
        
    except Exception as e:
        
        return jsonify({
            'error': 'Erro interno do servidor',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/bulk-action', methods=['POST'])
def bulk_computer_action():
    """Executa ação em lote em múltiplos computadores"""
    try:
        data = request.get_json()
        
        if not data or 'computers' not in data or 'action' not in data:
            return jsonify({
                'success': False,
                'message': 'Campos "computers" e "action" são obrigatórios'
            }), 400
        
        computers = data['computers']
        action = data['action'].lower()
        
        if action not in ['enable', 'disable']:
            return jsonify({
                'success': False,
                'message': 'Ação deve ser "enable" ou "disable"'
            }), 400
        
        if not isinstance(computers, list) or len(computers) == 0:
            return jsonify({
                'success': False,
                'message': 'Lista de computadores não pode estar vazia'
            }), 400
        
       
        if len(computers) > 50:
            return jsonify({
                'success': False,
                'message': 'Máximo de 50 computadores por operação em lote'
            }), 400
        
        results = []
        success_count = 0
        error_count = 0
        
        for computer_name in computers:
            try:
                computer_name = computer_name.strip()
                if not computer_name:
                    continue
                
         
                result = ad_computer_manager.toggle_computer_status(computer_name, action)
                
                if result.get('success'):
                    success_count += 1

                    try:
                        is_enabled = action == 'enable'
                        new_uac = result.get('operation', {}).get('new_status', {}).get('userAccountControl')
                        sql_manager.update_computer_status_in_sql(computer_name, is_enabled, new_uac)
                    except Exception as sql_error:
                        continue
                else:
                    error_count += 1
                
                results.append({
                    'computer': computer_name,
                    'success': result.get('success', False),
                    'message': result.get('message', 'Erro desconhecido'),
                    'already_in_desired_state': result.get('already_in_desired_state', False)
                })
                
            except Exception as e:
                error_count += 1
                results.append({
                    'computer': computer_name,
                    'success': False,
                    'message': str(e),
                    'error': True
                })
        
       
        try:
            sql_manager.log_computer_operation(
                computer_name=f'BULK_OPERATION_{len(computers)}_computers',
                operation=f'bulk_{action}',
                status='completed',
                details=json.dumps({
                    'total': len(computers),
                    'success': success_count,
                    'errors': error_count,
                    'action': action
                }, default=str)
            )
        except Exception as log_error:
            logger.exception('Erro ao registrar operação em lote: %s', log_error)
        
        return jsonify({
            'success': True,
            'message': f'Operação em lote concluída: {success_count} sucessos, {error_count} erros',
            'summary': {
                'total': len(computers),
                'success_count': success_count,
                'error_count': error_count,
                'action': action
            },
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        
        return jsonify({
            'success': False,
            'message': f'Erro na operação em lote: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/<computer_name>/last-user', methods=['GET'])
def get_last_user_by_computer_ad_eventlog(computer_name):
   
    try:
        dias_historico = int(request.args.get('days', 30))
        
        
        
        resultado = ad_eventlog_service.buscar_ultimo_logon_por_computador(computer_name, dias_historico)
        
       
        response_data = {
            'success': resultado['success'],
            'computer_name': computer_name,
            'computer_found': resultado.get('computer_found'),
            'last_user': resultado['last_user'],
            'last_logon_time': resultado['last_logon_time'],
            'logon_type': resultado['logon_type'],
            'connection_method': resultado['connection_method'],
            'search_method': resultado['search_method'],
            'search_time': resultado['search_time'],
            'total_time': resultado['total_time'],
            'recent_logons': resultado['recent_logons'],
            'events_found': resultado.get('events_found', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        
        if resultado['error']:
            response_data['error'] = resultado['error']
        
       
        
        return jsonify(response_data), 200
            
    except Exception as e:
        
        return jsonify({
            'success': False,
            'computer_name': computer_name,
            'computer_found': False,
            'error': f'Erro interno: {str(e)}',
            'search_method': 'api_error',
            'connection_method': 'ad_eventlog',
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/api/computers/warranty-summary', methods=['GET'])
def get_warranty_summary():
   
    try:
        
        
        query = """
        SELECT 
            dw.computer_id,
            dw.warranty_status,
            dw.warranty_start_date,
            dw.warranty_end_date,
            dw.last_updated,
            dw.last_error,
            dw.service_tag,
            dw.service_tag_clean,
            dw.product_line_description,
            dw.system_description,
            c.name as computer_name,
            c.is_enabled,
            c.last_logon_timestamp
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        WHERE c.is_domain_controller = 0
            AND c.name IS NOT NULL
        ORDER BY 
            CASE 
                WHEN dw.warranty_end_date IS NULL THEN 3
                WHEN dw.warranty_end_date < GETDATE() THEN 1
                WHEN dw.warranty_end_date <= DATEADD(day, 30, GETDATE()) THEN 2
                ELSE 4
            END,
            dw.warranty_end_date ASC
        """
        
       
        start_time = time.time()
        
        warranties = sql_manager.execute_query(query)
        
        query_time = time.time() - start_time
        
        
        if not warranties:
            
            return jsonify([])
      
        processed_warranties = []
        for row in warranties:
            warranty_data = {
                'computer_id': row['computer_id'],
                'computer_name': row['computer_name'],
                'warranty_status': row['warranty_status'],
                'warranty_start_date': row['warranty_start_date'].isoformat() if row['warranty_start_date'] else None,
                'warranty_end_date': row['warranty_end_date'].isoformat() if row['warranty_end_date'] else None,
                'last_updated': row['last_updated'].isoformat() if row['last_updated'] else None,
                'last_error': row['last_error'],
                'service_tag': row['service_tag'],
                'service_tag_clean': row['service_tag_clean'],
                'product_line_description': row['product_line_description'],
                'system_description': row['system_description'],
                'is_enabled': row['is_enabled'],
                'last_logon_timestamp': row['last_logon_timestamp'].isoformat() if row['last_logon_timestamp'] else None
            }
            processed_warranties.append(warranty_data)
        
        
        return jsonify(processed_warranties)
        
    except Exception as e:
        
        return jsonify([]), 200

@app.route('/api/computers/warranty-stats', methods=['GET'])
def get_warranty_stats():
    
    try:
        
        
        query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE 
                WHEN dw.warranty_status = 'Active' 
                    AND dw.warranty_end_date > GETDATE() 
                    AND dw.warranty_end_date > DATEADD(day, 60, GETDATE())
                THEN 1 ELSE 0 
            END) as active,
            SUM(CASE 
                WHEN dw.warranty_end_date < GETDATE() 
                THEN 1 ELSE 0 
            END) as expired,
            SUM(CASE 
                WHEN dw.warranty_end_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE()) 
                THEN 1 ELSE 0 
            END) as expiring_30,
            SUM(CASE 
                WHEN dw.warranty_end_date BETWEEN DATEADD(day, 31, GETDATE()) AND DATEADD(day, 60, GETDATE()) 
                THEN 1 ELSE 0 
            END) as expiring_60,
            SUM(CASE 
                WHEN dw.warranty_end_date IS NULL OR dw.last_error IS NOT NULL 
                THEN 1 ELSE 0 
            END) as unknown
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        WHERE c.is_domain_controller = 0
        """
        
        result = sql_manager.execute_query(query)
        
        if not result:
            stats = {
                'total': 0,
                'active': 0,
                'expired': 0,
                'expiring_30': 0,
                'expiring_60': 0,
                'unknown': 0
            }
        else:
            stats = result[0]
        
        response_data = {
            'total': int(stats.get('total', 0)),
            'active': int(stats.get('active', 0)),
            'expired': int(stats.get('expired', 0)),
            'expiring_30': int(stats.get('expiring_30', 0)),
            'expiring_60': int(stats.get('expiring_60', 0)),
            'unknown': int(stats.get('unknown', 0)),
            'last_updated': datetime.now().isoformat()
        }
        
        
        
        return jsonify(response_data)
        
    except Exception as e:
      
        return jsonify({
            'total': 0,
            'active': 0,
            'expired': 0,
            'expiring_30': 0,
            'expiring_60': 0,
            'unknown': 0,
            'last_updated': datetime.now().isoformat(),
            'error': 'Erro ao carregar estatísticas'
        })

@app.route('/api/computers/warranty/<int:computer_id>', methods=['GET'])
def get_warranty_by_computer_id(computer_id):
   
    try:
    
        query = """
        SELECT 
            dw.*,
            c.name as computer_name,
            c.description as computer_description
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        WHERE dw.computer_id = ?
        """
        
        result = sql_manager.execute_query(query, [computer_id])
        
        if not result:
            return jsonify({ 
                'error': 'Garantia não encontrada para esta máquina',
                'computer_id': computer_id 
            }), 404
        
        warranty = result[0]
        
        
        warranty_calculated_status = 'unknown'
        days_to_expiry = None
        
        if warranty['warranty_end_date'] and not warranty['last_error']:
            now = datetime.now()
            end_date = warranty['warranty_end_date']
            
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            
            days_to_expiry = (end_date - now).days
            
            if days_to_expiry < 0:
                warranty_calculated_status = 'expired'
            elif days_to_expiry <= 30:
                warranty_calculated_status = 'expiring_30'
            elif days_to_expiry <= 60:
                warranty_calculated_status = 'expiring_60'
            else:
                warranty_calculated_status = 'active'
        
        
        response_data = {
            'id': warranty['id'],
            'computer_id': warranty['computer_id'],
            'computer_name': warranty['computer_name'],
            'computer_description': warranty['computer_description'],
            'service_tag': warranty['service_tag'],
            'service_tag_clean': warranty['service_tag_clean'],
            'warranty_start_date': warranty['warranty_start_date'].isoformat() if warranty['warranty_start_date'] else None,
            'warranty_end_date': warranty['warranty_end_date'].isoformat() if warranty['warranty_end_date'] else None,
            'warranty_status': warranty['warranty_status'],
            'warranty_calculated_status': warranty_calculated_status,
            'days_to_expiry': days_to_expiry,
            'product_line_description': warranty['product_line_description'],
            'system_description': warranty['system_description'],
            'ship_date': warranty['ship_date'].isoformat() if warranty.get('ship_date') else None,
            'order_number': warranty['order_number'],
            'entitlements': warranty['entitlements'],
            'last_updated': warranty['last_updated'].isoformat() if warranty['last_updated'] else None,
            'cache_expires_at': warranty['cache_expires_at'].isoformat() if warranty['cache_expires_at'] else None,
            'last_error': warranty['last_error'],
            'created_at': warranty['created_at'].isoformat() if warranty['created_at'] else None
        }
        
        
        
        return jsonify(response_data)
        
    except Exception as e:
        
        return jsonify({ 
            'error': 'Erro interno do servidor',
            'details': str(e) 
        }), 500

@app.route('/api/computers/warranty/refresh', methods=['POST'])
def refresh_warranties():
   
    try:
        data = request.get_json() or {}
        max_computers = data.get('max_computers')
        only_expired = data.get('only_expired', False)
        only_errors = data.get('only_errors', False)
        workers = data.get('workers', 5)
        
        
        
        import subprocess
        import os
    
        script_path = 'dell_warranty_updater.py'  
        
        cmd = ['python', script_path]
        
        if max_computers:
            cmd.extend(['--max-computers', str(max_computers)])
        
        if only_expired:
            cmd.append('--only-expired')
        
        if only_errors:
            cmd.append('--only-errors')
        
        cmd.extend(['--workers', str(workers)])
        
        if os.getenv('FLASK_ENV') == 'development':
         
            simulated_response = {
                'success': True,
                'message': 'Atualização de garantias iniciada em background (simulação)',
                'timestamp': datetime.now().isoformat(),
                'parameters': {
                    'max_computers': max_computers or 'all',
                    'only_expired': only_expired,
                    'only_errors': only_errors,
                    'workers': workers
                },
                'estimated_duration': '5-15 minutos',
                'note': 'Esta é uma simulação para desenvolvimento'
            }

            return jsonify(simulated_response)
        
    
        try:
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            response_data = {
                'success': True,
                'message': 'Atualização de garantias iniciada em background',
                'timestamp': datetime.now().isoformat(),
                'process_id': process.pid,
                'parameters': {
                    'max_computers': max_computers or 'all',
                    'only_expired': only_expired,
                    'only_errors': only_errors,
                    'workers': workers
                },
                'command': ' '.join(cmd),
                'estimated_duration': '5-30 minutos dependendo da quantidade'
            }
            
       
            return jsonify(response_data)
            
        except FileNotFoundError:
          
            return jsonify({
                'success': False,
                'message': 'Script de atualização não encontrado',
                'error': f'Arquivo {script_path} não encontrado',
                'timestamp': datetime.now().isoformat()
            }), 500
            
        except Exception as subprocess_error:
           
            return jsonify({
                'success': False,
                'message': 'Erro ao iniciar atualização de garantias',
                'error': str(subprocess_error),
                'timestamp': datetime.now().isoformat()
            }), 500
        
    except Exception as e:
       
        return jsonify({ 
            'success': False,
            'message': 'Erro ao iniciar atualização de garantias',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/warranty/refresh-status', methods=['GET'])
def get_warranty_refresh_status():
   
    try:
        
        query = """
        SELECT TOP 5
            sync_type,
            start_time,
            end_time,
            status,
            computers_found,
            computers_added,
            computers_updated,
            errors_count,
            error_message
        FROM sync_logs
        WHERE sync_type LIKE '%warranty%' OR sync_type LIKE '%dell%'
        ORDER BY start_time DESC
        """
        
        logs = sql_manager.execute_query(query)
        
  
        if logs:
            last_log = logs[0]
            last_run = {
                'type': last_log['sync_type'],
                'start_time': last_log['start_time'].isoformat() if last_log['start_time'] else None,
                'end_time': last_log['end_time'].isoformat() if last_log['end_time'] else None,
                'status': last_log['status'],
                'computers_found': last_log['computers_found'],
                'computers_updated': last_log['computers_updated'],
                'errors_count': last_log['errors_count'],
                'error_message': last_log['error_message']
            }
        else:
            last_run = None
        
        running_processes = []
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'dell_warranty' in ' '.join(proc.info['cmdline'] or []):
                        running_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': ' '.join(proc.info['cmdline'] or [])
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
           
            pass
        
        response_data = {
            'last_run': last_run,
            'running_processes': running_processes,
            'is_running': len(running_processes) > 0,
            'recent_logs': logs,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        
        return jsonify({
            'error': 'Erro interno do servidor',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/warranty/search', methods=['GET'])
def search_warranties():
    
    try:
        
        status_filter = request.args.get('status', 'all')  
        organization = request.args.get('organization', '')
        search_term = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 100)), 1000)
        offset = int(request.args.get('offset', 0))

        
  
        where_conditions = ["c.is_domain_controller = 0"]
        params = []
        
      
        if search_term:
            where_conditions.append("""
                (c.name LIKE ? OR 
                 dw.service_tag LIKE ? OR 
                 dw.service_tag_clean LIKE ? OR
                 dw.product_line_description LIKE ? OR
                 dw.system_description LIKE ?)
            """)
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern] * 5)
        
        
        if organization:
            where_conditions.append("o.code = ?")
            params.append(organization)
        
        if status_filter != 'all':
            if status_filter == 'active':
                where_conditions.append("""
                    dw.warranty_end_date > GETDATE() 
                    AND dw.warranty_end_date > DATEADD(day, 60, GETDATE())
                    AND dw.last_error IS NULL
                """)
            elif status_filter == 'expired':
                where_conditions.append("dw.warranty_end_date < GETDATE()")
            elif status_filter == 'expiring_30':
                where_conditions.append("""
                    dw.warranty_end_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())
                """)
            elif status_filter == 'expiring_60':
                where_conditions.append("""
                    dw.warranty_end_date BETWEEN DATEADD(day, 31, GETDATE()) AND DATEADD(day, 60, GETDATE())
                """)
            elif status_filter == 'unknown':
                where_conditions.append("""
                    (dw.warranty_end_date IS NULL OR dw.last_error IS NOT NULL)
                """)
        
        where_clause = " AND ".join(where_conditions)
        
       
        query = f"""
        SELECT 
            dw.computer_id,
            c.name as computer_name,
            dw.service_tag,
            dw.service_tag_clean,
            dw.warranty_start_date,
            dw.warranty_end_date,
            dw.warranty_status,
            dw.product_line_description,
            dw.system_description,
            dw.last_updated,
            dw.last_error,
            o.name as organization_name,
            o.code as organization_code,
            c.is_enabled
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        LEFT JOIN organizations o ON c.organization_id = o.id
        WHERE {where_clause}
        ORDER BY 
            CASE 
                WHEN dw.warranty_end_date IS NULL THEN 3
                WHEN dw.warranty_end_date < GETDATE() THEN 1
                WHEN dw.warranty_end_date <= DATEADD(day, 30, GETDATE()) THEN 2
                ELSE 4
            END,
            dw.warranty_end_date ASC,
            c.name
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
     
        count_query = f"""
        SELECT COUNT(*) as total
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        LEFT JOIN organizations o ON c.organization_id = o.id
        WHERE {where_clause}
        """
        
        
        params_with_pagination = params + [offset, limit]
        results = sql_manager.execute_query(query, params_with_pagination)
        count_result = sql_manager.execute_query(count_query, params)
        
        total = count_result[0]['total'] if count_result else 0
        
  
        warranties = []
        for row in results:
            warranty_data = {
                'computer_id': row['computer_id'],
                'computer_name': row['computer_name'],
                'service_tag': row['service_tag'],
                'service_tag_clean': row['service_tag_clean'],
                'warranty_start_date': row['warranty_start_date'].isoformat() if row['warranty_start_date'] else None,
                'warranty_end_date': row['warranty_end_date'].isoformat() if row['warranty_end_date'] else None,
                'warranty_status': row['warranty_status'],
                'product_line_description': row['product_line_description'],
                'system_description': row['system_description'],
                'last_updated': row['last_updated'].isoformat() if row['last_updated'] else None,
                'last_error': row['last_error'],
                'organization_name': row['organization_name'],
                'organization_code': row['organization_code'],
                'is_enabled': row['is_enabled']
            }
            warranties.append(warranty_data)
        
        response_data = {
            'warranties': warranties,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total,
            'filters': {
                'status': status_filter,
                'organization': organization,
                'search_term': search_term
            },
            'timestamp': datetime.now().isoformat()
        }
        
        
        return jsonify(response_data)
        
    except Exception as e:
        
        return jsonify({
            'error': 'Erro interno do servidor',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/warranty/debug/<computer_name>', methods=['GET'])
def debug_warranty_info(computer_name):
    
    try:
        debug_info = {
            'computer_name': computer_name,
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        
        
        computer_query = """
        SELECT id, name, description, organization_id 
        FROM computers 
        WHERE name = ? AND is_domain_controller = 0
        """
        
        computer_result = sql_manager.execute_query(computer_query, [computer_name])
        
        if computer_result:
            computer = computer_result[0]
            debug_info['tests']['computer_exists'] = {
                'found': True,
                'computer_id': computer['id'],
                'description': computer['description']
            }
            
          
            warranty_query = """
            SELECT * FROM dell_warranty WHERE computer_id = ?
            """
            
            warranty_result = sql_manager.execute_query(warranty_query, [computer['id']])
            
            if warranty_result:
                warranty = warranty_result[0]
                debug_info['tests']['warranty_exists'] = {
                    'found': True,
                    'service_tag': warranty['service_tag'],
                    'warranty_status': warranty['warranty_status'],
                    'warranty_end_date': warranty['warranty_end_date'].isoformat() if warranty['warranty_end_date'] else None,
                    'last_updated': warranty['last_updated'].isoformat() if warranty['last_updated'] else None,
                    'last_error': warranty['last_error']
                }
            else:
                debug_info['tests']['warranty_exists'] = {
                    'found': False,
                    'message': 'Nenhum dado de garantia encontrado'
                }
            
           
            extracted_service_tag = extract_service_tag_from_computer_name(computer_name)
            debug_info['tests']['service_tag_extraction'] = {
                'original_name': computer_name,
                'extracted_service_tag': extracted_service_tag,
                'extraction_successful': extracted_service_tag != computer_name
            }
            
            if extracted_service_tag:
                
                try:
                    dell_result = dell_api.get_warranty_info(extracted_service_tag)
                    
                    debug_info['tests']['dell_api_test'] = {
                        'attempted': True,
                        'service_tag_used': extracted_service_tag,
                        'success': 'error' not in dell_result,
                        'result': dell_result
                    }
                except Exception as dell_error:
                    debug_info['tests']['dell_api_test'] = {
                        'attempted': True,
                        'service_tag_used': extracted_service_tag,
                        'success': False,
                        'error': str(dell_error)
                    }
            else:
                debug_info['tests']['dell_api_test'] = {
                    'attempted': False,
                    'reason': 'Não foi possível extrair service tag válida'
                }
        else:
            debug_info['tests']['computer_exists'] = {
                'found': False,
                'message': f'Computador {computer_name} não encontrado na base de dados'
            }
        
  
        debug_info['summary'] = {
            'computer_in_db': debug_info['tests']['computer_exists']['found'],
            'has_warranty_data': debug_info['tests'].get('warranty_exists', {}).get('found', False),
            'can_extract_service_tag': debug_info['tests'].get('service_tag_extraction', {}).get('extraction_successful', False),
            'dell_api_working': debug_info['tests'].get('dell_api_test', {}).get('success', False)
        }
        
        
        recommendations = []
        
        if not debug_info['summary']['computer_in_db']:
            recommendations.append('Computador não encontrado - verificar se está sincronizado do AD')
        
        if not debug_info['summary']['has_warranty_data']:
            recommendations.append('Executar script de atualização de garantias Dell')
        
        if not debug_info['summary']['can_extract_service_tag']:
            recommendations.append('Verificar se nome do computador segue padrão com service tag')
        
        if not debug_info['summary']['dell_api_working']:
            recommendations.append('Verificar conectividade com API Dell e credenciais')
        
        if debug_info['tests'].get('warranty_exists', {}).get('found') and debug_info['tests']['warranty_exists'].get('last_error'):
            recommendations.append('Executar atualização específica para corrigir erro na garantia')
        
        debug_info['summary']['recommendations'] = recommendations
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        
        return jsonify({
            'success': False,
            'computer_name': computer_name,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/<computer_name>/warranty/refresh', methods=['POST'])
def refresh_single_computer_warranty(computer_name):
   
    try:
        
        
        
        computer_query = """
        SELECT id, name, description 
        FROM computers 
        WHERE name = ? AND is_domain_controller = 0
        """
        
        computer_result = sql_manager.execute_query(computer_query, [computer_name])
        
        if not computer_result:
            return jsonify({
                'success': False,
                'message': f'Computador {computer_name} não encontrado',
                'computer_name': computer_name
            }), 404
        
        computer = computer_result[0]
        computer_id = computer['id']

        service_tag = extract_service_tag_from_computer_name(computer_name)
        
        if not service_tag or len(service_tag) < 5:
            return jsonify({
                'success': False,
                'message': f'Não foi possível extrair service tag válida de {computer_name}',
                'computer_name': computer_name,
                'extracted_service_tag': service_tag
            }), 400

        warranty_data = dell_api.get_warranty_info(service_tag)
        
        if 'error' in warranty_data:
            
            error_query = """
            MERGE dell_warranty AS target
            USING (SELECT ? as computer_id) AS source
            ON target.computer_id = source.computer_id
            WHEN MATCHED THEN
                UPDATE SET 
                    service_tag = ?,
                    last_updated = GETDATE(),
                    cache_expires_at = DATEADD(hour, 6, GETDATE()),
                    last_error = ?
            WHEN NOT MATCHED THEN
                INSERT (computer_id, service_tag, last_updated, cache_expires_at, last_error, created_at)
                VALUES (?, ?, GETDATE(), DATEADD(hour, 6, GETDATE()), ?, GETDATE());
            """
            
            error_message = f"{warranty_data.get('code', 'ERROR')}: {warranty_data.get('error', 'Unknown error')}"
            
            sql_manager.execute_query(error_query, [
                computer_id, service_tag, error_message,
                computer_id, service_tag, error_message
            ], fetch=False)
            
            return jsonify({
                'success': False,
                'message': f'Erro ao consultar garantia: {warranty_data["error"]}',
                'computer_name': computer_name,
                'service_tag': service_tag,
                'error_code': warranty_data.get('code'),
                'dell_api_error': warranty_data['error']
            }), 200

        warranty_start_date = None
        warranty_end_date = None
        warranty_status = 'Unknown'
        
   
        if warranty_data.get('dataExpiracao') and warranty_data['dataExpiracao'] != 'Não disponível':
            try:
                
                from datetime import datetime as dt
                warranty_end_date = dt.strptime(warranty_data['dataExpiracao'], '%d/%m/%Y')
                warranty_status = 'Active' if warranty_data.get('status') == 'Em garantia' else 'Expired'
            except:
                pass

        upsert_query = """
        MERGE dell_warranty AS target
        USING (SELECT ? as computer_id) AS source
        ON target.computer_id = source.computer_id
        WHEN MATCHED THEN
            UPDATE SET 
                service_tag = ?,
                service_tag_clean = ?,
                warranty_start_date = ?,
                warranty_end_date = ?,
                warranty_status = ?,
                product_line_description = ?,
                system_description = ?,
                last_updated = GETDATE(),
                cache_expires_at = DATEADD(day, 7, GETDATE()),
                last_error = NULL
        WHEN NOT MATCHED THEN
            INSERT (computer_id, service_tag, service_tag_clean, warranty_start_date, warranty_end_date,
                   warranty_status, product_line_description, system_description, 
                   last_updated, cache_expires_at, last_error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), DATEADD(day, 7, GETDATE()), NULL, GETDATE());
        """
        
        params = [
            computer_id, service_tag, service_tag, warranty_start_date, warranty_end_date,
            warranty_status, warranty_data.get('modelo', ''), warranty_data.get('modelo', ''),
            computer_id, service_tag, service_tag, warranty_start_date, warranty_end_date,
            warranty_status, warranty_data.get('modelo', ''), warranty_data.get('modelo', '')
        ]
        
        sql_manager.execute_query(upsert_query, params, fetch=False)
        
        
        response_data = {
            'success': True,
            'message': f'Garantia atualizada com sucesso para {computer_name}',
            'computer_name': computer_name,
            'computer_id': computer_id,
            'service_tag': service_tag,
            'warranty_data': {
                'service_tag': service_tag,
                'warranty_status': warranty_status,
                'warranty_end_date': warranty_end_date.isoformat() if warranty_end_date else None,
                'product_description': warranty_data.get('modelo', ''),
                'dell_status': warranty_data.get('status', ''),
                'expiration_date_formatted': warranty_data.get('dataExpiracao', ''),
                'ship_date': warranty_data.get('shipDate'),
                'order_number': warranty_data.get('orderNumber')
            },
            'last_updated': datetime.now().isoformat(),
            'cache_expires_in_days': 7
        }
        
       
        
        return jsonify(response_data), 200
        
    except Exception as e:

        return jsonify({
            'success': False,
            'message': f'Erro interno ao atualizar garantia: {str(e)}',
            'computer_name': computer_name,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/warranty/export', methods=['GET'])
def export_warranty_data():
   
    try:
        format_type = request.args.get('format', 'csv').lower()
        status_filter = request.args.get('status', 'all')
        

        
        
        query = """
        SELECT 
            c.name as computer_name,
            dw.service_tag,
            dw.service_tag_clean,
            dw.warranty_status,
            dw.warranty_start_date,
            dw.warranty_end_date,
            dw.product_line_description,
            dw.system_description,
            dw.last_updated,
            dw.last_error,
            o.name as organization_name,
            o.code as organization_code,
            c.is_enabled,
            c.last_logon_timestamp,
            CASE 
                WHEN dw.warranty_end_date IS NULL THEN 'Desconhecido'
                WHEN dw.warranty_end_date < GETDATE() THEN 'Expirada'
                WHEN dw.warranty_end_date <= DATEADD(day, 30, GETDATE()) THEN 'Expirando em 30 dias'
                WHEN dw.warranty_end_date <= DATEADD(day, 60, GETDATE()) THEN 'Expirando em 60 dias'
                ELSE 'Ativa'
            END as warranty_status_calc,
            CASE 
                WHEN dw.warranty_end_date IS NOT NULL AND dw.warranty_end_date >= GETDATE()
                THEN DATEDIFF(day, GETDATE(), dw.warranty_end_date)
                ELSE NULL
            END as days_to_expiry
        FROM dell_warranty dw
        INNER JOIN computers c ON dw.computer_id = c.id
        LEFT JOIN organizations o ON c.organization_id = o.id
        WHERE c.is_domain_controller = 0
        """
        

        params = []
        if status_filter != 'all':
            if status_filter == 'active':
                query += " AND dw.warranty_end_date > DATEADD(day, 60, GETDATE())"
            elif status_filter == 'expired':
                query += " AND dw.warranty_end_date < GETDATE()"
            elif status_filter == 'expiring_30':
                query += " AND dw.warranty_end_date BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())"
            elif status_filter == 'expiring_60':
                query += " AND dw.warranty_end_date BETWEEN DATEADD(day, 31, GETDATE()) AND DATEADD(day, 60, GETDATE())"
        
        query += " ORDER BY dw.warranty_end_date ASC, c.name"
        
        results = sql_manager.execute_query(query, params)
        
        if format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
       
            headers = [
                'Computer Name', 'Service Tag', 'Service Tag Clean', 'Warranty Status',
                'Warranty Start Date', 'Warranty End Date', 'Product Description',
                'System Description', 'Last Updated', 'Organization', 'Organization Code',
                'Computer Enabled', 'Last Logon', 'Warranty Status Calculated', 'Days to Expiry',
                'Last Error'
            ]
            writer.writerow(headers)

            for row in results:
                csv_row = [
                    row['computer_name'],
                    row['service_tag'] or '',
                    row['service_tag_clean'] or '',
                    row['warranty_status'] or '',
                    row['warranty_start_date'].strftime('%Y-%m-%d') if row['warranty_start_date'] else '',
                    row['warranty_end_date'].strftime('%Y-%m-%d') if row['warranty_end_date'] else '',
                    row['product_line_description'] or '',
                    row['system_description'] or '',
                    row['last_updated'].strftime('%Y-%m-%d %H:%M:%S') if row['last_updated'] else '',
                    row['organization_name'] or '',
                    row['organization_code'] or '',
                    'Yes' if row['is_enabled'] else 'No',
                    row['last_logon_timestamp'].strftime('%Y-%m-%d %H:%M:%S') if row['last_logon_timestamp'] else '',
                    row['warranty_status_calc'],
                    row['days_to_expiry'] if row['days_to_expiry'] is not None else '',
                    row['last_error'] or ''
                ]
                writer.writerow(csv_row)
            
            output.seek(0)
            csv_content = output.getvalue()
            output.close()
            
        
            from flask import Response
            
            filename = f"dell_warranties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={"Content-disposition": f"attachment; filename={filename}"}
            )
            
        elif format_type == 'json':
           
            processed_results = []
            for row in results:
                processed_row = {
                    'computer_name': row['computer_name'],
                    'service_tag': row['service_tag'],
                    'service_tag_clean': row['service_tag_clean'],
                    'warranty_status': row['warranty_status'],
                    'warranty_start_date': row['warranty_start_date'].isoformat() if row['warranty_start_date'] else None,
                    'warranty_end_date': row['warranty_end_date'].isoformat() if row['warranty_end_date'] else None,
                    'product_line_description': row['product_line_description'],
                    'system_description': row['system_description'],
                    'last_updated': row['last_updated'].isoformat() if row['last_updated'] else None,
                    'organization_name': row['organization_name'],
                    'organization_code': row['organization_code'],
                    'is_enabled': row['is_enabled'],
                    'last_logon_timestamp': row['last_logon_timestamp'].isoformat() if row['last_logon_timestamp'] else None,
                    'warranty_status_calculated': row['warranty_status_calc'],
                    'days_to_expiry': row['days_to_expiry'],
                    'last_error': row['last_error']
                }
                processed_results.append(processed_row)
            
            return jsonify({
                'success': True,
                'data': processed_results,
                'total_records': len(processed_results),
                'export_date': datetime.now().isoformat(),
                'status_filter': status_filter
            })
        
        else:
            return jsonify({
                'success': False,
                'message': f'Formato {format_type} não suportado. Use csv ou json.'
            }), 400
        
    except Exception as e:
        
        return jsonify({
            'success': False,
            'message': f'Erro ao exportar dados: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/computers/sync-complete', methods=['POST'])
def sync_complete_from_ad():
    
    try:
        
        ad_computers = ad_manager.get_computers()
        
        if not ad_computers:
            return jsonify({
                'success': False,
                'message': 'Nenhuma máquina encontrada no Active Directory',
                'timestamp': datetime.now().isoformat()
            }), 400
        

       
        stats_before_query = """
        SELECT 
            COUNT(*) as total_before,
            SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled_before,
            SUM(CASE WHEN is_enabled = 0 THEN 1 ELSE 0 END) as disabled_before
        FROM computers 
        WHERE is_domain_controller = 0
        """
        
        stats_before_result = sql_manager.execute_query(stats_before_query)
        stats_before = stats_before_result[0] if stats_before_result else {}
        
       
        
        cleanup_query = """
        DELETE FROM computers 
        WHERE is_domain_controller = 0
        """
        
        deleted_count = sql_manager.execute_query(cleanup_query, fetch=False)
        
        
        try:
            
            cleanup_logs_query = """
            DELETE FROM computer_operations_log 
            WHERE operation_time < DATEADD(day, -30, GETDATE())
            """
            sql_manager.execute_query(cleanup_logs_query, fetch=False)
            
            
            cleanup_warranty_query = """
            IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'dell_warranty')
            BEGIN
                DELETE FROM dell_warranty 
                WHERE computer_id NOT IN (SELECT id FROM computers)
            END
            """
            sql_manager.execute_query(cleanup_warranty_query, fetch=False)
            
        except Exception as cleanup_error:
            logger.exception('Erro ao limpar dados antigos: %s', cleanup_error)
 
        
        stats = {
            'found_ad': len(ad_computers),
            'total_before': stats_before.get('total_before', 0),
            'deleted': deleted_count,
            'added': 0,
            'updated': 0,
            'errors': 0
        }
        
        for computer in ad_computers:
            try:
     
                result = sql_manager.sync_computer_to_sql(computer)
                
                if result:
                    stats['added'] += 1
                else:
                    stats['errors'] += 1
            
                    
            except Exception as e:
                
                stats['errors'] += 1

        final_stats_query = """
        SELECT 
            COUNT(*) as total_after,
            SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled_after,
            SUM(CASE WHEN is_enabled = 0 THEN 1 ELSE 0 END) as disabled_after
        FROM computers 
        WHERE is_domain_controller = 0
        """
        
        final_stats_result = sql_manager.execute_query(final_stats_query)
        final_stats = final_stats_result[0] if final_stats_result else {}
        
        stats['total_after'] = final_stats.get('total_after', 0)
        stats['enabled_after'] = final_stats.get('enabled_after', 0)
        stats['disabled_after'] = final_stats.get('disabled_after', 0)
        
      
        sql_manager.log_sync_operation(
            'complete_sync_with_cleanup', 
            'completed' if stats['errors'] == 0 else 'completed_with_errors', 
            {
                'found': stats['found_ad'],
                'added': stats['added'], 
                'updated': 0,  
                'errors': stats['errors']
            }
        )
        

        try:
            reset_identity_query = """
            IF EXISTS (SELECT * FROM computers WHERE is_domain_controller = 0)
            BEGIN
                DECLARE @max_id INT
                SELECT @max_id = ISNULL(MAX(id), 0) FROM computers
                DBCC CHECKIDENT('computers', RESEED, @max_id)
            END
            """
            sql_manager.execute_query(reset_identity_query, fetch=False)
        except Exception as reset_error:
            logger.exception('Erro ao resetar identity: %s', reset_error)
        duration_message = f"Sincronização completa com limpeza finalizada"
        
        response_data = {
            'success': True,
            'message': duration_message,
            'stats': {
                'computers_found_ad': stats['found_ad'],
                'computers_before_cleanup': stats['total_before'],
                'computers_deleted': stats['deleted'],
                'computers_added': stats['added'],
                'computers_after_sync': stats['total_after'],
                'enabled_after': stats['enabled_after'],
                'disabled_after': stats['disabled_after'],
                'computers_with_errors': stats['errors'],
                'total_processed': stats['found_ad']
            },
            'operation_type': 'complete_cleanup_and_rebuild',
            'timestamp': datetime.now().isoformat(),
            'cache_cleared': True,
            'data_refreshed': True
        }
        
        
        
        return jsonify(response_data)
        
    except Exception as e:
        
        

        sql_manager.log_sync_operation(
            'complete_sync_with_cleanup', 
            'failed', 
            error_message=str(e)
        )
        
        return jsonify({
            'success': False,
            'message': f'Erro na sincronização completa: {str(e)}',
            'operation_type': 'complete_cleanup_and_rebuild',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/sync-incremental', methods=['POST'])
def sync_incremental_from_ad():
  
    try:
        
        
        
        sync_service.sync_ad_to_sql()
        
        return jsonify({
            'success': True,
            'message': 'Sincronização incremental concluída',
            'operation_type': 'incremental_update',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        
        return jsonify({
            'success': False,
            'message': f'Erro na sincronização incremental: {str(e)}',
            'operation_type': 'incremental_update',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/computers/force-ad-refresh', methods=['POST'])
def force_ad_refresh():
    
    try:

        return sync_complete_from_ad()
        
    except Exception as e:
        
        return jsonify({
            'success': False,
            'message': f'Erro no refresh do AD: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/computers/sync-status', methods=['GET'])
def get_detailed_sync_status():
    
    try:
        
        sql_stats_query = """
        SELECT 
            COUNT(*) as total_sql,
            SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled_sql,
            SUM(CASE WHEN is_enabled = 0 THEN 1 ELSE 0 END) as disabled_sql,
            MAX(last_sync_ad) as last_sync_time,
            COUNT(CASE WHEN last_sync_ad IS NULL THEN 1 END) as never_synced,
            COUNT(CASE WHEN last_sync_ad < DATEADD(hour, -24, GETDATE()) THEN 1 END) as outdated_sync
        FROM computers 
        WHERE is_domain_controller = 0
        """
        
        sql_stats_result = sql_manager.execute_query(sql_stats_query)
        sql_stats = sql_stats_result[0] if sql_stats_result else {}
        
        
        try:
            ad_computers = ad_manager.get_computers()
            ad_stats = {
                'total_ad': len(ad_computers),
                'enabled_ad': len([c for c in ad_computers if not c.get('disabled', False)]),
                'disabled_ad': len([c for c in ad_computers if c.get('disabled', False)])
            }
        except Exception as ad_error:
            
            ad_stats = {
                'total_ad': 0,
                'enabled_ad': 0,
                'disabled_ad': 0,
                'ad_error': str(ad_error)
            }
        
        
        recent_logs_query = """
        SELECT TOP 5
            sync_type,
            start_time,
            end_time,
            status,
            computers_found,
            computers_added,
            computers_updated,
            errors_count,
            error_message
        FROM sync_logs
        ORDER BY start_time DESC
        """
        
        recent_logs = sql_manager.execute_query(recent_logs_query)
        
        response_data = {
            'sql_stats': sql_stats,
            'ad_stats': ad_stats,
            'sync_needed': (sql_stats.get('total_sql', 0) != ad_stats.get('total_ad', 0)),
            'sync_service_status': {
                'running': sync_service.sync_running,
                'last_sync': sync_service.last_sync.isoformat() if sync_service.last_sync else None
            },
            'recent_sync_logs': recent_logs,
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }
        
        if sql_stats.get('total_sql', 0) == 0:
            response_data['recommendations'].append('Executar sincronização completa - SQL vazio')
        elif sql_stats.get('total_sql', 0) != ad_stats.get('total_ad', 0):
            response_data['recommendations'].append('Diferença detectada entre AD e SQL - considerar sincronização completa')
        elif sql_stats.get('never_synced', 0) > 0:
            response_data['recommendations'].append(f'{sql_stats.get("never_synced")} máquinas nunca sincronizadas')
        elif sql_stats.get('outdated_sync', 0) > 0:
            response_data['recommendations'].append(f'{sql_stats.get("outdated_sync")} máquinas com sync antigo (24h+)')
        
        return jsonify(response_data)
        
    except Exception as e:
        
        return jsonify({
            'error': 'Erro interno do servidor',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500