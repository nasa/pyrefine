import glob
import math
import os
import subprocess


class AFLR3:
    def __init__(self, project_name, bl_type="manual"):
        """
        AFLR3 driver for boundary layer extrusion and hybrid mesh generation

        Parameters
        ----------
        project_name:
            str: The root name of the project (without any mesh numbers).
        bl_type:
            str: Boundary layer type: 'manual' (default), 'yplus', or 're_cell'. The latter options require FUN3D v14.2+.
        """

        #: str: The root name of the project (without any mesh numbers).
        self.project_name = project_name

        #: str: Boundary layer type: 'manual' (default), 'yplus', or 're_cell'.
        self.bl_type = bl_type

        #: int: Initial wall spacing in wall units based on bl_type ('yplus' or 're_cell').
        self.bl_initial = 1

        #: int: Full boundary layer height in wall units based on bl_type ('yplus' or 're_cell').
        self.bl_full = 1000
        if self.bl_type == "re_cell":
            self.bl_full = 3000

        #: str: Additional arguments passed into aflr3
        self.aflr_extra_args = ""

        #: int: Number of initial layers with constant spacing (aflr3 default = 5)
        self.n_constant_layers = 0

        #: float: Maximum boundary layer geometric growth rate (aflr3 default = 1.5).
        self.max_blgr = 1.2

        #: float: Boundary layer geometric growth acceleration rate (aflr3 default = 1.05).
        #:  This is set to 1.0 by default to enforce constant growth rate.
        self.bldr = 1.0

        # determine boundary conditions for AFLR3
        file_path = f"./{project_name}01.mapbc"
        with open(file_path, "r") as f:
            lines = f.readlines()
            bc_ids = ""
            bc_flags = ""
            iteration = 0
            for line in lines:  # Loop for assigning BCs to surfaces from *mapbc file
                iteration += 1
                words = line.split()
                if iteration == 2:  # Update bc_id list with current surface
                    bc_ids = f"{words[0]}"
                else:
                    bc_ids = f"{bc_ids},{words[0]}"

                if "4000" in line:  # Identifies viscous wall BCs
                    if iteration == 2:
                        bc_flags = "-1"
                    else:
                        bc_flags = f"{bc_flags},-1"
                elif "5000" in line or "5050" in line:  # Identifies farfield BCs
                    if iteration == 2:
                        bc_flags = "0"
                    else:
                        bc_flags = f"{bc_flags},0"
                else:  # Identifies all other BCs and assigns them as BL intersecting surface
                    if iteration == 2:
                        bc_flags = "2"
                    else:
                        bc_flags = f"{bc_flags},2"

                if iteration == 1:  # First Line in mapbc (identifies number of BC's)
                    bc_ids = ""
                    bc_flags = ""

        #: str: Boundary condition IDs for AFLR3
        self.BC_IDs = bc_ids
        #: str: Boundary condition flags for AFLR3
        self.BC_Flags = bc_flags

        #: int: Number of layers
        self.nbl = 0

        #: float: Initial wall spacing in grid units
        self.initial_wall_spacing = None

    def run(self):
        """
        Run the AFLR3 process.
        """

        # Compute initial spacing and number of layers:
        self.compute_spacing()

        # Remove the aflr, hybrid folders if they exist
        subprocess.run("rm -r aflr/ hybrid/", shell=True)

        # Find the latest *.lb8.ugrid file from Flow folder
        list_of_files = glob.glob("./Flow/*.meshb")
        latest_file = max(list_of_files, key=os.path.getctime)
        desired_file = latest_file.replace(".meshb", ".lb8.ugrid")
        subprocess.run(f"ref translate {latest_file} {desired_file}", shell=True)

        # Make a new directory and load the necessary ugrid file to begin aflr3 process:
        subprocess.run(
            f"mkdir aflr \
        \ncp {desired_file} ./aflr/{self.project_name}.lb8.ugrid",
            shell=True,
        )
        os.chdir("./aflr")

        # Print important input parameters for AFLR3:
        print("\nAFLR3 Highlighted BL Inputs:")
        print(
            f"Initial Wall Spacing, Number of Layers, BL Growth Rate = {self.initial_wall_spacing}, {self.nbl}, {self.max_blgr}"
        )

        # Load and run AFLR3 in aflr directory with the copied ugrid:
        subprocess.run(
            f"ugc {self.project_name}.lb8.ugrid {self.project_name}_boundary.lb8.ugrid -b \
        \naflr3 -i {self.project_name}_boundary.lb8.ugrid -ogrid {self.project_name}_aflr3.lb8.ugrid -blc -blds \
        {self.initial_wall_spacing} -nbl {self.nbl} -BC_IDs {self.BC_IDs} -Grid_BC_Flag {self.BC_Flags} \
        -blpr -bli {self.n_constant_layers} -bldr {self.bldr} \
        -blrm {self.max_blgr} {self.aflr_extra_args} -tmp $PWD -log",
            shell=True,
        )
        # if AFLR3 fails, try again with extra arguments
        with open(f'{self.project_name}_aflr3.aflr3.log') as aflr3_log:
            if 'ERROR' in aflr3_log.read():
                self.aflr_extra_args = '-mrecbm 2 -mrecbdw 1 -mrec4 1 -mdsblf 0 -mdf 2 -mdfb 1 -mbv_mode 1'
                print(f"\nAFLR3 had errors, trying again with different aflr_extra_args = '{self.aflr_extra_args}'\n")
                subprocess.run(
                    f'aflr3 -i {self.project_name}_boundary.lb8.ugrid -ogrid {self.project_name}_aflr3.lb8.ugrid -blc -blds \
                {self.initial_wall_spacing} -nbl {self.nbl} -BC_IDs {self.BC_IDs} -Grid_BC_Flag {self.BC_Flags} \
                -blpr -bli {self.n_constant_layers} -bldr {self.bldr} \
                -blrm {self.max_blgr} {self.aflr_extra_args} -tmp $PWD -log', shell=True, )

        # Create new directory for hybrid run:
        # MJO: Check for aflr.*b8.ugrid, aflr 16.32.50 didnt take -ogrid
        aflr_ugrid = glob.glob(self.project_name+"_aflr3.*b8.ugrid")[0]
        if aflr_ugrid.split(".")[-2] == 'b8':
            subprocess.run(
                f"ugc {aflr_ugrid} {self.project_name}_aflr3.lb8.ugrid \
            \nrm {aflr_ugrid}",
                shell=True,)
        subprocess.run(
            f"mkdir ../hybrid \
        \ncp {self.project_name}_aflr3.lb8.ugrid ../hybrid/{self.project_name}.lb8.ugrid \
        \ncp ../*.nml* ../hybrid \
        \ncp ../tdata ../hybrid \
        \ncp ../*species* ../hybrid \
        \ncp ../*kinetic* ../hybrid \
        \ncp ../*ascent_actions* ../hybrid \
        \ncp ../{self.project_name}01.mapbc ../hybrid \
        \ncd ../hybrid \
        \nref translate {self.project_name}.lb8.ugrid {self.project_name}01.meshb",
            shell=True,
        )
        os.chdir("../hybrid")

    def compute_spacing(self):
        if self.bl_type == "manual":
            if self.nbl == 0 or self.initial_wall_spacing is None:
                raise ValueError(
                    """nbl and/or initial_wall_spacing undefined.
                                    Please manually specify these or call compute_spacing_from_reynolds_number."""
                )
            return  # these parameters were computed elsewhere
        # Grab latest flow*out file from initial refine run
        list_of_files = glob.glob("./Flow/flow*out")
        latest_file = max(list_of_files, key=os.path.getctime)
        file_path = f"{latest_file}"
        with open(file_path, "r") as f:
            lines = f.readlines()
            iterations = 0
            for line in lines:
                if self.bl_type == "re_cell":
                    if "Max Cell Reynolds Number, Distance" in line:
                        iterations += 1
                        words = line.split()
                        max_plus = words[6]
                        max_plus = float(max_plus[:-1])  # removes comma from value/converts to number
                        distance = float(words[7])
                if self.bl_type == "yplus":
                    if "Max y+, Distance" in line:
                        iterations += 1
                        words = line.split()
                        max_plus = words[4]
                        max_plus = float(max_plus[:-1])  # removes comma from value/converts to number
                        distance = float(words[5])
        if iterations == 1:
            self.initial_wall_spacing = distance / max_plus * self.bl_initial
            self.nbl = math.ceil(math.log(self.bl_full / self.bl_initial * (self.max_blgr - 1) + 1, self.max_blgr) - 1)
        else:
            raise ValueError(
                """Could not find yplus or re_cell output.
                                Please output boundary data with these options in FUN3D (requires v14.2+)."""
            )

    def compute_spacing_from_reynolds_number(self, re, bl_initial=None, bl_full=None):
        if bl_initial:  # initial yplus
            self.bl_initial = bl_initial
        if bl_full:  # bl height in terms of yplus
            self.bl_full = bl_full
        cf = 0.026 * re ** (-1.0 / 7.0)
        self.initial_wall_spacing = self.bl_initial * math.sqrt(2.0 / cf) / re
        self.nbl = math.ceil(math.log(self.bl_full / self.bl_initial * (self.max_blgr - 1) + 1, self.max_blgr) - 1)
