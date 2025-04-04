import argparse

from pyrefine.shell_utils import cp
from pyrefine.simulation.sfe_cfg import SFEconfig


def update_sfe_cfg_parameter_keys(input_file_name="sfe_cfl_controller1.cfg", output_file_name="sfe_0.cfg"):
    param = {
        "caseName": "case_name",
        "caseCommentString": "case_comment_string",
        "Mach": "mach",
        "Reynolds": "reynolds",
        "Angle": "angle",
        "Yaw": "yaw",
        "weakBC": "weak_bc",
        "twod": "twod_mode",
        "first_order": "pure_galerkin",
        "freezeTurbulence": "freeze_turbulence",
        "conservativeRamping": "conservative_ramping",
        "relaxFlag": "relax_flag",
        "writeShockSensor": "write_shock_sensor",
        "writeDiscontinuity_Visc": "write_discontinuity_Visc",
        "# printLineSearch": "# print_line_search",
        "# printLineSearch_Max": "# print_line_search_max",
        "ompThreads": "omp_threads",
        "writeMatrix": "write_matrix",
        "relative": "relative_linear_residual_tolerance",
        "absolute": "absolute_linear_residual_tolerance",
        "timeAccuracy": "time_accuracy",
        "timeStep": "time_step",
        "nsubIterations": "nsub_iterations",
        "cflinit": "cfl_init",
        "cflmin": "cfl_min",
        "cflmax": "cfl_max",
        "QCR": "qcr",
        "QCR_BC": "qcr_bc",
        "RC": "rc",
        "DES": "des",
        "Cw": "cw",
        "DDES": "ddes",
        "# printColoring": "# print_coloring",
        "shock_ad": "smoothing",
        "preconditioner_monitor": "dynamic_reordering",
        "preconditioner_monitor_factor": "dynamic_reordering_growth_trigger",
        "preconditioner_monitor_write_matrix": "dynamic_reordering_write_linear_system",
        "preconditioner_monitor_prune_factor": "dynamic_reordering_prune_factor",
        "preconditioner_monitor_min_prune_width": "dynamic_reordering_min_prune_width",
    }

    # simpleSwitch -> number_of_smoothers = count of smoothers & smoother_type
    #    'simpleCoef': 'smoother_coef',
    #    'shock_clip': 'smoother_clip',
    #    'shock_beta': 'smoother_beta',
    #    'shock_exponent': 'smoother_exponent',
    # simpleCoef_dumb -> smoother_coef[i] , type == 1 uniform || type == 2 ramped
    # ryan_coeff -> smoother_coef[i] , type = 8 metric_pressure

    def smoother_param_update(key: str, old_key: str, new_key: str, value):
        found = False
        if key == old_key:
            found = True
            simple_coef = str(value).split("+")
            # print(f'found {old_key} {simple_coef} count = {len(simple_coef)}')
            for i, coef in enumerate(simple_coef):
                # print(f'{new_key}({i}) = {coef}')
                sfe_cfg_new[f"{new_key}({i})"] = coef
        return found

    input_file = input_file_name
    if input_file_name == output_file_name:
        input_file = f"{input_file_name}_deprecated"
        cp(input_file_name, input_file)

    sfe_cfg = SFEconfig(input_file)
    sfe_cfg_new = SFEconfig()

    smoother_coef = []
    smoother_count = 0

    for old_key, value in sfe_cfg.items():
        if old_key in param:
            sfe_cfg_new[param[old_key]] = value
        elif old_key == "simpleSwitch":
            smoother_coef = str(value).split("+")
            # print(f'found simpleSwitch {smoother_coef} count = {len(smoother_coef)}')
            smoother_count = len(smoother_coef)
            sfe_cfg_new["number_of_smoothers"] = smoother_count
            for i, coef in enumerate(smoother_coef):
                # print(f'smoother_type({i}) = {coef}')
                sfe_cfg_new[f"smoother_type({i})"] = coef
        elif smoother_param_update(old_key, "simpleCoef", "smoother_coef", value):
            pass
        elif smoother_param_update(old_key, "shock_clip", "smoother_clip", value):
            pass
        elif smoother_param_update(old_key, "shock_beta", "smoother_beta", value):
            pass
        elif smoother_param_update(old_key, "shock_exponent", "smoother_exponent", value):
            pass
        elif old_key == "simpleCoef_dumb":
            # print('checking for simpleCoef_dumb')
            if 1 in smoother_coef:
                idx = smoother_coef.index(1)
                sfe_cfg_new[f"smoother_coef({idx})"] = value
            if 2 in smoother_coef:
                idx = smoother_coef.index(2)
                sfe_cfg_new[f"smoother_coef({idx})"] = value
        elif old_key == "ryan_coeff":
            # print('checking for ryan_coeff')
            if 8 in smoother_coef:
                idx = smoother_coef.index(8)
                sfe_cfg_new[f"smoother_coef({idx})"] = value
        elif old_key == "preconditioner":
            if value == "lsiluk":
                sfe_cfg_new["linear_solver"] = "fgmres"
                sfe_cfg_new[old_key] = value
        else:
            sfe_cfg_new[old_key] = value

    sfe_cfg_new.write(output_file=output_file_name, force=True)


def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--input_file", default="sfe.cfg", help="Input SFE configuration file with deprecated parameter names."
    )
    parser.add_argument(
        "--output_file", default="sfe.cfg", help="Output SFE configuration file with current parameter names."
    )
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()

    update_sfe_cfg_parameter_keys(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
