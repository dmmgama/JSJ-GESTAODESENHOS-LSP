# JSJ Gestão de Desenhos

**Sistema para gestão de legendas de desenhos de estruturas em AutoCAD**

Inclui:
- **App Streamlit** para gestão de CSVs/dados
- **Script LISP** para AutoCAD (gestão de legendas)

---

## 🚀 Instalação Rápida

### Pré-requisitos

1. **Python 3.10+** - [Descarregar Python](https://www.python.org/downloads/)
   - ✅ Durante a instalação, marcar **"Add Python to PATH"**

2. **AutoCAD** (para usar o LISP)

---

### Passo 1: Criar Ambiente Virtual

Abrir PowerShell/Terminal na pasta do projeto:

```powershell
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# OU no CMD:
.\.venv\Scripts\activate.bat
```

### Passo 2: Instalar Dependências

```powershell
pip install -r requirements.txt
```

### Passo 3: Executar a App

```powershell
streamlit run app.py
```

A app abre automaticamente no browser em `http://localhost:8501`

---

## 📁 Estrutura do Projeto

```
├── app.py                    # App principal Streamlit
├── csv_importer.py           # Módulo importador CSV
├── json_importer.py          # Módulo importador JSON
├── db.py                     # Módulo base de dados
├── lpp_builder.py            # Construtor de LPP
├── utils.py                  # Utilitários
├── create_template.py        # Criar templates
├── config.toml               # Configurações
├── csv_config.json           # Config do CSV
├── JSJ-GestaoDesenhosV41.lsp # Script LISP para AutoCAD
├── Iniciar_App.bat           # Atalho Windows para iniciar
├── requirements.txt          # Dependências Python
├── data/                     # Dados de entrada
│   ├── csv_in/               # CSVs para importar
│   └── json_in/              # JSONs para importar
└── output/                   # Ficheiros gerados
```

---

## 🖥️ Usar a App Streamlit

A app permite:
- Importar CSVs exportados do AutoCAD
- Visualizar e editar dados de legendas
- Gerar ficheiros para reimportar no AutoCAD
- Construir LPP (Lista de Peças de Projeto)

### Iniciar Rápido (Windows)

Duplo clique em `Iniciar_App.bat`

---

## 🏗️ Usar o LISP no AutoCAD

### Carregar o LISP

1. No AutoCAD: `APPLOAD` (ou Menu → Tools → Load Application)
2. Selecionar `JSJ-GestaoDesenhosV41.lsp`
3. Clicar "Load"

### Comando Principal

```
GESTAODESENHOSJSJ
```

### Menu Principal
| Opção | Função |
|-------|--------|
| **1** | Modificar Legendas (emitir revisões, alterar campos) |
| **2** | Exportar Lista (CSV/JSON) |
| **3** | Importar Lista (atualizar do CSV) |
| **4** | Gerir Layouts (criar/ordenar) |
| **9** | Navegar pelos layouts |
| **0** | Sair |

---

## 📋 Dependências Python

```
streamlit
pandas
openpyxl
sqlalchemy
unidecode
```

---

## ⚡ Troubleshooting

### "python não é reconhecido"
- Reinstalar Python com **"Add Python to PATH"** marcado
- Ou adicionar manualmente ao PATH do sistema

### "streamlit não é reconhecido"
- Certificar que o ambiente virtual está ativado (`.venv`)
- Reinstalar: `pip install streamlit`

### Porta 8501 ocupada
```powershell
streamlit run app.py --server.port 8502
```

---

## 📄 Licença

Projeto interno JSJ Engenharia.
