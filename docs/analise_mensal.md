# Documentação - Tela de Análise Mensal

## Visão Geral

A **Análise Mensal** é um wizard interativo de 12 etapas (etapas 0-11) queauxilia o usuário a realizar uma análise financeira mensal completa do seu negócio. O wizard é basado na planilha "Analise mensal SuccessWay.xlsx".

---

## Estrutura do Wizard (12 Etapas)

```
Etapa 0: Introdução
Etapa 1: Mês e Ano da Análise
Etapa 2: Capacidade Produtiva
Etapa 3: Faturamento
Etapa 4: Clientes do Mês
Etapa 5: Gastos Variáveis
Etapa 6: Custo das Mercadorias
Etapa 7: Custos Fixos
Etapa 8: Margem de Segurança
Etapa 9: Resultado Final
Etapa 10: Avaliação
Etapa 11: Fim
```

---

## Descrição de Cada Etapa

### Etapa 0 - Introdução
- Apresenta o propósito do wizard
- Botão para iniciar a análise

### Etapa 1 - Mês e Ano
- **Campos**: Mês (select), Ano (number)
- **Validação**: Ambos obrigatórios

### Etapa 2 - Capacidade Produtiva
- **Campos**: Capacidade máxima de produção/venda
- **Validação**: Número > 0

### Etapa 3 - Faturamento
- **Campos**: Faturamento total do mês
- **Validação**: Número >= 0

### Etapa 4 - Clientes
- **Campos**: Quantidade de clientes atendidos
- **Validação**: Número >= 0

### Etapa 5 - Gastos Variáveis
- **Campos**: Lista de gastos que variam conforme a produção/venda
- **Exemplos**: Matéria-prima, comissões, insumos
- **Validação**: Pelo menos 1 item ou valor zero

### Etapa 6 - Custo das Mercadorias
- **Campos**: Custo total das mercadorias vendidas
- **Validação**: Número >= 0

### Etapa 7 - Custos Fixos
- **Campos**: Lista de custos fixos mensais
- **Exemplos**: Aluguel, salários, contas fixas
- **Validação**: Lista não vazia

### Etapa 8 - Margem de Segurança
- **Campos**: Percentual de margem de segurança desejada
- **Validação**: Percentual válido (0-100)

### Etapa 9 - Resultado Final
- Mostra cálculos automáticos:
  - Lucro Bruto = Faturamento - Custo Mercadorias
  - Margem Bruta = (Lucro Bruto / Faturamento) * 100
  - Lucro Líquido = Lucro Bruto - Custos Fixos - Gastos Variáveis
  - Margem Líquida = (Lucro Líquido / Faturamento) * 100
  - Ponto de Equilíbrio = Custos Fixos / (1 - (Custo Mercadorias / Faturamento))
  - Margem de Segurança = ((Faturamento - Ponto de Equilíbrio) / Faturamento) * 100

### Etapa 10 - Avaliação
- Mensagens motivacionais condicionais (F1-F11)
- baseadas nas métricas calculadas
- Botão "Não corresponde" abre modal de comparação

### Etapa 11 - Fim
- Mensagem de conclusão
- Botões para nova análise ou ver histórico

---

## Arquivos Necessários para Implementação

### Backend (Python/Flask)

| Arquivo | Descrição |
|---------|-----------|
| `app/models/analise_mensal.py` | Modelo SQLAlchemy da tabela `analise_mensal` |
| `app/models/custo_fixo.py` | Modelo SQLAlchemy da tabela `custo_fixo` |
| `app/routes/analise_mensal.py` | Rotas da API e páginas |
| `migrations/versions/criar_tabelas_analise_mensal.py` | Migration do banco |

### Frontend (HTML/JS)

| Arquivo | Descrição |
|---------|-----------|
| `app/templates/analise_mensal.html` | Wizard principal |
| `app/templates/analise_mensal_lista.html` | Lista de análises salvas |

### Banco de Dados

**Tabela: `analise_mensal`**
```sql
CREATE TABLE analise_mensal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    ano INTEGER NOT NULL,
    capacidade INTEGER,
    faturamento DECIMAL(12,2),
    quant_clientes INTEGER,
    custo_mercadorias DECIMAL(12,2),
    margem_seguranca DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Tabela: `custo_fixo`**
```sql
CREATE TABLE custo_fixo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analise_mensal_id INTEGER NOT NULL,
    nome VARCHAR(100) NOT NULL,
    valor DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (analise_mensal_id) REFERENCES analise_mensal(id) ON DELETE CASCADE
);
```

---

## API Endpoints

### Páginas HTML
- `GET /analise-mensal` - Wizard de nova análise
- `GET /analise-mensal/lista` - Lista de análises salvas
- `GET /analise-mensal/edit/{id}` - Editar análise existente

### API REST
- `GET /analise-mensal/api/available-years` - Anos com análises salvas
- `GET /analise-mensal/api/listar` - Lista análises do usuário
- `GET /analise-mensal/api/{id}` - Retorna análise específica
- `POST /analise-mensal/api/salvar` - Salva nova análise
- `PUT /analise-mensal/api/{id}` - Atualiza análise existente
- `DELETE /analise-mensal/api/{id}` - Remove análise

### API Dados Básicos
- `GET /basic-data/api/latest` - Retorna últimos dados básicos (para %lucro_ideal)

---

## Variáveis JavaScript Principais

### Estado do Wizard
```javascript
let currentStep = 0;           // Etapa atual (0-11)
let analiseData = {};          // Dados da análise
let isEditMode = false;         // Modo edição
let editAnaliseId = null;       // ID da análise em edição
```

### Dados por Etapa
```javascript
// Etapa 1
analiseData.mes = 3;           // Março
analiseData.ano = 2024;         // 2024

// Etapa 2
analiseData.capacidade = 100;

// Etapa 3
analiseData.faturamento = 50000;

// Etapa 4
analiseData.quant_clientes = 45;

// Etapa 5
analiseData.gastos = [
    { nome: 'Frete', valor: 500 },
    { nome: 'Embalagens', valor: 300 }
];

// Etapa 6
analiseData.custo_mercadorias = 25000;

// Etapa 7
analiseData.custosFixos = [
    { nome: 'Aluguel', valor: 2000 },
    { nome: 'Salários', valor: 8000 }
];

// Etapa 8
analiseData.margem_seguranca = 10;  // Percentual
```

### Funções Principais
- `showStep(n)` - Mostra etapa n
- `nextStep()` - Avança para próxima etapa
- `prevStep()` - Volta para etapa anterior
- `validarEtapa(n)` - Valida dados da etapa n
- `salvarAnalise()` - Salva análise no banco
- `carregarAnaliseExistente(id)` - Carrega análise para edição
- `atualizarCalculosParciais()` - Atualiza cálculos em tempo real
- `excluirAnalise(id)` - Exclui análise

---

## Mensagens Condicionais (F1-F11)

As mensagens F1-F11 aparecem na Etapa 10 baseadas em condições:

| Código | Condição | Mensagem |
|--------|----------|----------|
| F1 | Faturamento < capacidade * 0.3 | "Mesmo com capacidade disponível, seu faturamento está baixo. Vamos avaliar..." |
| F2 | Crescimento cliente > 20% | "Parabéns! Você está conquistando mais clientes..." |
| F3 | Margem bruta < 30% | "Sua margem bruta está baixa. Considere ajustar preços..." |
| F4 | Margem líquida > 20% | "Excelente! Sua margem líquida está acima de 20%..." |
| F5 | Ponto equilíbrio > 70% faturamento | "Cuidado! Seu ponto de equilíbrio está muito alto..." |
| F6 | Margem segurança < 10% | "Sua margem de segurança está baixa. Preço de venda pode estar inadequado..." |
| F7 | Margem segurança > 30% | "Boa margem de segurança! Você tem folga para momentos difíceis..." |
| F8 | Sem custos fixos | "Cadastre seus custos fixos para uma análise precisa..." |
| F9 | %Lucro_ideal não cadastrado | "Para uma análise completa, cadastre seu lucro ideal nos Dados Básicos..." |
| F10 | Lucro líquido negativo | "Ops! Seu lucro líquido está negativo. Vamos identificar onde melhorar..." |
| F11 | Clique em "Não corresponde" | Abre modal para comparar valores |

---

## Dependências Externas

### Para calcular %Lucro_ideal (F9)
O wizard busca o valor de `porcentagem_lucro` da tabela `dados_basicos`:
```python
@router.get("/basic-data/api/latest")
async def get_latest_basic_data(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    dados = db.query(BasicData).filter(...).first()
    return {"porcentagem_lucro": dados.porcentagem_lucro}
```

---

## Configurações de Navegação

### Rotas Escondidas (comentadas nos templates)
- Dados Básicos (`/basic-data/new`)
- Diagnóstico (`/diagnostico`)
- Simulador de Cenário (`/simulador`)
- Calculadora de Preços (`/calculadora`)
- Importância dos Meses (`/importancia-meses`)
- Produto (`/produto`)

### Botões de Navegação por Página

**Dashboard (`/dashboard`):**
- Índice (sempre visível)
- Análise Mensal (centro)

**Análise Mensal (`/analise-mensal`):**
- Índice, Histórico

**Lista de Análises (`/analise-mensal/lista`):**
- Índice, Nova Análise

---

## Pontos de Atenção na Implementação

1. **Ordem das Rotas FastAPI**: Rotas específicas devem vir ANTES de rotas com parâmetros
   ```python
   # CORRETO
   @router.get("/analise-mensal/api/available-years")
   @router.get("/analise-mensal/api/listar")
   @router.get("/analise-mensal/api/{analise_id}")
   
   # ERRADO - "available-years" seria interpretado como {analise_id}
   @router.get("/analise-mensal/api/{analise_id}")
   @router.get("/analise-mensal/api/available-years")  # NUNCA SERÁ ATINGIDO
   ```

2. **Credentials em Fetch**: Toda requisição fetch deve incluir `credentials: 'include'`
   ```javascript
   fetch(url, {
       method: 'POST',
       credentials: 'include',  // OBRIGATÓRIO para autenticação
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify(data)
   });
   ```

3. **Validação por Etapa**: Cada etapa tem sua própria função de validação

4. **Null Checks**: Funções como `atualizarCalculosParciais()` e `atualizarF11()` precisam verificar se os elementos existem antes de acessá-los

5. **Transição de Etapas**: Ao editar, `showStep(1)` inicia na etapa do mês (não na avaliação)

---

## Fluxo de Dados

```
[Usuário preenche wizard]
        ↓
[Validação por etapa]
        ↓
[salvarAnalise()]
        ↓
[POST /analise-mensal/api/salvar]
        ↓
[Backend: cria analise_mensal + custos_fixos]
        ↓
[Resposta de sucesso]
        ↓
[Redireciona para lista OU mostra step 11]
```

---

## Editando uma Análise Existente

1. Usuário acessa `/analise-mensal/lista`
2. Clica no botão "Editar" de uma análise
3. Sistema carrega dados via `GET /analise-mensal/api/{id}`
4. Função `carregarAnaliseExistente()` popula o wizard
5. `showStep(1)` inicia na etapa do mês
6. Após editar, `salvarAnalise()` usa `PUT` com ID existente

---

## Personalização de Mensagens

As mensagens motivacionais estão no HTML (linhas ~1400-1500 do `analise_mensal.html`).
Para adicionar/editar mensagens, procure a função `atualizarF11()`.

---

## Testes Recomendados

1. Criar análise do zero (todas as etapas)
2. Salvar e verificar na lista
3. Editar análise existente
4. Excluir análise (com modal de confirmação)
5. Navegação entre etapas (próximo/anterior)
6. Validação de campos obrigatórios
7. Mensagens condicionais appearing corretamente
8. Cálculos automáticos na etapa 9
9. Verificar autenticação (sem cookies deve retornar 401)
