#!/usr/bin/env python
import numpy as np
from typing import List

import plotly.graph_objects as go

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from pyrefine.post_processing.fun3d_file_reader import Fun3dAdaptationSteadyHistoryReader
from pyrefine.post_processing.tecplot_writer import write_data_to_tecplot_format
from pyrefine.monitoring.plotly_base import PyrefinePlotly


class GuiAdaptHistoryLive(PyrefinePlotly):
    def __init__(self):
        super().__init__()

        project_rootname = ''
        data_directory = ''
        variables = 'C_L, C_D'
        xlog = False
        ylog = False
        self.load_data(data_directory, project_rootname)

        sections = []
        sections.append(self.create_case_information_div())
        sections.append(self.create_graphs_div(variables, xlog, ylog))
        self.full_layout = html.Div(children=sections,
                                    style=dict(backgroundColor=self.background_color))

    def load_data(self, data_directory, project_rootname):
        self.project_rootname = project_rootname
        self.reader = Fun3dAdaptationSteadyHistoryReader(data_directory, project_rootname)
        print(f'GUI: loaded data for {self.reader.number_of_meshes} meshes')

    def create_case_information_div(self):
        start_button = html.Button('Start', id='start_button', n_clicks=0,
                                   style=dict(backgroundColor='lightblue',
                                              fontSize='24px'))
        children = [html.H1('Case Information'),
                    self.create_case_information_input_table(),
                    html.H3('Plot settings upon refresh:'),
                    self.create_plot_settings_input_table(),
                    start_button,
                    dcc.Interval(id='live_update_interval', interval=10*60*1000, n_intervals=0)]
        div = html.Div(children=children, id='div_case_info')
        return div

    def create_case_information_input_table(self):
        return html.Table([
            html.Tr([html.Td('Refresh interval in minutes:'),
                     dcc.Input(id='refresh_interval_input', type='number',
                               value=0.5, style=dict(width='30%')),
                     ]),
            html.Tr([html.Td('Data directory:'),
                     dcc.Input(id='data_directory', type='text',
                               value='./Flow', style=dict(width='300%'))
                     ]),
            html.Tr([html.Td('project_rootname:'),
                     dcc.Input(id='project_rootname', type='text',
                               value='om6ste', style=dict(width='300%'))
                     ]),
        ])

    def create_plot_settings_input_table(self):
        return html.Table([
            html.Tr([html.Td('Active variables:'),
                     dcc.Input(id='variable_list', type='text',
                               value='C_L, C_D', style=dict(width='300%'))
                     ]),
            html.Tr([html.Td('Use log scale:'),
                     dcc.Checklist(id='log_scale_checklist',
                                   options=[dict(label='X axis', value='xlog'),
                                            dict(label='Y axis', value='ylog')],
                                   labelStyle=dict(display='inline-block'))

                     ]),
        ])

    def create_graphs_div(self, variables, xlog, ylog):
        children = [self.generate_adaptation_history_div(variables, xlog, ylog)]
        div = html.Div(children=children,
                       id='div_adapt_hist')
        return div

    def generate_adaptation_history_div(self, variables, xlog, ylog):
        self.hist_fig = self.generate_adapt_history_fig(variables, xlog, ylog)
        export_html = self.generate_export_field_and_button(default_filename='adapt_hist.html',
                                                            button_txt='Export interactive figure',
                                                            id_base='hist_export_html')
        export_tec = self.generate_export_field_and_button(default_filename='adapt_hist.dat',
                                                           button_txt='Export tecplot data',
                                                           id_base='hist_export_tec')
        children = [html.H1('Adaptation History'),
                    dcc.Graph(figure=self.hist_fig, id='adapt_hist_graph')]
        children.extend(export_html)
        children.extend(export_tec)

        return html.Div(children=children)

    def convert_variable_string_to_list(self, variables: str):
        vars = variables.split(',')
        for i in range(len(vars)):
            vars[i] = vars[i].strip()
        return vars

    def generate_adapt_history_fig(self, variables, xlog, ylog):
        active_variable_list = self.convert_variable_string_to_list(variables)
        fig = go.Figure()
        for variable_name, var_data in self.reader.final_hist_values.items():
            vis = True if variable_name in active_variable_list else 'legendonly'
            fig.add_trace(
                go.Scatter(
                    x=self.reader.number_of_nodes,
                    y=var_data,
                    mode='lines+markers',
                    name=variable_name,
                    visible=vis,
                    customdata=np.c_[np.arange(1, self.reader.number_of_meshes+1)],
                    hovertemplate=('Mesh: %{customdata[0]:n}<br>' +
                                   'Nodes: %{x:d} <br>' +
                                   'Value: %{y:.3e}')
                )
            )
        xaxis, yaxis = self.get_axis_settings()
        xaxis['title'] = 'Number of Nodes'
        xaxis['type'] = 'log' if xlog else 'linear'
        yaxis['title'] = 'Value'
        yaxis['type'] = 'log' if ylog else 'linear'
        self.set_default_figure_layout(fig, xaxis, yaxis)
        return fig

    def export_adapt_history_tecplot(self, filename: str):
        self.reader.write_data_to_tec(filename)
        return f'Exported to {filename}'


if __name__ == '__main__':
    ap = GuiAdaptHistoryLive()
    app = dash.Dash()
    app.layout = ap.full_layout

    @app.callback(
        Output('live_update_interval', 'interval'),
        [Input('start_button', 'n_clicks')],
        [State('refresh_interval_input', 'value')])
    def set_live_update_interval(n_clicks, interval_min):
        interval_ms = 10 * 60 * 1000
        if n_clicks > 0:
            interval_ms = interval_min * 60 * 1000
        return interval_ms

    @app.callback(
        Output('div_adapt_hist', 'children'),
        [Input('live_update_interval', 'n_intervals')],
        [State('data_directory', 'value'),
         State('project_rootname', 'value'),
         State('variable_list', 'value'),
         State('log_scale_checklist', 'value')])
    def generate_history_div(n_intervals, data_directory, project_rootname, variables, log_scale):
        if n_intervals > 0:
            ap.load_data(data_directory, project_rootname)
        xlog = False
        ylog = False
        if log_scale is not None:
            xlog = True if 'xlog' in log_scale else False
            ylog = True if 'ylog' in log_scale else False
        return ap.generate_adaptation_history_div(variables, xlog, ylog)

    @app.callback(
        Output('hist_export_html_status', 'children'),
        [Input('hist_export_html_button', 'n_clicks')],
        [State('hist_export_html_input', 'value')])
    def export_adapt_history_html(n_clicks, filename):
        status = ''
        if n_clicks > 0:
            status = ap.export_fig_as_html(ap.hist_fig, filename)
        return status

    @app.callback(
        Output('hist_export_tec_status', 'children'),
        [Input('hist_export_tec_button', 'n_clicks')],
        [State('hist_export_tec_input', 'value')])
    def export_adapt_history_tecplot(n_clicks, filename):
        status = ''
        if n_clicks > 0:
            status = ap.export_adapt_history_tecplot(filename)
        return status

    app.run_server(debug=True, dev_tools_ui=True)
