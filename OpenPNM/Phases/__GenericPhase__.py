"""
===============================================================================
module __GenericPhase__: Base class for building Phase objects
===============================================================================

"""
import OpenPNM
from OpenPNM.Base import Core
import OpenPNM.Phases.models
import scipy as sp

class GenericPhase(Core):
    r"""
    Base class to generate a generic phase object.  The user must specify models
    and parameters for all the properties they require. Classes for several
    common phases are included with OpenPNM and can be found under OpenPNM.Phases.

    Parameters
    ----------
    network : OpenPNM Network object
        The network to which this Phase should be attached

    components : list of OpenPNM Phase objects
        These Phase objects are ficticious or virtual phases that are the pure
        components from which the mixture is made.  They are used to calculate
        and store any pure component data.  If none are supplied then this
        object will act like either a pure component, a mixture whose properties
        are well known (like air) and need not to be found from consideration of
        the pure component properties.

    name : str, optional
        A unique string name to identify the Phase object, typically same as
        instance name but can be anything.

    """
    def __init__(self,network=None,components=[],name=None,**kwargs):
        super(GenericPhase,self).__init__(**kwargs)
        self._logger.debug("Construct class")

        if network == None:
            self._net = OpenPNM.Network.GenericNetwork()
        else:
            self._net = network

        self.name = name  # Assign name to object

        # Initialize label 'all' in the object's own info dictionaries
        self['pore.all'] = self._net['pore.all']
        self['throat.all'] = self._net['throat.all']

        #Set standard conditions on the fluid to get started
        self['pore.temperature'] = 298.0
        self['pore.pressure'] = 101325.0

        # Register Ohase object in Network dictionary
        self._net['pore.'+self.name] = True
        self._net['throat.'+self.name] = True

        if components != []:
            for comp in components:
                self._phases.append(comp) # Associate any sub-phases
                #Add models for components to inherit mixture T and P
                comp.add_model(propname='pore.temperature',model=OpenPNM.Phases.models.mixture_props.temperature,mixture=self)
                comp.add_model(propname='pore.pressure',model=OpenPNM.Phases.models.mixture_props.pressure,mixture=self)
                #Move T and P models to beginning of regeneration order
                comp.reorder_models({'pore.temperature':0,'pore.pressure':1})
        self._net._phases.append(self)  # Append this Phase to the Network

    def __setitem__(self,prop,value):
        for phys in self._physics:
            if prop in phys.keys():
                self._logger.error(prop+' is already defined in at least one associated Physics object')
                return
        super(GenericPhase,self).__setitem__(prop,value)

    def __getitem__(self,key):
        if key not in self.keys():
            self._logger.debug(key+' not on Phase, constructing data from Physics')
            return self._interleave_data(key,sources=self._physics)
        else:
            return super(GenericPhase,self).__getitem__(key)

    def set_component(self,phase,mode='add'):
        r'''
        This method is used to add or remove a ficticious phase object to this
        object.

        Parameters
        ----------
        phase : OpenPNM Phase object
            This is the ficticious phase object defining a pure component.

        mode : string
            Indicates whether to 'add' or 'remove' the supplied object
        '''
        if mode == 'add':
            if phase.name in self.phases():
                self._logger.error('Phase already present')
            else:
                self._phases.append(phase)
                temp = phase._models
                phase._models.clear()
                phase.add_model(propname='pore.temperature',model=OpenPNM.Phases.models.mixture_props.temperature,mixture=self)
                phase.add_model(propname='pore.pressure',model=OpenPNM.Phases.models.mixture_props.pressure,mixture=self)
                phase._models.update(temp)
        elif mode == 'remove':
            if phase.name in self.phases():
                self._phases.remove(phase)
            else:
                self._logger.error('Phase not found')

    def regenerate(self,**kwargs):
        for item in self._phases:
            item.regenerate(**kwargs)
        super(GenericPhase,self).regenerate(**kwargs)

    #Pull in doc string for the Core regenerate method
    regenerate.__doc__ = Core.regenerate.__doc__

    def check_mixture_health(self):
        r'''
        Query the properties of the 'virtual phases' that make up a mixture
        to ensure they all add up
        '''
        mole_sum = sp.zeros((self.Np,))
        for comp in self._phases:
            try:
                mole_sum = mole_sum + comp['pore.mole_fraction']
            except:
                pass
        return mole_sum

    def check_physics_health(self):
        r'''
        Perform a check to find pores which have overlapping or undefined Physics
        '''
        phys = self.physics()
        Ptemp = sp.zeros((self.Np,))
        Ttemp = sp.zeros((self.Nt,))
        for item in phys:
                Pind = self['pore.'+item]
                Tind = self['throat.'+item]
                Ptemp[Pind] = Ptemp[Pind] + 1
                Ttemp[Tind] = Ttemp[Tind] + 1
        health = {}
        health['overlapping_pores'] = sp.where(Ptemp>1)[0].tolist()
        health['undefined_pores'] = sp.where(Ptemp==0)[0].tolist()
        health['overlapping_throats'] = sp.where(Ttemp>1)[0].tolist()
        health['undefined_throats'] = sp.where(Ttemp==0)[0].tolist()
        return health


