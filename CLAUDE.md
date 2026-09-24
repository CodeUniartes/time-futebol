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
contracts/             schemas JSON compartilhados com o site/API (pedido, catálogo público); ver contracts/README.md
docs/                  roadmap.md (visão dos sub-projetos), superpowers/specs e plans
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
- Schema do catálogo tem `schema_version` (hoje 2); mudança incompatível => migrar em `CatalogService.migrate` (em memória; grava na próxima gravação).
- Camisa tem `season` (int, opcional) e `active` (padrão true; só controla o que o site publica). Nome de exibição: `model_display_name`; menus usam `model_menu_map`. ID novo de camisa inclui o ano.
- `save_catalog` grava `updated_at` (UTC, `Z`): é o `catalog_version` que o site vai carregar nos pedidos.
- Pedido do site: `order_import_service.parse_site_order(dict, catalog)` (não sabe a origem do JSON) devolve `payload` para `OrderPanel.load_order_payload` + `warnings`. Ignora campos desconhecidos; contrato em `contracts/order.schema.json`.
- Contratos: campo novo opcional mantém `schema_version`; o que quebra leitor antigo cria versão nova. `config/site.json` (tokens) é ignorado pelo git.
- UI: cores e fontes só vêm de `src/ui/theme.py` (marca em `docs/brand.md`). Botão de ação = grafite; botão que conclui (gerar/salvar) = `cta` (laranja escuro). Nunca texto branco sobre o laranja puro `#F47726` (2,8:1). `tests/test_theme.py` guarda os contrastes.
- Roadmap (SP2 publicar catálogo, SP3 API, SP4 site, SP5 painel de prévia, SP6 upload): `docs/roadmap.md`.

## Fluxo de trabalho
- Branch `main` estável; mudanças em `feature/<slug>` / `fix/<slug>`.
- Escrever teste antes de mexer em services/utils; rodar `python -m pytest` antes de commitar.
- Se mexer no empacotamento, testar o .exe (a pasta `assets` entra via `--add-data`).
