# Montador de Pedido Futebol

App desktop Windows (Python 3 + CustomTkinter) que monta pastas de produção de pedidos de camisas
(arquivos `.tif`/`.tiff` de letras, números, logos e camisa completa). Copia arquivos, nunca move/apaga originais.
Idioma da UI e dos textos: português (BR).

## Comandos
- Rodar: `python app.py`
- Testes: `python -m pytest` (deps: `pip install -r requirements-dev.txt`)
- Gerar .exe: `build_exe.bat` -> `dist\Montador de Pedido Futebol.exe`

## Arquitetura (sem framework, camadas simples)
```
app.py                 entrada -> src/ui/main_window.py
src/models/            dataclasses/constantes (CartItem, CATEGORY_DEFINITIONS, BLANK_CATALOG)
src/services/          regra de negócio + I/O (catalog, cart, order, file, validation, backup, settings)
src/ui/                telas CustomTkinter (order_panel = painel principal, config_window, first_run_wizard)
src/utils/             helpers puros (path, json atômico, texto, nomes de arquivo)
tests/                 pytest, cobre utils/services (UI não é testada)
```
Fluxo: `OrderPanel` -> `CartService` (itens) -> `ValidationService` -> `FileService.generate` (copia p/ `PEDIDO_{n}_{cliente}_{data}` + `99_CONFERENCIA`).

## Regras / pegadinhas
- UI só orquestra; lógica nova vai em `services/` ou `utils/` (testável sem Tk).
- Categorias novas: adicionar em `CATEGORY_DEFINITIONS` e `FEATURE_DEFINITIONS` (`models/catalog_models.py`).
- `normalize_category` deixa a definição do código prevalecer; do JSON só vêm `folder_path`, `enabled`, `name`, `extensions`, `output_folder_name`.
- Chave do carrinho = (time, modelo, categoria, item casefold): mesmo item de times diferentes não funde.
- Caminhos usam `APP_ROOT` (`utils/path_utils.py`): no .exe é a pasta do executável, senão a raiz do repo.
- Salvar JSON sempre via `save_json` (escrita atômica).
- `config/catalogo.json`, `config/settings.json`, `data/pedidos_salvos`, `dist/`, `build/` NÃO vão pro git (dados locais da máquina).
  Modelo de config: `config/catalogo.example.json`. Sem catálogo, o app cria um em branco e abre o assistente.
- Schema do catálogo tem `schema_version`; mudança incompatível => migrar em `CatalogService.load_catalog`.

## Fluxo de trabalho
- Branch `main` estável; mudanças em `feature/<slug>` / `fix/<slug>`.
- Escrever teste antes de mexer em services/utils; rodar `python -m pytest` antes de commitar.
- Se mexer no empacotamento, testar o .exe (a pasta `assets` entra via `--add-data`).
