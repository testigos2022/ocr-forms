import json

import dash
from dash import Dash, dcc, html, Input, Output, State, MATCH, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

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

levels = ["a", "b", "c","d"]

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


# @app.callback(
#     Output("dropdown-container-output", "children"),
#     Input({"type": "dropdown", "index": ALL}, "value"),
# )
# def display_output(values):
#     return html.Div(
#         [
#             html.Div("Dropdown {} = {}".format(i + 1, value))
#             for (i, value) in enumerate(values)
#         ]
#     )


@app.callback(
    Output({"type": "dropdown", "index": ALL}, "options"),
    Input({"type": "dropdown", "index": ALL}, "value"),
    # State({"type": "dropdown", "index": ALL}, "value"),
)
def update_dropdown_options(dropdown_values:list[str])->list[dict[str,str]]:
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
    for level_idx, (value, level) in enumerate(zip(dropdown_values, levels)):
        parent_value=dropdown_values[level_idx-1] if level_idx>0 else "root"
        print(f"{parent_value=}")
        if parent_value is not None:
            path = f"{parent_value}"
            options.append(
                [
                    {"label": f"path: {path}, options: {k}", "value": f"{path}-{k}"}
                    for k in range(3)
                ]
            )
        else:
            options.append([])
    print(f"{options=}")
    return options


if __name__ == "__main__":
    app.run_server(debug=True)
