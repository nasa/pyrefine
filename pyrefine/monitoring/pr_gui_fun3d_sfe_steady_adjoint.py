#!/usr/bin/env python
import numpy as np
from typing import List

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from pyrefine.post_processing.fun3d_file_reader import Fun3dAdaptationSteadyHistoryReader
from pyrefine.post_processing.sfe_file_reader import SFEForwardHistoryReader
from pyrefine.post_processing.sfe_file_reader import SFEGoalOrientedHistoryReader
from pyrefine.post_processing.tecplot_writer import write_data_to_tecplot_format
from pyrefine.monitoring.plotly_base import PyrefinePlotly


class GuiAdaptHistory(PyrefinePlotly):
    def __init__(self):
        super().__init__()

        project_rootname = ''
        data_directory = ''
        self.load_data(data_directory, project_rootname)
        self.load_sfe_data(data_directory, project_rootname, 1)
        self.load_sfe_adjoint_data(data_directory, project_rootname)

        sections = []
        sections.append(self.create_case_information_div())
        sections.append(self.create_graphs_div())
        sections.append(self.create_sfe_tabs_outer_div())
        self.full_layout = html.Div(children=sections,
                                    style=dict(backgroundColor=self.background_color))

    def load_data(self, data_directory, project_rootname):
        self.data_directory = data_directory
        self.project_rootname = project_rootname
        self.reader = Fun3dAdaptationSteadyHistoryReader(data_directory, project_rootname)
        print(f'GUI: loaded data for {self.reader.number_of_meshes} meshes')

    def create_case_information_div(self):
        load_button = html.Button('Load', id='load_button', n_clicks=0)
        children = [html.H1('Case Information'),
                    self.create_case_information_input_table(),
                    load_button]
        div = html.Div(children=children, id='div_case_info')
        return div

    def create_case_information_input_table(self):
        return html.Table([html.Tr(
            [html.Td('Data directory:'),
             dcc.Input(
                id='data_directory', type='text', value='./Flow',
                style=dict(width='300%'))]),
            html.Tr(
            [html.Td('project_rootname:'),
             dcc.Input(
                id='project_rootname', type='text', value='om6ste',
                style=dict(width='300%'))])])

    def create_graphs_div(self):
        children = [self.generate_adaptation_history_div()]
        div = html.Div(children=children,
                       id='div_adapt_hist')
        return div

    def generate_adaptation_history_div(self):
        self.hist_fig = self.generate_adapt_history_fig()
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

    def generate_adapt_history_fig(self):
        fig = go.Figure()
        for variable_name, var_data in self.reader.final_hist_values.items():
            vis = None if variable_name == 'C_D' else 'legendonly'
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
        yaxis['title'] = 'Value'
        self.set_default_figure_layout(fig, xaxis, yaxis)
        return fig

    def export_adapt_history_tecplot(self, filename: str):
        self.reader.write_data_to_tec(filename)
        return f'Exported to {filename}'

# SFE details

    def load_sfe_data(self, data_directory, project_rootname, mesh_number):
        self.sfe_fwd_reader = SFEForwardHistoryReader(self.data_directory, self.project_rootname, mesh_number)
        print(f'GUI: loaded data for mesh number {self.sfe_fwd_reader.imesh}')

    def load_sfe_adjoint_data(self, data_directory, project_rootname):
        print('GUI: loading SFE adjoint data ...')
        self.sfe_goal_reader = SFEGoalOrientedHistoryReader(self.data_directory, self.project_rootname)
        print(f'GUI: loaded data for {self.sfe_goal_reader.number_of_adjoints} adjoints')

    def create_sfe_tabs_outer_div(self):
        div = html.Div(children=[html.H1('SFE data'),
                                 html.Div('Mesh number: '),
                                 dcc.Input(id='mesh_number',type='number',value=1),
                                 html.Div(children=[self.generate_plots_tabs()], id='sfe_detail_plots_tabs_div')],
                       id='sfe_detail_plots_div')
        return div

    def generate_plots_tabs(self):
        tabs = dcc.Tabs([dcc.Tab(label='Convergence', children=[self.generate_sfe_forward_convergence_div()],id='convergence_tab'),
                         dcc.Tab(label='Timing', children=[self.create_sfe_forward_timing_div()],id='timing_tab'),
                         dcc.Tab(label='Preconditioning', children=[self.generate_sfe_forward_preconditioning_div()],id='preconditioning_tab'),
                         dcc.Tab(label='Adjoint', children=[self.generate_sfe_adjoint_div()],id='adjoint_tab')
                         ])
        return tabs

    def generate_sfe_forward_convergence_div(self):
        self.sfe_fwd_convergence_fig = self.generate_sfe_forward_convergence_fig()
        export_html = self.generate_export_field_and_button(default_filename='sfe_forward_convergence.html',
                                                            button_txt='Export interactive figure',
                                                            id_base='sfe_forward_convergence_export_html')
        export_tec = self.generate_export_field_and_button(default_filename='sfe_forward_convergence.dat',
                                                           button_txt='Export tecplot data',
                                                           id_base='sfe_forward_convergence_export_tec')
        children = [html.H2('SFE Forward Convergence'),
                    dcc.Graph(figure=self.sfe_fwd_convergence_fig, id='sfe_fwd_convergence_graph')]
        children.extend(export_html)
        children.extend(export_tec)

        return html.Div(children=children)

    def create_sfe_forward_timing_div(self):
        self.timing_normalization_radio = self.create_timing_normalization_radio()
        self.normalized_timings = 'actual'
        div = html.Div(children=[html.H2('SFE Forward Solve Timing'),
                                html.Div('Timing format: '),
                                self.timing_normalization_radio,
                                html.Div(children=[self.generate_sfe_forward_timing_div()],id='timing_inner_div')]
                        )

        return div

    def generate_sfe_forward_timing_div(self):
        if self.normalized_timings == 'actual':
            self.sfe_timing_fig = self.generate_sfe_forward_timing_fig(self.sfe_fwd_reader.timing_data)
        else:
            self.sfe_timing_fig = self.generate_sfe_forward_timing_fig(self.sfe_fwd_reader.norm_timing_data)
        export_html = self.generate_export_field_and_button(default_filename='sfe_forward_timing.html',
                                                            button_txt='Export interactive figure',
                                                            id_base='sfe_forward_timing_export_html')
        export_tec = self.generate_export_field_and_button(default_filename='sfe_forward_timing.dat',
                                                           button_txt='Export tecplot data',
                                                           id_base='sfe_forward_timing_export_tec')

        children = [dcc.Graph(figure=self.sfe_timing_fig, id='sfe_fwd_timing_graph')]
        children.extend(export_html)
        children.extend(export_tec)

        return html.Div(children=children)

    def generate_sfe_forward_preconditioning_div(self):
        self.sfe_fwd_preconditioning_fig = self.generate_sfe_forward_preconditioning_fig()
        export_html = self.generate_export_field_and_button(default_filename='sfe_forward_preconditioning.html',
                                                            button_txt='Export interactive figure',
                                                            id_base='sfe_forward_preconditioning_export_html')
        export_tec = self.generate_export_field_and_button(default_filename='sfe_forward_preconditioning.dat',
                                                           button_txt='Export tecplot data',
                                                           id_base='sfe_forward_preconditioning_export_tec')
        children = [html.H2('SFE Forward Preconditioning'),
                    dcc.Graph(figure=self.sfe_fwd_preconditioning_fig, id='sfe_fwd_preconditioning_graph')]
        children.extend(export_html)
        children.extend(export_tec)

        return html.Div(children=children)

    def generate_sfe_adjoint_div(self):
        self.adjoint_hist_fig = self.generate_adjoint_history_fig()
        export_html = self.generate_export_field_and_button(default_filename='sfe_adjoint_hist.html',
                                                            button_txt='Export interactive figure',
                                                            id_base='sfe_adjoint_export_html')
        export_tec = self.generate_export_field_and_button(default_filename='sfe_adjoint_hist.dat',
                                                           button_txt='Export tecplot data',
                                                           id_base='sfe_adjoint_export_tec')
        children = [html.H2('SFE Adjoint History'),
                    dcc.Graph(figure=self.adjoint_hist_fig, id='adjoint_hist_graph')]
        children.extend(export_html)
        children.extend(export_tec)

        return html.Div(children=children)

    def generate_sfe_forward_convergence_fig(self):
        fig_sfe_fwd_convergence = make_subplots(specs=[[{"secondary_y": True}]])
        for variable_name, var_data in self.sfe_fwd_reader.residual_convergence_data.items():
            vis = None if variable_name in ['Density', 'X-momentum', 'Y-momentum', 'Z-momentum', 'Energy', 'Turbulence']  else 'legendonly'
            sec_y = True if variable_name in ['CL', 'CD']  else False
            fig_sfe_fwd_convergence.add_trace(
                go.Scatter(
                    x=np.arange(1, self.sfe_fwd_reader.number_of_steps+1, 1),
                    y=var_data,
                    mode='lines',
                    name=variable_name,
                    visible=vis,
                    hovertemplate=('Steps: %{x:d} <br>' +
                                   'Value: %{y:.3e}')
                ),
                secondary_y=sec_y
            )
        xaxis, yaxis = self.get_axis_settings()
        xaxis['title'] = 'Steps'
        yaxis['title'] = 'Residual'
        self.set_default_figure_layout(fig_sfe_fwd_convergence, xaxis, yaxis)
        fig_sfe_fwd_convergence.update_yaxes(type='log', secondary_y=False)
        fig_sfe_fwd_convergence.update_yaxes(title_text='CL, CD', secondary_y=True)
        return fig_sfe_fwd_convergence

    def generate_sfe_forward_timing_fig(self, timing_data):
        fig_sfe_timing = go.Figure()
        for variable_name, var_data in timing_data.items():
            vis = None if variable_name in ['RHS', 'LHS', 'Linear solve']  else 'legendonly'
            fig_sfe_timing.add_trace(
                go.Scatter(
                    x=np.arange(1, self.sfe_fwd_reader.number_of_steps+1, 1),
                    y=var_data,
                    mode='lines',
                    name=variable_name,
                    visible=vis,
                    hovertemplate=('Steps: %{x:d} <br>' +
                                   'Value: %{y:.3e}')
                )
            )
        xaxis, yaxis = self.get_axis_settings()
        xaxis['title'] = 'Steps'
        if self.normalized_timings == 'actual':
            yaxis['title'] = 'Time [s]'
        else:
            yaxis['title'] = 'Proportion of Total Step Time []'
        self.set_default_figure_layout(fig_sfe_timing, xaxis, yaxis)
        return fig_sfe_timing

    def generate_sfe_forward_preconditioning_fig(self):
        fig_sfe_fwd_preconditioning = make_subplots(specs=[[{"secondary_y": True}]])
        for variable_name, var_data in self.sfe_fwd_reader.preconditioner_data.items():
            vis = None if variable_name in ['Amplification', 'Rank']  else 'legendonly'
            sec_y = True if variable_name in ['Rank']  else False
            line_mode = 'markers' if variable_name in ['Rank']  else 'lines'
            fig_sfe_fwd_preconditioning.add_trace(
                go.Scatter(
                    x=np.arange(1, self.sfe_fwd_reader.number_of_steps+1, 1),
                    y=var_data,
                    mode=line_mode,
                    name=variable_name,
                    visible=vis,
                    hovertemplate=('Steps: %{x:d} <br>' +
                                   'Value: %{y:.3e}')
                ),
                secondary_y=sec_y
            )
        xaxis, yaxis = self.get_axis_settings()
        xaxis['title'] = 'Steps'
        yaxis['title'] = 'Amplification'
        self.set_default_figure_layout(fig_sfe_fwd_preconditioning, xaxis, yaxis)
        fig_sfe_fwd_preconditioning.update_yaxes(type='log', secondary_y=False)
        fig_sfe_fwd_preconditioning.update_yaxes(title_text='Rank', secondary_y=True)
        return fig_sfe_fwd_preconditioning

    def generate_adjoint_history_fig(self):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        for variable_name, var_data in self.sfe_goal_reader.adjoint_data.items():
            vis = None if variable_name in ['Final Linear', 'Amplification', 'Preconditioner Rank']  else 'legendonly'
            sec_y = True if variable_name in ['Preconditioner Rank']  else False
            line_mode = 'markers' if variable_name in ['Preconditioner Rank']  else 'lines'
            fig.add_trace(
                go.Scatter(
                    # x=self.reader.number_of_nodes,
                    x=np.arange(1, self.sfe_goal_reader.number_of_adjoints+1, 1),
                    y=var_data,
                    mode=line_mode,
                    name=variable_name,
                    visible=vis,
                    customdata=np.c_[np.arange(1, self.sfe_goal_reader.number_of_adjoints+1)],
                    hovertemplate=('Mesh: %{customdata[0]:n}<br>' +
                                   'Nodes: %{x:d} <br>' +
                                   'Value: %{y:.3e}')
                ),
                secondary_y=sec_y
            )
        xaxis, yaxis = self.get_axis_settings()
        xaxis['title'] = 'Mesh Numbers'
        yaxis['title'] = 'Value'
        self.set_default_figure_layout(fig, xaxis, yaxis)
        fig.update_yaxes(type='log', secondary_y=False)
        fig.update_yaxes(title_text='Preconditioner Rank', secondary_y=True)
        return fig

    def create_timing_normalization_radio(self):
        return dcc.RadioItems(
            options=[
                {'label': 'Actual', 'value': 'actual'},
                {'label': 'Normalized', 'value': 'norm'},
            ],
            id='timing_normalization_radio',
            value='actual'
        )

    def export_sfe_forward_convergence_tecplot(self, filename: str):
        self.sfe_fwd_reader.write_convergence_data_to_tec(filename)
        return f'Exported to {filename}'

    def export_sfe_forward_timing_tecplot(self, filename: str):
        self.sfe_fwd_reader.write_timing_data_to_tec(filename)
        return f'Exported to {filename}'

    def export_sfe_forward_preconditioning_tecplot(self, filename: str):
        self.sfe_fwd_reader.write_preconditioner_data_to_tec(filename)
        return f'Exported to {filename}'

    def export_sfe_adjoint_tecplot(self, filename: str):
        self.sfe_goal_reader.write_adjoint_data_to_tec(filename)
        return f'Exported to {filename}'

if __name__ == '__main__':
    ap = GuiAdaptHistory()
    app = dash.Dash()
    app.layout = ap.full_layout

    @app.callback(
        [Output('div_adapt_hist', 'children'),
        Output('sfe_detail_plots_div', 'children')],
        [Input('load_button', 'n_clicks')],
        [State('data_directory', 'value'),
         State('project_rootname', 'value')])
    def generate_adaptation_history_div(n_clicks, data_directory, project_rootname):
        if n_clicks > 0:
            ap.load_data(data_directory, project_rootname)
            ap.load_sfe_adjoint_data(data_directory, project_rootname)
        div1 = ap.generate_adaptation_history_div()
        div2 = ap.create_sfe_tabs_outer_div()
        return div1, div2

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

# SFE details

    @app.callback(
        [Output('convergence_tab', 'children'),
        Output('timing_inner_div', 'children'),
        Output('preconditioning_tab', 'children'),
        Output('adjoint_tab', 'children')],
        [Input('mesh_number', 'value')],
        [Input('timing_normalization_radio', 'value')])
    def create_sfe_tabs_outer_div(mesh_number, timing_normalization_radio):
        ap.normalized_timings = timing_normalization_radio
        if (mesh_number < 1):
            print(f'Mesh number must be an integer greater than 0')
            mesh_number = 1
        elif (mesh_number > ap.reader.number_of_meshes):
            print(f'Mesh number must be an integer less than {ap.reader.number_of_meshes+1}')
            mesh_number = ap.reader.number_of_meshes
        ap.load_sfe_data(ap.data_directory, ap.project_rootname, mesh_number)
        div1 = ap.generate_sfe_forward_convergence_div()
        div2 = ap.generate_sfe_forward_timing_div()
        div3 = ap.generate_sfe_forward_preconditioning_div()
        div4 = ap.generate_sfe_adjoint_div()
        return div1, div2, div3, div4

    @app.callback(
        Output('sfe_forward_timing_export_html_status', 'children'),
        [Input('sfe_forward_timing_export_html_button', 'n_clicks')],
        [State('sfe_forward_timing_export_html_input', 'value')])
    def export_sfe_forward_timing_html(n_clicks, filename):
        status = ''
        if n_clicks > 0:
            status = ap.export_fig_as_html(ap.sfe_timing_fig, filename)
        return status

    @app.callback(
        Output('sfe_forward_timing_export_tec_status', 'children'),
        [Input('sfe_forward_timing_export_tec_button', 'n_clicks')],
        [State('sfe_forward_timing_export_tec_input', 'value')])
    def export_sfe_forward_timing_tecplot(n_clicks, filename):
        status = ''
        if n_clicks > 0:
            status = ap.export_sfe_forward_timing_tecplot(filename)
        return status

    @app.callback(
        Output('sfe_forward_convergence_export_html_status', 'children'),
        [Input('sfe_forward_convergence_export_html_button', 'n_clicks')],
        [State('sfe_forward_convergence_export_html_input', 'value')])
    def export_sfe_forward_convergence_html(n_clicks, filename):
        status = ''
        if n_clicks > 0:
            status = ap.export_fig_as_html(ap.sfe_fwd_convergence_fig, filename)
        return status

    @app.callback(
        Output('sfe_forward_convergence_export_tec_status', 'children'),
        [Input('sfe_forward_convergence_export_tec_button', 'n_clicks')],
        [State('sfe_forward_convergence_export_tec_input', 'value')])
    def export_sfe_forward_convergence_tecplot(n_clicks, filename):
        status = ''
        if n_clicks > 0:
            status = ap.export_sfe_forward_convergence_tecplot(filename)
        return status

    @app.callback(
        Output('sfe_forward_preconditioning_export_html_status', 'children'),
        [Input('sfe_forward_preconditioning_export_html_button', 'n_clicks')],
        [State('sfe_forward_preconditioning_export_html_input', 'value')])
    def export_sfe_forward_preconditioning_html(n_clicks, filename):
        status = ''
        if n_clicks > 0:
            status = ap.export_fig_as_html(ap.sfe_fwd_preconditioning_fig, filename)
        return status

    @app.callback(
        Output('sfe_forward_preconditioning_export_tec_status', 'children'),
        [Input('sfe_forward_preconditioning_export_tec_button', 'n_clicks')],
        [State('sfe_forward_preconditioning_export_tec_input', 'value')])
    def export_sfe_forward_preconditioning_tecplot(n_clicks, filename):
        status = ''
        if n_clicks > 0:
            status = ap.export_sfe_forward_preconditioning_tecplot(filename)
        return status

    @app.callback(
        Output('sfe_adjoint_export_html_status', 'children'),
        [Input('sfe_adjoint_export_html_button', 'n_clicks')],
        [State('sfe_adjoint_export_html_input', 'value')])
    def export_sfe_adjoint_html(n_clicks, filename):
        status = ''
        if n_clicks > 0:
            status = ap.export_fig_as_html(ap.adjoint_hist_fig, filename)
        return status

    @app.callback(
        Output('sfe_adjoint_export_tec_status', 'children'),
        [Input('sfe_adjoint_export_tec_button', 'n_clicks')],
        [State('sfe_adjoint_export_tec_input', 'value')])
    def export_sfe_adjoint_tecplot(n_clicks, filename):
        status = ''
        if n_clicks > 0:
            status = ap.export_sfe_adjoint_tecplot(filename)
        return status

    app.run_server(debug=True, dev_tools_ui=True)
