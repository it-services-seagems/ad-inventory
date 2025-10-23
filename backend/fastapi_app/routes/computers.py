from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from datetime import datetime
import time
import re
from ..managers import sql_manager, ad_manager, ad_computer_manager
from ..connections import require_dhcp_manager

computers_router = APIRouter()


@computers_router.get('/')
def list_computers(source: str = 'sql', inventory_filter: str = None):
    try:
        if source == 'sql':
            results = sql_manager.get_computers_from_sql(inventory_filter=inventory_filter)
            # Return a pure list (compatibility with old Flask response)
            return JSONResponse(content=results)
        else:
            results = ad_manager.get_computers()
            return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@computers_router.get('/details/{computer_name}')
def computer_details(computer_name: str):
    try:
        # Use a richer query (join OS and organization) similar to the legacy Flask app
        q = """
        SELECT TOP 1
            c.id,
            c.name,
            c.dns_hostname,
            c.distinguished_name as dn,
            c.is_enabled,
            c.is_domain_controller,
            c.description,
            c.last_logon_timestamp as lastLogon,
            c.created_date as created,
            c.user_account_control,
            c.primary_group_id,
            c.last_sync_ad,
            c.ip_address,
            c.mac_address,
            o.name as organization_name,
            o.code as organization_code,
            os.name as os,
            os.version as osVersion
        FROM computers c
        LEFT JOIN organizations o ON c.organization_id = o.id
    LEFT JOIN operating_systems os ON c.operating_system_id = os.id
    WHERE c.name = ?"""
        rows = sql_manager.execute_query(q, params=(computer_name,))
        if rows:
            # Format the result similar to Flask route
            computer = rows[0]
            return computer
        raise HTTPException(status_code=404, detail='Computer not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@computers_router.options('/{computer_name}/toggle-status')
def toggle_status_options(computer_name: str, request: Request):
    # Replica the explicit OPTIONS CORS handling from Flask route
    resp = JSONResponse(content={'status': 'OK', 'computer': computer_name})
    origin = request.headers.get('origin')
    if origin:
        resp.headers['Access-Control-Allow-Origin'] = origin
    else:
        resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Accept,X-Requested-With'
    resp.headers['Access-Control-Allow-Methods'] = 'POST,OPTIONS'
    resp.headers['Access-Control-Max-Age'] = '3600'
    return resp


@computers_router.post('/{computer_name}/toggle-status')
def toggle_status(computer_name: str, payload: dict, response: Response):
    # Closely follow Flask behavior including validation and fallback
    if not computer_name or not computer_name.strip():
        raise HTTPException(status_code=400, detail='Nome da máquina é obrigatório')

    if not payload or 'action' not in payload:
        raise HTTPException(status_code=400, detail='Campo "action" é obrigatório no body')

    action = payload.get('action', '').lower()
    if action not in ['enable', 'disable']:
        raise HTTPException(status_code=400, detail='Ação deve ser "enable" ou "disable"')

    use_powershell = payload.get('use_powershell', False)

    try:
        result = None
        try:
            if not use_powershell:
                result = ad_computer_manager.toggle_computer_status(computer_name, action)
            else:
                raise Exception('PowerShell requested')
        except Exception as ldap_err:
            # Fallback to PowerShell method
            try:
                result = ad_computer_manager.toggle_computer_status_powershell(computer_name, action)
            except Exception as ps_err:
                raise HTTPException(status_code=500, detail=f"Ambos os métodos falharam. LDAP: {ldap_err}. PowerShell: {ps_err}")

        # Update SQL cache if needed
        if result.get('success') and not result.get('already_in_desired_state'):
            try:
                is_enabled = action == 'enable'
                new_uac = result.get('operation', {}).get('new_status', {}).get('userAccountControl')
                sql_updated = sql_manager.update_computer_status_in_sql(computer_name, is_enabled, new_uac)
                result['cache_updated'] = sql_updated
            except Exception:
                # non-critical
                pass

        result['timestamp'] = datetime.now().isoformat() if 'datetime' in globals() else None
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@computers_router.get('/{computer_name}/warranty')
def get_computer_warranty(computer_name: str, force: bool = False):
    """Get warranty information for a specific computer by computer name.

    Behavior:
    - If ?force=true is not set, try returning cached warranty row from `dell_warranty` if present and not expired.
    - Otherwise call Dell API, normalize and save to DB, then return normalized `warranty_data`.
    """
    try:
        from ..managers import dell as _dell_module
        dell_api = getattr(_dell_module, 'dell_api', None)

        # First, get computer details to find service tag and id
        # Avoid selecting a potentially missing 'service_tag' column from the computers table
        q = "SELECT TOP 1 id, name FROM computers WHERE name = ?"
        rows = sql_manager.execute_query(q, params=(computer_name,))

        if not rows:
            raise HTTPException(status_code=404, detail=f'Computer {computer_name} not found')

        computer_id = rows[0].get('id')
        # Try to extract service tag from the computer name as fallback for schemas that don't store it
        service_tag = rows[0].get('service_tag') if 'service_tag' in rows[0] else None
        if not service_tag:
            service_tag = sql_manager.extract_service_tag_from_computer_name(rows[0].get('name'))
        if not service_tag:
            raise HTTPException(status_code=404, detail=f'Service tag not found for computer {computer_name}')

        # Try serving from database cache first (unless force)
        if not force:
            try:
                q2 = "SELECT * FROM dell_warranty WHERE computer_id = ?"
                dw = sql_manager.execute_query(q2, params=(computer_id,))
                if dw and len(dw) > 0:
                    row = dw[0]
                    # Determine if cache still valid
                    cache_expires = row.get('cache_expires_at')
                    last_error = row.get('last_error')
                    from datetime import datetime
                    now = datetime.now()
                    if cache_expires and cache_expires >= now and not last_error:
                        # Return DB row (normalize dates to ISO strings)
                        def _fmt(d):
                            try:
                                if d is None:
                                    return None
                                if isinstance(d, datetime):
                                    return d.isoformat()
                                return str(d)
                            except Exception:
                                return None

                        warranty_data = {
                            'computer_id': row.get('computer_id'),
                            'service_tag': row.get('service_tag'),
                            'warranty_start_date': _fmt(row.get('warranty_start_date')),
                            'warranty_end_date': _fmt(row.get('warranty_end_date')),
                            'warranty_status': row.get('warranty_status'),
                            'product_line_description': row.get('product_line_description'),
                            'system_description': row.get('system_description'),
                            'last_updated': _fmt(row.get('last_updated')),
                            'cache_expires_at': _fmt(row.get('cache_expires_at')),
                            'entitlements': row.get('entitlements'),
                            'last_error': row.get('last_error')
                        }
                        return JSONResponse(content=warranty_data)
            except Exception:
                # If DB check fails, log is done in sql_manager; continue to API path
                pass

        # If we reach here, call Dell API to get fresh info
        if dell_api is None:
            raise HTTPException(status_code=503, detail='Dell API client not available')

        res = dell_api.get_warranty_info(service_tag)
        if res is None or 'error' in res:
            code = res.get('code') if isinstance(res, dict) else None
            if code == 'SERVICE_TAG_NOT_FOUND':
                raise HTTPException(status_code=404, detail=res)
            elif code == 'AUTH_ERROR':
                raise HTTPException(status_code=401, detail=res)
            else:
                raise HTTPException(status_code=400, detail=res)

        # Normalize and persist processed data (best-effort)
        try:
            from ..routes.warranty_jobs import _convert_raw_to_processed
            processed = _convert_raw_to_processed(res, service_tag)
            try:
                sql_manager.save_warranty_to_database(computer_id, processed)
            except Exception:
                pass

            # Format response payload similar to frontend expectations
            def _fmt_date(d):
                try:
                    from datetime import datetime
                    if d is None:
                        return None
                    if isinstance(d, datetime):
                        return d.isoformat()
                    return str(d)
                except Exception:
                    return None

            import json
            ent = processed.get('entitlements')
            try:
                ent_list = json.loads(ent) if isinstance(ent, str) else (ent or [])
            except Exception:
                ent_list = []

            warranty_data = {
                'service_tag': processed.get('service_tag'),
                'product_line_description': processed.get('product_line_description'),
                'system_description': processed.get('system_description'),
                'warranty_start_date': _fmt_date(processed.get('warranty_start_date')),
                'warranty_end_date': _fmt_date(processed.get('warranty_end_date')),
                'warranty_status': processed.get('warranty_status'),
                'entitlements': ent_list,
                'last_updated': _fmt_date(processed.get('last_updated')),
                'cache_expires_at': _fmt_date(processed.get('cache_expires_at'))
            }

            return JSONResponse(content=warranty_data)
        except HTTPException:
            raise
        except Exception as e:
            # On unexpected errors, return raw Dell response as fallback
            try:
                return JSONResponse(content=res)
            except Exception:
                raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@computers_router.post('/{computer_name}/warranty/refresh')
def refresh_computer_warranty(computer_name: str):
    """Refresh warranty information for a specific computer"""
    try:
        from ..managers.dell import dell_api
        
        # Get computer details to find service tag
        # Avoid selecting a potentially missing 'service_tag' column from the computers table
        q = "SELECT TOP 1 id, name FROM computers WHERE name = ?"
        rows = sql_manager.execute_query(q, params=(computer_name,))

        if not rows:
            raise HTTPException(status_code=404, detail=f'Computer {computer_name} not found')

        computer_id = rows[0].get('id')
        service_tag = rows[0].get('service_tag') if 'service_tag' in rows[0] else None
        if not service_tag:
            service_tag = sql_manager.extract_service_tag_from_computer_name(rows[0].get('name'))
        if not service_tag:
            raise HTTPException(status_code=404, detail=f'Service tag not found for computer {computer_name}')
        
        # Get fresh warranty info from Dell API
        if dell_api is None:
            raise HTTPException(status_code=503, detail='Dell API client not available')
            
        res = dell_api.get_warranty_info(service_tag)
        if res is None or 'error' in res:
            # map some error codes to HTTP statuses
            code = res.get('code') if isinstance(res, dict) else None
            if code == 'SERVICE_TAG_NOT_FOUND':
                raise HTTPException(status_code=404, detail=res)
            elif code == 'AUTH_ERROR':
                raise HTTPException(status_code=401, detail=res)
            else:
                raise HTTPException(status_code=400, detail=res)
        
        # Save to database if successful and normalize response for frontend
        try:
            from ..routes.warranty_jobs import _convert_raw_to_processed
            processed = _convert_raw_to_processed(res, service_tag)
            # Try to persist processed info to DB, but don't fail the request if DB write fails
            try:
                sql_manager.save_warranty_to_database(computer_id, processed)
            except Exception:
                # Non-blocking: log is done inside sql_manager
                pass

            # Build a warranty_data object compatible with frontend expectations
            def _fmt_date(d):
                try:
                    if d is None:
                        return None
                    # If it's a datetime, return ISO; else return as-is
                    from datetime import datetime
                    if isinstance(d, datetime):
                        return d.isoformat()
                    return str(d)
                except Exception:
                    return None

            entitlements = processed.get('entitlements')
            try:
                import json
                if isinstance(entitlements, str):
                    ent_list = json.loads(entitlements)
                else:
                    ent_list = entitlements or []
            except Exception:
                ent_list = []

            warranty_data = {
                'service_tag': processed.get('service_tag'),
                # include both names used by different frontend places
                'product_line_description': processed.get('product_line_description'),
                'product_description': processed.get('product_line_description'),
                'system_description': processed.get('system_description'),
                'warranty_start_date': _fmt_date(processed.get('warranty_start_date')),
                'warranty_end_date': _fmt_date(processed.get('warranty_end_date')),
                'warranty_status': processed.get('warranty_status'),
                'entitlements': ent_list,
                'last_updated': _fmt_date(processed.get('last_updated')),
                'cache_expires_at': _fmt_date(processed.get('cache_expires_at')),
                # compatibility alias
                'expiration_date_formatted': _fmt_date(processed.get('warranty_end_date'))
            }

            return JSONResponse(content={"status": "success", "warranty_data": warranty_data})
        except HTTPException:
            raise
        except Exception as e:
            # If processing fails, still return the raw API response as fallback
            try:
                return JSONResponse(content={"status": "success", "warranty": res})
            except Exception:
                raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@computers_router.get('/{computer_name}/current-user')
def get_current_user(computer_name: str, force: bool = False):
    """Get current logged user for a specific computer"""
    try:
        # Get DHCP manager to reuse connection logic
        dhcp = require_dhcp_manager()
        
        # Try to connect using DHCP manager's connection method
        # Use the first available server
        servers = dhcp.all_servers
        if not servers:
            raise HTTPException(status_code=503, detail='No DHCP servers available for PowerShell connection')
        
        # Use the first server for the connection
        server = servers[0]
        client = dhcp.testar_conexao_servidor(server)
        
        if not client:
            return JSONResponse(content={
                'status': 'unreachable',
                'message': 'Could not connect to domain controller',
                'computer_name': computer_name
            })
        
        # PowerShell script to get current user
        script = f"""
        try {{
            # Verificar se é servidor ou DC primeiro
            $computer = Get-ADComputer -Identity "{computer_name}" -Properties OperatingSystem -ErrorAction Stop
            if ($computer.OperatingSystem -like "*Server*" -or $computer.Name -like "*DC*" -or $computer.Name -like "*SVR*") {{
                Write-Output "SKIP_SERVER_DC"
                exit
            }}
            
            # Tentar pegar usuário logado
            $user = (Get-CimInstance Win32_ComputerSystem -ComputerName "{computer_name}" -ErrorAction Stop).UserName
            $serial = (Get-CimInstance Win32_BIOS -ComputerName "{computer_name}" -ErrorAction Stop).SerialNumber
            
            if ($user) {{
                Write-Output "USER:$user"
            }} else {{
                Write-Output "USER:NONE"
            }}
            Write-Output "SERIAL:$serial"
            Write-Output "STATUS:OK"
        }} catch {{
            if ($_.Exception.Message -like "*RPC*" -or $_.Exception.Message -like "*network*" -or $_.Exception.Message -like "*timeout*") {{
                Write-Output "STATUS:OFFLINE"
            }} else {{
                Write-Output "STATUS:ERROR"
                Write-Output "ERROR:$($_.Exception.Message)"
            }}
        }}
        """
        
        # Execute script
        output, streams, had_errors = client.execute_ps(script)
        
        # Parse output
        lines = output.strip().split('\n') if output else []
        result = {
            'status': 'error',
            'computer_name': computer_name,
            'usuario_atual': None,
            'serial_number': None,
            'message': 'Unknown error'
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('USER:'):
                user = line.replace('USER:', '').strip()
                if user and user != 'NONE':
                    # Format user name: SNM\nome.sobrenome -> Nome Sobrenome
                    if '\\' in user:
                        domain, username = user.split('\\', 1)
                        if '.' in username:
                            first_name, last_name = username.split('.', 1)
                            formatted_user = f"{first_name.title()} {last_name.title()}"
                        else:
                            formatted_user = username.title()
                    else:
                        formatted_user = user.title()
                    result['usuario_atual'] = formatted_user
                    result['raw_user'] = user
                else:
                    result['usuario_atual'] = 'Nenhum usuário logado'
                    result['status'] = 'no_user'
            elif line.startswith('SERIAL:'):
                result['serial_number'] = line.replace('SERIAL:', '').strip()
            elif line.startswith('STATUS:'):
                status = line.replace('STATUS:', '').strip()
                if status == 'OK':
                    result['status'] = 'ok'
                elif status == 'OFFLINE':
                    result['status'] = 'unreachable'
                    result['message'] = 'Computer is offline or unreachable'
                elif status == 'ERROR':
                    result['status'] = 'error'
            elif line.startswith('ERROR:'):
                result['message'] = line.replace('ERROR:', '').strip()
            elif line == 'SKIP_SERVER_DC':
                result['status'] = 'skipped'
                result['message'] = 'Machine is server or domain controller - skipped'
                return JSONResponse(content=result, status_code=412)  # Precondition Failed
        
        # Update database if successful and not forced check
        if result['status'] in ['ok', 'no_user'] and not force:
            try:
                current_user = result.get('raw_user')
                if current_user:
                    # Get current data from database to check for changes
                    q = "SELECT TOP 1 usuario_atual, usuario_anterior FROM computers WHERE name = ?"
                    rows = sql_manager.execute_query(q, params=(computer_name,))
                    
                    if rows:
                        db_current = rows[0].get('usuario_atual')
                        db_previous = rows[0].get('usuario_anterior')
                        
                        # Update logic: if current user is different, move current to previous
                        if db_current != current_user:
                            update_q = "UPDATE computers SET usuario_atual = ?, usuario_anterior = ? WHERE name = ?"
                            sql_manager.execute_query(update_q, params=(current_user, db_current, computer_name))
                            result['updated'] = True
                            result['previous_user'] = db_current
                        else:
                            result['updated'] = False
                
                result['saved'] = True
            except Exception as e:
                result['saved'] = False
                result['save_error'] = str(e)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(content={
            'status': 'error',
            'message': str(e),
            'computer_name': computer_name
        }, status_code=500)


@computers_router.get('/{computer_name}/last-user')
def get_last_user(computer_name: str, days: int = 30):
    """Get last user information for a specific computer"""
    try:
        # This is a placeholder implementation
        # The actual last-user functionality would require Windows Event Log access
        # which is more complex and might need dedicated WinRM connections
        
        # For now, return the current user data from the database
        q = """
        SELECT TOP 1 
            usuario_atual, 
            usuario_anterior,
            last_logon_timestamp as last_logon
        FROM computers 
        WHERE name = ?
        """
        rows = sql_manager.execute_query(q, params=(computer_name,))
        
        if not rows:
            raise HTTPException(status_code=404, detail=f'Computer {computer_name} not found')
        
        row = rows[0]
        
        # Simulate last user response format
        result = {
            'success': True,
            'computer_name': computer_name,
            'last_user': row.get('usuario_atual') or row.get('usuario_anterior'),
            'last_logon_time': row.get('last_logon').isoformat() if row.get('last_logon') else None,
            'logon_type': 'Interactive',
            'search_method': 'database_cache',
            'total_time': 0.1
        }
        
        if not result['last_user']:
            result['success'] = False
            result['error'] = 'No user information found'
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'error': str(e),
            'computer_name': computer_name
        }, status_code=500)


@computers_router.post('/initialize-user-columns')
def initialize_user_columns():
    """Initialize user columns in the computers table if they don't exist"""
    try:
        # Check if columns exist and create them if they don't
        try:
            # Try to select the columns to check if they exist
            test_q = "SELECT TOP 1 usuario_atual, usuario_anterior FROM computers"
            sql_manager.execute_query(test_q)
            return JSONResponse(content={
                'status': 'success',
                'message': 'User columns already exist'
            })
        except Exception:
            # Columns don't exist, create them
            try:
                alter_q1 = "ALTER TABLE computers ADD usuario_atual NVARCHAR(255)"
                sql_manager.execute_query(alter_q1)
                
                alter_q2 = "ALTER TABLE computers ADD usuario_anterior NVARCHAR(255)"
                sql_manager.execute_query(alter_q2)
                
                return JSONResponse(content={
                    'status': 'success',
                    'message': 'User columns created successfully'
                })
            except Exception as e:
                return JSONResponse(content={
                    'status': 'error',
                    'message': f'Failed to create user columns: {str(e)}'
                }, status_code=500)
                
    except Exception as e:
        return JSONResponse(content={
            'status': 'error',
            'message': str(e)
        }, status_code=500)


@computers_router.post('/bulk-update-current-users')
def bulk_update_current_users():
    """Update current users for all computers (excluding servers and DCs)"""
    try:
        # Get all computers excluding servers and DCs
        q = """
        SELECT name 
        FROM computers 
        WHERE is_enabled = 1 
        AND is_domain_controller = 0
        AND (description NOT LIKE '%server%' OR description IS NULL)
        AND (name NOT LIKE '%DC%' AND name NOT LIKE '%SVR%')
        ORDER BY name
        """
        
        computers = sql_manager.execute_query(q)
        
        if not computers:
            return JSONResponse(content={
                'status': 'success',
                'message': 'No computers found to update',
                'total': 0,
                'processed': 0,
                'updated': 0,
                'errors': 0
            })
        
        total = len(computers)
        processed = 0
        updated = 0
        errors = 0
        results = []
        
        # Get DHCP manager for connections
        dhcp = require_dhcp_manager()
        servers = dhcp.all_servers
        
        if not servers:
            raise HTTPException(status_code=503, detail='No servers available for PowerShell connections')
        
        server = servers[0]
        
        for computer_row in computers:
            computer_name = computer_row['name']
            processed += 1
            
            try:
                # Get current user via the same method as individual endpoint
                client = dhcp.testar_conexao_servidor(server)
                
                if not client:
                    results.append({
                        'computer': computer_name,
                        'status': 'connection_failed',
                        'message': 'Could not connect to server'
                    })
                    errors += 1
                    continue
                
                # Same PowerShell script as individual endpoint
                script = f"""
                try {{
                    $computer = Get-ADComputer -Identity "{computer_name}" -Properties OperatingSystem -ErrorAction Stop
                    if ($computer.OperatingSystem -like "*Server*" -or $computer.Name -like "*DC*" -or $computer.Name -like "*SVR*") {{
                        Write-Output "SKIP_SERVER_DC"
                        exit
                    }}
                    
                    $user = (Get-CimInstance Win32_ComputerSystem -ComputerName "{computer_name}" -ErrorAction Stop).UserName
                    
                    if ($user) {{
                        Write-Output "USER:$user"
                    }} else {{
                        Write-Output "USER:NONE"
                    }}
                    Write-Output "STATUS:OK"
                }} catch {{
                    Write-Output "STATUS:OFFLINE"
                }}
                """
                
                output, streams, had_errors = client.execute_ps(script)
                lines = output.strip().split('\n') if output else []
                
                current_user = None
                status = 'error'
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('USER:'):
                        user = line.replace('USER:', '').strip()
                        if user and user != 'NONE':
                            current_user = user
                    elif line.startswith('STATUS:'):
                        status = line.replace('STATUS:', '').strip().lower()
                    elif line == 'SKIP_SERVER_DC':
                        status = 'skipped'
                        break
                
                if status == 'skipped':
                    results.append({
                        'computer': computer_name,
                        'status': 'skipped',
                        'message': 'Server or DC - skipped'
                    })
                    continue
                elif status == 'ok' and current_user:
                    # Update database
                    q_select = "SELECT TOP 1 usuario_atual, usuario_anterior FROM computers WHERE name = ?"
                    existing = sql_manager.execute_query(q_select, params=(computer_name,))
                    
                    if existing:
                        db_current = existing[0].get('usuario_atual')
                        
                        if db_current != current_user:
                            # User changed - update
                            q_update = "UPDATE computers SET usuario_atual = ?, usuario_anterior = ? WHERE name = ?"
                            sql_manager.execute_query(q_update, params=(current_user, db_current, computer_name))
                            updated += 1
                            results.append({
                                'computer': computer_name,
                                'status': 'updated',
                                'current_user': current_user,
                                'previous_user': db_current
                            })
                        else:
                            # No change
                            results.append({
                                'computer': computer_name,
                                'status': 'no_change',
                                'current_user': current_user
                            })
                    else:
                        # Computer not found in DB
                        results.append({
                            'computer': computer_name,
                            'status': 'not_found_in_db'
                        })
                        errors += 1
                else:
                    # Offline or no user
                    results.append({
                        'computer': computer_name,
                        'status': 'offline_or_no_user'
                    })
                
            except Exception as e:
                results.append({
                    'computer': computer_name,
                    'status': 'error',
                    'message': str(e)
                })
                errors += 1
            
            # Add small delay to avoid overwhelming the servers
            time.sleep(0.1)
        
        return JSONResponse(content={
            'status': 'success',
            'total': total,
            'processed': processed,
            'updated': updated,
            'errors': errors,
            'results': results[:50]  # Limit results to first 50 for response size
        })
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(content={
            'status': 'error',
            'message': str(e)
        }, status_code=500)
