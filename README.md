# QualiSUS  v1.1.0

![Ambiente de Homologação](https://img.shields.io/badge/Status-Homologação-amber?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-Flask_%7C_Tailwind-blue?style=for-the-badge)

O **QualiSUS** é uma plataforma de elite desenvolvida para a gestão inteligente de saúde ocupacional dos servidores públicos do Estado de Pernambuco. O sistema combina uma arquitetura robusta em Flask com uma experiência de usuário (UX/UI) de nível enterprise, focada em alta densidade de dados e clareza operacional.

---

## 🚀 Principais Funcionalidades

### 1. Dashboard de Alta Fidelidade
- Visualização de KPIs críticos com **Sparklines SVG**.
- Indicadores de tendência em tempo real.
- Micro-interações táteis para feedback instantâneo.

### 2. Navegação Enterprise (Sidebar v4)
- **Collapsible Sidebar**: Alternância entre estados expandido e mini para otimização de espaço.
- **Persistência de Estado**: Memória local da preferência de visualização do usuário.
- **Active Glow System**: Destaque visual sofisticado para o item de navegação ativo.

### 3. Grid de Alta Precisão
- Listagens otimizadas com **Zebra Striping** e separadores suaves.
- Estados de hover responsivos para escaneabilidade rápida de grandes volumes de dados.
- Badge system semântico para status de atendimento e vínculos.

### 4. Centro de Comando (Search v2)
- Interface de busca global ativada via `CMD+K`.
- Backdrop em glassmorphism para foco total na pesquisa.

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia |
| :--- | :--- |
| **Backend** | Python 3.13 + Flask |
| **Frontend Styling** | Tailwind CSS (Enterprise Custom Palette) |
| **Icons** | Lucide Icons |
| **Data Export** | SheetJS (Excel Generation) |
| **UX Patterns** | Glassmorphism, CSS Transitions, Flexbox/Grid Layouts |

---

## 📁 Estrutura do Projeto

```bash
├── backend/            # API, Blueprints e Lógica de Negócio
│   ├── app/            # Core da aplicação Flask
│   └── routes/         # Definição modular de rotas
├── front/              # Frontend e Templates Jinja2
│   ├── src/templates/  # Estrutura HTML/Jinja
│   └── static/         # Assets, CSS e JS Frontend
├── db/                 # Scripts de migração e modelos de dados
├── deploy/             # Configurações de container e scripts de lançamento
└── docs/               # Documentação técnica detalhada
```

---

## ⚙️ Configuração Rápida

1. **Dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ambiente**:
   Configure o arquivo `.env` baseado no `.env.example`.

3. **Execução**:
   ```bash
   python backend/app/app.py
   ```

---

## 🛡️ Gestão de Ambientes

O sistema possui indicadores visuais dinâmicos no cabeçalho e na sidebar para distinguir entre o ambiente de **Homologação** (para testes e validações) e o ambiente de **Produção**.

---

© 2026 QualiSUS Enterprise - Gestão de Estado.

