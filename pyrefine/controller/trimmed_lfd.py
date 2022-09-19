import numpy as np
import f90nml

from .monitor_quantity import ControllerMonitorQuantity

class ControllerTrimmedLfdDriver(ControllerMonitorQuantity):
    def __init__(self, project_name, pbs=None):
        """
        A controller to double the complexity of the adaptation based on the
        convergence of the LFD-computed flutter dynamic pressure.

        Parameters
        ----------
        project_name: str
            The root name of the project (without any mesh numbers)
        pbs: :class:PBS
            PBS queue helper
        """
        super().__init__(project_name, pbs)

        #: float: a relaxation factor for updating the trim state based on the old trim state
        #:        a value of 1.0 takes 100% of the current trim state
        #:        a value of 0.0 takes 100% of the old trim state
        self.trim_relaxation_factor = 1.0

        #: List[str]: extensions of files to remove at the end of each adaptation cycle
        #             if save_all is True
        self.file_extensions_to_cleanup_every_step += ["-distance.solb.names", ".forces_imaginary",
                                                       "_hist.dat_imaginary", "_massoud_body1.dat",
                                                       "_modal_structure.restart"]

    def _retrieve_flutter_history(self):
        raise NotImplementedError('Trimmed LFD controller must implement a method to read the flutter history')

    def get_monitored_quantities_for_step(self, istep):
        raise NotImplementedError('Trimmed LFD controller must implement a monitor quantity')

    def update_inputs(self, istep):
        raise NotImplementedError('Trimmed LFD controller must implement a trim updating scheme')


class ControllerPapaTrimmedLfdDriver(ControllerTrimmedLfdDriver):
    def __init__(self, project_name, pbs=None):
        """
        A controller to double the complexity of the adaptation based on the
        convergence of the LFD-computed flutter dynamic pressure, for PAPA
        (pitch and plunge) configurations

        Parameters
        ----------
        project_name: str
            The root name of the project (without any mesh numbers)
        pbs: :class:PBS
            PBS queue helper
        """
        super().__init__(project_name, pbs)

        #: float: torsional constant of the pitch spring
        self.torsional_constant = 1.

    def _retrieve_flutter_history(self):
        f = open('history.dat', 'r')
        contents = f.readlines()

        rho_flutter = np.zeros(len(contents)-1, dtype=float)
        vel_flutter = np.zeros(len(contents)-1, dtype=float)

        for i in range(len(rho_flutter)):
            line = contents[i+1].split()
            rho_flutter[i] = float(line[3])
            vel_flutter[i] = float(line[4])

        q_flutter = .5*rho_flutter*vel_flutter**2
        f.close()
        return q_flutter

    def get_monitored_quantities_for_step(self, istep):
        q_flutter = self._retrieve_flutter_history()
        values = [q_flutter[-1]]
        return values

    def update_inputs(self, istep):
        # read the original (set) AoA, from outside the Flow folder
        nml = f90nml.read('../fun3d.nml')
        AoA_rigid = nml['reference_physical_properties']['angle_of_attack']

        if istep > 1:
            # read the wing chord and the wing area
            chord = nml['force_moment_integ_properties']['x_moment_length']
            area = nml['force_moment_integ_properties']['area_reference']

            # read the AoA at the previous istep
            istep_m1 = istep - 1
            nml = f90nml.read(f'fun3d.nml_steady{istep_m1:02d}')
            AoA_previous = nml['reference_physical_properties']['angle_of_attack']

            # read the pitching moment at the previous istep
            f = open(f'{self.project_name}{istep_m1:02d}.forces', 'r')
            contents = f.read().split()
            Cmy = float(contents[-13])

            # read the flutter Q at the previous step
            q_flutter = self._retrieve_flutter_history()
            q_flutter = q_flutter[-1]

            # compute pitch rotation needed for equilibrium
            theta = (180/np.pi)*(q_flutter*chord*area*Cmy)/self.torsional_constant
            AoA_new = AoA_rigid + theta

            # relaxation of AoA
            AoA = self.trim_relaxation_factor*AoA_new + (1-self.trim_relaxation_factor)*AoA_previous
            print('Old AoA was', AoA_previous, ', current AoA computed as',
                  AoA_new, ', with relaxation next AoA will be set to', AoA)

        else:
            AoA = AoA_rigid

        # write AoA to disk
        f = open('aoa.txt', 'w')
        f.write(f'{AoA}\n')
        f.close()
