# Modificações na Lógica de Usuário - Service Tag

## Resumo das Alterações

### Backend (FastAPI)

#### 1. SQL Manager (`backend/fastapi_app/managers/sql.py`)
- ✅ **Adicionados campos de usuário na query principal**:
  - `c.usuario_atual` 
  - `c.usuario_anterior`
- ✅ **Nova função `get_current_user_by_service_tag()`**:
  - Busca usuário usando service tag da máquina
  - Suporta prefixos conhecidos (SHQ, ESM, DIA, TOP, RUB, JAD, ONI, CLO)
  - Retorna dados completos do usuário e máquina

#### 2. API Router (`backend/fastapi_app/routes/computers.py`)
- ✅ **Novo endpoint**: `GET /api/computers/user-by-service-tag/{service_tag}`
- ✅ **Funcionalidade**:
  - Busca usuário atual pelo service tag
  - Retorna JSON com informações completas
  - Tratamento de erros apropriado

### Frontend (React)

#### 1. Serviço API (`frontend/src/services/api.js`)
- ✅ **Nova função**: `getCurrentUserByServiceTag(serviceTag)`
- ✅ **Mantida função original**: `getCurrentUserByComputerName(computerName)`

#### 2. Componente Computers (`frontend/src/pages/Computers.jsx`)
- ✅ **Adicionados campos de usuário**:
  - `currentUser`: mapeado de `computer.usuarioAtual`
  - `previousUser`: mapeado de `computer.usuarioAnterior`
- ✅ **Nova coluna na tabela**: "Usuário Atual"
- ✅ **Ordenação por usuário**: suporte a ordenar por `currentUser`
- ✅ **Busca aprimorada**: inclui usuários no texto de busca

### Estrutura de Dados

#### Backend Response Format:
```json
{
  "success": true,
  "service_tag": "C1WSB92",
  "computer_name": "DIAC1WSB92",
  "usuario_atual": "SNM\\joao.silva",
  "usuario_anterior": "SNM\\maria.santos",
  "description": "Desktop Dell",
  "last_logon": "2025-11-05T10:30:00",
  "message": "Usuário encontrado com sucesso"
}
```

#### Frontend Computer Object (enhanced):
```javascript
{
  id: 123,
  name: "DIAC1WSB92",
  os: "Windows 10",
  // ... outros campos existentes
  usuarioAtual: "SNM\\joao.silva",        // Do banco de dados
  usuarioAnterior: "SNM\\maria.santos",   // Do banco de dados
  currentUser: "SNM\\joao.silva",         // Mapeado para frontend
  previousUser: "SNM\\maria.santos"       // Mapeado para frontend
}
```

### Fluxo de Funcionamento

1. **Listagem de Computadores**:
   - Query SQL agora inclui campos `usuario_atual` e `usuario_anterior`
   - Frontend recebe e mapeia os dados automaticamente
   - Exibe usuário atual na nova coluna da tabela

2. **Busca por Service Tag**:
   - Endpoint: `/api/computers/user-by-service-tag/{service_tag}`
   - Extrai service tag do nome da máquina
   - Busca no banco usando padrões conhecidos
   - Retorna informações completas do usuário

### Como Usar

#### 1. Via Frontend:
- A coluna "Usuário Atual" aparece automaticamente na listagem
- Ordenação disponível clicando no cabeçalho da coluna
- Busca inclui nomes de usuários

#### 2. Via API Direta:
```bash
# Buscar usuário por service tag
curl http://10.15.2.19:42059/api/computers/user-by-service-tag/C1WSB92
```

#### 3. Via JavaScript:
```javascript
import { apiMethods } from './services/api'

// Buscar usuário por service tag
const result = await apiMethods.getCurrentUserByServiceTag('C1WSB92')
if (result.success) {
  console.log('Usuário atual:', result.usuario_atual)
}
```

### Scripts de Teste

#### 1. Teste Backend:
```bash
cd backend
python test_user_service_tag.py
```

#### 2. Teste API HTTP:
```bash
cd backend
python test_api_service_tag.py
```

### Dependências

- ✅ **Banco de dados**: Campos `usuario_atual` e `usuario_anterior` devem existir na tabela `computers`
- ✅ **Ambiente virtual**: Usar venv `api` para executar scripts Python
- ✅ **Service Tags**: Máquinas devem seguir padrão de nomenclatura com prefixos conhecidos

### Status

- ✅ Backend implementado
- ✅ Frontend implementado  
- ✅ Endpoints criados
- ✅ Testes preparados
- 🔄 Aguardando testes em ambiente

### Próximos Passos

1. **Ativar ambiente virtual `api`**
2. **Testar funcionamento do backend**
3. **Verificar se campos existem no banco**
4. **Testar interface do usuário**
5. **Ajustes conforme necessário**