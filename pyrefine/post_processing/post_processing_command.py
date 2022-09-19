from abc import ABC, abstractmethod


class PostProcessingCommand(ABC):

    def __init__(self, target):
        """
        A simple implementation of the command design pattern

        Overide this abstract base class to add new commands to the
        Fun3d reader.

        Parameters
        ----------
        target: :class:`~pyrefine.post_processing.fun3d_file_reader.Fun3dAdaptationSteadyHistoryReader`
            Store a reference to the receiver or target of the command
        """
        self.target = target

    @abstractmethod
    def execute(self) -> None:
        """
        The bulk of the post-processing work should be stored in this method.
        """
        pass
