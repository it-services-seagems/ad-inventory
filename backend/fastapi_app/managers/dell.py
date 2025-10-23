import requests
from datetime import datetime, timedelta, timezone
import logging
from ..config import DELL_CLIENT_ID, DELL_CLIENT_SECRET

logger = logging.getLogger(__name__)


class DellWarrantyAPI:
    def __init__(self):
        self.base_url = "https://apigtwb2c.us.dell.com"
        self.token = None
        self.token_expires_at = None

    def get_access_token(self):
        try:
            url = f"{self.base_url}/auth/oauth/v2/token"
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'grant_type': 'client_credentials',
                'client_id': DELL_CLIENT_ID,
                'client_secret': DELL_CLIENT_SECRET
            }
            response = requests.post(url, headers=headers, data=data, timeout=30)
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
                return True
            logger.warning('Dell token request failed: %s', response.status_code)
            return False
        except Exception:
            logger.exception('get_access_token failed')
            return False

    def is_token_valid(self):
        return (self.token and self.token_expires_at and datetime.now(timezone.utc) < self.token_expires_at)

    def ensure_valid_token(self):
        if not self.is_token_valid():
            return self.get_access_token()
        return True

    def _clean_service_tag(self, service_tag):
        """Remove known prefixes from service tag before sending to Dell API"""
        if not service_tag:
            return service_tag
            
        service_tag = service_tag.strip().upper()
        prefixes_to_remove = ['SHQ', 'DIA', 'TOP', 'RUB', 'ESM', 'ONI', 'JAD', 'CLO']
        
        for prefix in prefixes_to_remove:
            if service_tag.startswith(prefix) and len(service_tag) > len(prefix):
                cleaned_tag = service_tag[len(prefix):]
                logger.info(f"Removed prefix '{prefix}' from '{service_tag}' -> '{cleaned_tag}'")
                return cleaned_tag
                
        return service_tag

    def get_warranty_info(self, service_tag):
        if not service_tag or len(service_tag.strip()) < 4:
            return {'error': 'Service tag inválido', 'code': 'INVALID_SERVICE_TAG'}

        # Clean the service tag by removing known prefixes
        original_tag = service_tag.strip().upper()
        service_tag = self._clean_service_tag(original_tag)
        
        # Validate cleaned service tag
        if not service_tag or len(service_tag) < 4:
            return {'error': f'Service tag inválido após remoção do prefixo: {original_tag}', 'code': 'INVALID_SERVICE_TAG'}

        # Skip obvious non-Dell machines
        skip_patterns = ['APP', 'SRV', 'DC', 'SQL', 'SYNC', 'HUB', 'AV', 'FS', 'LIC', 'RM', 'RPA']
        for pattern in skip_patterns:
            if pattern in service_tag:
                return {'error': f'Service tag parece ser de servidor/aplicação, não Dell: {original_tag}', 'code': 'NOT_DELL_MACHINE'}

        if not self.ensure_valid_token():
            return {'error': 'Erro de autenticação com Dell API', 'code': 'AUTH_ERROR'}

        try:
            url = f"{self.base_url}/PROD/sbil/eapi/v5/asset-entitlements"
            headers = {'Authorization': f'Bearer {self.token}', 'Accept': 'application/json'}
            params = {'servicetags': service_tag}
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    return {'error': 'Service tag não encontrado', 'code': 'SERVICE_TAG_NOT_FOUND'}
                warranty_data = data[0]
                if warranty_data.get('invalid', False):
                    return {'error': 'Service tag inválido', 'code': 'INVALID_SERVICE_TAG'}

                # Simplified mapping
                latest_end_date = None
                entitlements = warranty_data.get('entitlements', [])
                for e in entitlements:
                    if e.get('endDate'):
                        try:
                            end_date = datetime.fromisoformat(e.get('endDate').replace('Z', '+00:00'))
                            if latest_end_date is None or end_date > latest_end_date:
                                latest_end_date = end_date
                        except Exception:
                            continue

                if latest_end_date:
                    now = datetime.now(timezone.utc)
                    status = 'Em garantia' if latest_end_date > now else 'Expirado'
                    data_expiracao = latest_end_date.strftime('%d/%m/%Y')
                else:
                    status = 'Desconhecido'
                    data_expiracao = None

                return {
                    'serviceTag': warranty_data.get('serviceTag', service_tag),
                    'serviceTagLimpo': warranty_data.get('serviceTag', service_tag),
                    # Provide standardized keys expected by processing code
                    'productLineDescription': warranty_data.get('productLineDescription', warranty_data.get('modelo', 'Não especificado')),
                    'systemDescription': warranty_data.get('systemDescription', ''),
                    # Keep older/localized keys for backward compatibility
                    'modelo': warranty_data.get('productLineDescription', warranty_data.get('modelo', 'Não especificado')),
                    'dataExpiracao': data_expiracao,
                    'status': status,
                    'entitlements': entitlements
                }
            elif response.status_code == 401:
                if self.get_access_token():
                    return self.get_warranty_info(service_tag)
                return {'error': 'Erro de autenticação', 'code': 'AUTH_ERROR'}
            elif response.status_code == 404:
                return {'error': 'Service tag não encontrado', 'code': 'SERVICE_TAG_NOT_FOUND'}
            else:
                return {'error': f'DELL_API_ERROR_{response.status_code}', 'code': 'DELL_API_ERROR'}
        except requests.exceptions.Timeout:
            return {'error': 'Timeout na conexão com Dell API', 'code': 'TIMEOUT_ERROR'}
        except Exception:
            logger.exception('get_warranty_info failed')
            return {'error': 'INTERNAL_ERROR', 'code': 'INTERNAL_ERROR'}

    def get_warranty_info_bulk(self, service_tags):
        if not isinstance(service_tags, (list, tuple)):
            return {'error': 'service_tags deve ser uma lista'}

        cleaned = [t.strip().upper() for t in service_tags if t and isinstance(t, str)]
        if not cleaned:
            return {}

        # Batch in 100s - call get_warranty_info per tag (simpler)
        results = {}
        for tag in cleaned:
            results[tag] = self.get_warranty_info(tag)
        return results


dell_api = DellWarrantyAPI()
