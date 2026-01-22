# Configuração do Ambiente

## Arquivos de Configuração

Este projeto usa arquivos template para evitar conflitos entre ambientes de desenvolvimento, homologação e produção.

### Arquivos que você precisa configurar:

1. **Backend Config**: Copie `backend/fastapi_app/config.py.template` para `backend/fastapi_app/config.py`
2. **Frontend Config**: Copie `frontend/vite.config.js.template` para `frontend/vite.config.js`  
3. **Startup Script**: Copie `start.bat.template` para `start.bat`

### Configurações necessárias:

#### config.py
- `AD_SERVER`: Servidor Active Directory
- `SQL_SERVER`: Servidor SQL Server
- `DELL_CLIENT_ID` e `DELL_CLIENT_SECRET`: Credenciais Dell API
- Outras credenciais específicas do ambiente

#### vite.config.js
- `apiTarget`: URL do backend (ex: http://10.15.3.30:42059)
- `allowedHosts`: Hosts permitidos para desenvolvimento
- `port`: Porta do frontend

#### start.bat
- Substitua `YOUR_BACKEND_PORT` e `YOUR_FRONTEND_PORT` pelas portas corretas
- Configure comandos de inicialização específicos do ambiente

## Nunca commite:
- `config.py` (contém credenciais)
- `vite.config.js` (contém IPs específicos do ambiente)  
- `start.bat` (contém configurações específicas do ambiente)
- Arquivos `.env*`

Esses arquivos estão no `.gitignore` para evitar conflitos entre ambientes.