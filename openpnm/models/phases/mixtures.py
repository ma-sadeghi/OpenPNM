import numpy as np


def salinity(target, temperature='pore.temperature',
             concentration='pore.concentration'):
    r"""
    Calculates the salinity in g salt per kg of solution from concentration

    Parameter
    ---------
    target : OpenPNM Object
        The object for which these values are being calculated.  This
        controls the length of the calculated array, and also provides
        access to other necessary thermofluid properties.

    temperature : string
        The dictionary key containing the temperature values in Kelvin.

    concentration : string
        The dictionary key containing the concentration values, in SI units of
        mol/m3.

    Returns
    -------
    salinity : ND-array
        The salinity in g of solute per kg of solution.

    Notes
    -----
    This model is useful for converting known concentration values (e.g.
    calculated by a transport algorithm) into salinity values, which can then
    be used for finding other physical properties of water which are available
    as a function of salinity.

    The salinity correlations are valid for salinity up to 160 g/kg, which
    corresponds to a concentration of 0.05 mol/L (assuming NaCl is the only
    solute)

    """
    C = target[concentration]
    T = target[temperature]
    a = 8.73220929e+00
    b = 6.00389629e+01
    c = -1.19083743e-01
    d = -1.77796042e+00
    e = 3.26987130e-04
    f = -1.09636011e-01
    g = -1.83933426e-07
    S = a + b*C + c*T + d*C**2 + e*T**2 + f*C**3 + g*T**3
    return S


def mole_weighted_average(target, prop):
    r"""
    """
    element = prop.split('.')[0]
    vals = np.zeros(target._count(element))
    for item in target.components.keys():
        frac = target[element + '.mole_fraction.' + item]
        temp = target.project[item][prop]
        vals += temp*frac
    return vals


def fuller_diffusivity(target, molecular_weight='pore.molecular_weight',
                       molar_diffusion_volume='pore.molar_diffusion_volume',
                       temperature='pore.temperature',
                       pressure='pore.pressure'):
    r"""

    """
    species_A, species_B = target.components.values()
    T = target[temperature]
    P = target[pressure]
    MA = species_A[molecular_weight]
    MB = species_B[molecular_weight]
    vA = species_A[molar_diffusion_volume]
    vB = species_A[molar_diffusion_volume]
    MAB = 1e3*2*(1.0/MA + 1.0/MB)**(-1)
    P = P*1e-5
    value = 0.00143*T**1.75/(P*(MAB**0.5)*(vA**(1./3) + vB**(1./3))**2)*1e-4
    return value


def wilke_fuller_diffusivity(target, mole_fraction='pore.mole_fraction',
                             molecular_weight='pore.molecular_weight',
                             molar_diffusion_volume='pore.molar_diffusion_volume',
                             temperature='pore.temperature',
                             pressure='pore.pressure'):
    r"""
    Estimates the diffusion coeffient of each species in a gas mixture

    Uses the fuller equation to estimate binary diffusivity between pairs, then
    uses the correction of Fairbanks and Wilke to account for the composition
    of the gas mixture.

    Parameters
    ----------
    target : OpenPNM Object
        The object for which these values are being calculated.  This
        controls the length of the calculated array, and also provides
        access to other necessary thermofluid properties.

    mole_fraction : string
        Dictionary key containing the mole fraction of each species.  The
        default is 'pore.mole_fraction'
    molecular_weight : string
        Dictionary key containing the molecular weight of each species.  The
        default is 'pore.molecular_weight'
    molar_diffusion_volume : string
        Dictionary key containing the molar diffusion volume of each species.
        This is used by the Fuller correlation.  The default is
        'pore.molar_diffusion_volume'
    temperature : string
        Dictionary key contain the temperature of the mixture.  The default
        is 'pore.temperature'
    pressure : string
        Dictionary key contain the pressure of the mixture.  The default
        is 'pore.pressure'

    Returns
    -------
    Dij : dict containing ND-arrys
        The dict contains one array for each component, containing the
        diffusion coefficient of that component at each location.

    Reference
    ---------
    Fairbanks DF and CR Wilke, Diffusion Coefficients in Multicomponent
    Gas Mixtures. Industrial & Engineering Chemistry, 42(3), p471–475 (1950).
    `DOI: 10.1021/ie50483a022 <http://doi.org/10.1021/ie50483a022>`_
    """
    comps = list(target.components.values())
    # Find diffusivity for each pair
    for i in range(len(comps)):
        for j in range(len(comps)):
            if j > i:
                A = comps[i]
                B = comps[j]
                temp = MixDict(target)
                temp.components = {A.name: A, B.name: B}
                D = fuller_diffusivity(target=temp,
                                       molecular_weight=molecular_weight,
                                       molar_diffusion_volume=molar_diffusion_volume,
                                       temperature=temperature, pressure=pressure)
                A['pore.D_in_' + B.name] = D
                B['pore.D_in_' + A.name] = D

    # Find the denominator
    values = {}
    for i in range(len(comps)):
        denom = 0.0
        A = comps[i]
        yA = target[mole_fraction + '.' + A.name]
        for j in range(len(comps)):
            if i != j:
                B = comps[j]
                yB = target[mole_fraction + '.' + B.name]
                Dab = A['pore.D_in_' + B.name]
                denom += yB/Dab
        values[A.name] = (1 - yA)/denom

    return values


class MixDict(dict):
    pass
