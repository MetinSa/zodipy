from collections.abc import Iterable as Iterable_
from typing import Optional, Union, Iterable
from datetime import datetime

import astropy.units as u
import numpy as np

from zodipy import models
from zodipy import _coordinates as coords
from zodipy import _integration as integ
from zodipy import simulation 

class Zodi:
    """Interface for simulating the Zodiacal emission.
    
    Currently, Zodipy only supports simulation the instantaneous Zodiacal 
    emission. It is possible that TOD simulations will be implemented in 
    future.
    """

    def __init__(
        self, 
        observer : Optional[str] = 'L2',
        observation_times : Optional[Union[Iterable[datetime], datetime]] = None,
        model : Optional[str] = 'planck 2018',
        integration_config : Optional[str] = 'default'
    ) -> None:
        """Initializing the zodi interface.

        The geometric setup of the simulation, the IPD model, and the 
        integration configuration used when integrating up the emission 
        are all configured here in the initialization of the Zodi object.
        
        Parameters
        ----------
        observer : str, optional
            The observer. Defaults to L2.
        observation_times : Iterable, optional
            The times of observation. Must be an iterable containing 
            `datetime` objects. Defaults to a single observeration at the 
            current time.
        model : str, optional
            String representing the Interplanteary dust model used in the 
            simulation. Available options are 'planck 2013', 'planck 2015',
            and 'planck 2018'. Defaults to 'planck 2018'.
        integration_config : str, optional
            String representing the integration config which determins the 
            integration details used in the simulation. Available options
            'default', and 'high'. Defaults to 'default'.
        """

        if observation_times is None:
            observation_times = [datetime.now().date()]
        elif not isinstance(observation_times, Iterable_): 
            observation_times = [observation_times]

        observer_locations = [
            coords.get_target_coordinates(observer, time) 
            for time in observation_times
        ]
        earth_locations = [
            coords.get_target_coordinates('earth', time) 
            for time in observation_times
        ]

        if 'planck' in model.lower():
            if '2013' in model:
                model = models.PLANCK_2013
            elif '2015' in model:
                model = models.PLANCK_2015
            elif '2018' in model:
                model = models.PLANCK_2018
            else:
                raise ValueError(
                    "Available models are: 'planck 2013', 'planck 2015', and "
                    "'planck 2018'"
                )
        
        if integration_config == 'default':
            integration_config = integ.DEFAULT
        elif integration_config == 'high':
            integration_config = integ.HIGH
        else:
            raise ValueError(
                "Available configs are: 'default' and 'high'"
            )

        self.simulation_strategy = simulation.InstantaneousStrategy(
            model, integration_config, observer_locations, earth_locations
        )

    def get_emission(
        self, 
        nside: int, 
        freq: Union[float, u.Quantity], 
        coord: Optional[str] = 'G',
        return_comps: Optional[bool] = False
    ) -> np.ndarray:
        """Returns the simulated Zodiacal emission in units of MJy/sr.

        Parameters
        ----------
        nside : int
            HEALPIX map resolution parameter.
        freq : float, `astropy.units.Quantity`
            Frequency [GHz] at which to evaluate the IPD model. The 
            frequency should be in units of GHz, unless an `astropy.Quantity`
            object is used, for which it only needs to be compatible with Hz.
        coord : str, optional
            Coordinate system of the output map. Accepted inputs are: 'E', 
            'C', or 'G'. Defaults to 'G' which is the Galactic coordinate 
            system.
        return_comps : bool, optional
            If True, the emission of each component in the model is returned
            separatly in form of an array of shape (`n_comps`, `npix`). 
            Defaults to False.

        Returns
        -------
        emission : `numpy.ndarray`
            Simulated Zodiacal emission in units of MJy/sr.
        """

        if isinstance(freq, u.Quantity):
            freq = freq.to('GHz').value

        emission = self.simulation_strategy.simulate(nside, freq)

        emission = coords.change_coordinate_system(emission, coord)

        return emission if return_comps else emission.sum(axis=0)