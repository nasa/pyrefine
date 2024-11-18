import subprocess


class RefineBootstrap:
    def __init__(self, project_name, initial_complexity=100_000, initial_wall_spacing=None):
        """
        refine bootstrap driver to generate an initial mesh for refinement from a CSM file using ESP

        Parameters
        ----------
        project_name:
            str: The root name of the project (without any mesh numbers).
        initial_complexity:
            int: Initial mesh complexity.
        initial_wall_spacing:
            float: Initial wall spacing for the spalding option of refine.
        """
        self.project_name = project_name
        self.initial_complexity = initial_complexity
        self.initial_wall_spacing = initial_wall_spacing

    def run(self):
        """
        Run the bootstrap process. Expects serveESP to be in your PATH.
        """
        spalding_option1 = ""
        spalding_option2 = ""
        if self.initial_wall_spacing:
            spalding_option1 = f"--spalding {self.initial_wall_spacing}"
            spalding_option2 = f"--fun3d-mapbc {self.project_name}-vol.mapbc"

        subprocess.run(
            f"serveESP -batch {self.project_name}.csm > esp.txt \
        \nref bootstrap {self.project_name}.egads > bootstrap.txt \
        \nmpiexec refmpi adapt {self.project_name}-vol.meshb \
        {spalding_option1} {self.initial_complexity} -s 10 {spalding_option2} \
        -x {self.project_name}01.meshb -x {self.project_name}01.lb8.ugrid > initialize.txt \
        \ncp {self.project_name}-vol.mapbc {self.project_name}01.mapbc",
            shell=True,
        )
