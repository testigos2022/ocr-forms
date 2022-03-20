import dash_bootstrap_components as dbc
from dash import html, dcc, dash, callback, Output, Input

app = dash.Dash(
                external_stylesheets=[dbc.themes.BOOTSTRAP],

                )

layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.Div(id="test-div")),
                dbc.Col(
                    dcc.Dropdown(
                        id="dropdown_a",
                        options=[
                            {"label": "a", "value": "a_value"},
                            {"label": "b", "value": "b_value"},
                        ],
                        # value="uncased",
                    ),
                    md=4,
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="dropdown_b",
                        # options=[{"label": "uncased", "value": "uncased"}],
                        # value="uncased",
                    ),
                    md=4,
                ),
            ]
        ),
    ]
)
app.layout = layout


@callback(Output("dropdown_b", "options"), Input("dropdown_a", "value"))
def update_dropdown_a_options(dropdown_a_value):
    if dropdown_a_value == "a_value":
        options = [{"label": f"a-{k}", "value": f"a-{k}"} for k in range(3)]
    elif dropdown_a_value == "b_value":
        options = [{"label": f"b-{k}", "value": f"b-{k}"} for k in range(6)]
    else:
        options = []
    return options


if __name__ == "__main__":
    app.run_server(debug=True, port=8477)
