Standard Adaptation Driver
--------------------------

The pyrefine class driving an adaptation is :class:`~pyrefine.adaptation_driver.AdaptationDriver`.
The driver uses three components to perform the actions of an adaptation.

The components and their default objects are:

* refine - :class:`~pyrefine.refine.multiscale.RefineMultiscale` - performs the metric computation, the generation of new meshes, and interpolation of the solution onto the new mesh.

* simulation - :class:`~pyrefine.simulation.fun3d.SimulationFun3dFV` - performs the set of simulations associated with a given adaptation cycle.

* controller - :class:`~pyrefine.controller.basic.ControllerBasic` - updates any input files at the start of an adaptation cycle, schedules the complexity for the mesh adaptation step, and cleans up files at the end of cycle.

Running an adaptation
---------------------
To set up an adaptation, the user must instantiate an adaptation driver by providing a project name and a pbs handler.
Next, the user can customize the driver components (see :ref:`customizing_driver`).
The user then can call the `set*` methods of the driver of components.
Once the problem is fully set up, the adaptation is started with the `run` method of the adaptation driver.

PBS Job submission
------------------
pyrefine uses the pbs4py PBS class to handle PBS job submission.
You set the information about the queue limits, the compute node description, profile filename for the environment, etc. that you want to be for each PBS job.
Once you've set up launcher, the adaptation driver will then it to create and submit PBS jobs.
See the `pbs4py documentation <https://nasa.github.io/pbs4py/>`_ for details about customizing the PBS job launcher.
You can individually set the `pbs` settings in each component
to control which queue each phase uses, which profile to source for the environment etc.
If an individual pbs handler is not specified for a given component, the default value of `pbs` is `None` which means it will get the `pbs` launcher from the adaptation driver.
That is, if none of the components are given individual `pbs` members, the default behavior is that all the components will use the same `pbs`, which is the one provided to the adaptation driver.


.. _customizing_driver:

Customizing the Driver Components
---------------------------------
There are two ways to customize the adaptation driver.

The first approach is to instantiate the adaptation driver and override one or more of the components.

.. code-block:: python

   pbs = PBS.k4()
   project = 'om6'
   driver = AdaptationDriver(project,pbs)
   driver.simulation = SimulationFun3dSFE(project):

The second approach is to create a new adaptation driver that subclasses :class:`~pyrefine.adaptation_driver.AdaptationDriver` and overrides the
components in the constructor. This approach may be more appropriate if there are multiple components that need the same input data so that the new driver class can have a single method that sets the input data to the components.

Stopping the Adaptation
-----------------------
The phases of the adaptation each check for an output file to indicate successful
completion of that step. If the file is not found, the adaptation will stop.

For early termination, there is also an option to stop the adaptation early with
a `stop.dat` file in the root directory of the adaptation. The `stop.dat` file should
contain the adaptation cycle that you wish to stop at.


Continue running after logging out of ssh
-----------------------------------------

Often times, you'd like to start the adaptation script and have it continue after
logging out of an ssh session. The detached sessions with the `screen` command is one option, but the simplest
approach is to use `nohup`. For example, `nohup ./adapt.py > adapt.out 2>&1 &`

Automated file cleanup during the adaptation
--------------------------------------------
When many meshes are run in an adaptation process, the number and size of the input and output files can grow rapidly.
To avoid filling up disk space with files that are no longer needed, pyrefine's controllers will clean up unneeded files
at the end of each adaptation cycle.
See :ref:`controller` for methods to select the files to be deleted or saved, how often
restart information is saved, or how to turn off the clean up operations completely.

Driver Class
------------
.. automodule:: pyrefine.adaptation_driver

.. autoclass:: AdaptationDriver
   :members:
