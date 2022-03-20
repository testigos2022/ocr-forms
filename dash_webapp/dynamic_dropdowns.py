from pprint import pprint

import itertools
import json

import dash
import pandas
from dash import Dash, dcc, html, Input, Output, State, MATCH, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from tqdm import tqdm

from data_io.readwrite_files import (
    read_csv,
    write_jsonl,
    read_jsonl,
    write_json,
    read_json,
)
from misc_utils.utils import (
    get_dict_paths,
    get_val_from_nested_dict,
    set_val_in_nested_dict,
)

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

app.layout = html.Div(
    [
        html.Button("press me", id="add-filter", n_clicks=0),
        html.Div(id="dropdown-container", children=[]),
        html.Div(id="dropdown-container-output"),
        # dcc.Store(id={"type": "selection_state", "index": index}),
    ]
)

levels = ["dep", "mun", "pue", "mes"]

# departamento2municipio2puesto2mesa = {
#     f"dep{d}": {
#         f"mun{mu}": {f"pue{p}": [f"mes{mm}" for mm in range(3)] for p in range(3)}
#         for mu in range(3)
#     }
#     for d in range(3)
# }
departamento2municipio2puesto2mesa = read_json("dash_webapp/nested_dict.json")


@app.callback(
    Output("dropdown-container", "children"),
    Input("add-filter", "n_clicks"),
    State("dropdown-container", "children"),
)
def display_dropdowns(n_clicks, children):
    dropdowns = []
    for k in levels:
        new_dropdown = dcc.Dropdown(
            id={"type": "dropdown", "index": k},
            # options=[{"label": "none", "value": "none"}],
        )
        dropdowns.append(new_dropdown)
    return dropdowns


@app.callback(
    Output({"type": "dropdown", "index": ALL}, "options"),
    Input({"type": "dropdown", "index": ALL}, "value"),
)
def update_dropdown_options(dropdown_values: list[str]) -> list[dict[str, str]]:
    if dropdown_values is None:
        raise PreventUpdate
    #
    print(f"{dropdown_values=}")
    # trigger=dash.callback_context.triggered[0]
    # prob_id = trigger['prop_id'].replace(".value","")
    # if prob_id!=".":
    #     trigger_index=json.loads(prob_id)["index"]
    #     print(f"{trigger_index=}")
    #     # print(f"{dash.callback_context.inputs=}")
    options = []
    for level_idx, level in enumerate(levels):
        parent_value = dropdown_values[level_idx - 1] if level_idx > 0 else "colombia"
        if parent_value is not None:
            path = dropdown_values[:level_idx]
            print(f"{parent_value=},{path=}")

            v = get_val_from_nested_dict(departamento2municipio2puesto2mesa, path)
            options.append([{"label": k, "value": k} for k in v])
        else:
            options.append([])
    print(f"{options=}")
    return options


# def rec_dd():
#     return defaultdict(rec_dd)


def create_nested_dict_file():
    file = "/home/tilo/data/colombia_election_forms/cne-mesas.csv"
    # data=pandas.read_csv(file,sep=";",encoding="latin1").to_dict("records")
    # write_jsonl("data.jsonl",data)
    g = read_jsonl("data.jsonl")
    nested_dict = {}
    for d in tqdm(itertools.islice(g, 0, None)):
        key_path = [d["DEPARTAMENTO"], d["MUNICIPIO"], d["PUESTO"], d["MESA"]]
        set_val_in_nested_dict(nested_dict, key_path, None)
    write_json("nested_dict.json", nested_dict)


if __name__ == "__main__":
    # create_nested_dict_file()

    # pprint(nested_dict)
    # g=read_csv(file,delimiter=";",encoding="latin1")
    # for d in itertools.islice(g,0,10):
    #     print(d)
    # v=get_val_from_nested_dict(departamento2municipio2puesto2mesa,["dep0","mun0","pue0"])
    # print(f"{v=}")
    # dd={}
    # set_val_in_nested_dict(dd,["dep1","mun2","pue3"], "some-value")
    # print(f"{dd=}")
    # for k in range(3):
    #     key_path = ["dep1", "mun2", "pue4"]
    #     value = "another-value"
    #     set_val_in_nested_dict(dd, key_path, value)
    # print(f"{dd=}")
    app.run_server(debug=True)
