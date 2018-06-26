import openpnm as op
import scipy as sp
import pytest


class DispersionTest:

    def setup_class(self):
        sp.random.seed(0)
        self.net = op.network.Cubic(shape=[4, 3, 1], spacing=1e-4)
        self.geo = op.geometry.StickAndBall(network=self.net,
                                            pores=self.net.Ps,
                                            throats=self.net.Ts)

        self.phase = op.phases.Water(network=self.net)
        self.phase['throat.viscosity'] = self.phase['pore.viscosity'][0]

        self.phys = op.physics.GenericPhysics(network=self.net,
                                              phase=self.phase,
                                              geometry=self.geo)
        mod1 = op.models.physics.hydraulic_conductance.hagen_poiseuille
        self.phys.add_model(propname='throat.hydraulic_conductance',
                            model=mod1, throat_viscosity='throat.viscosity',
                            regen_mode='normal')
        mod2 = op.models.physics.diffusive_conductance.ordinary_diffusion
        self.phys.add_model(propname='throat.diffusive_conductance',
                            model=mod2, regen_mode='normal')

    def test_dispersion(self):
        alg1 = op.algorithms.StokesFlow(network=self.net, phase=self.phase)
        alg1.set_value_BC(pores=self.net.pores('back'), values=10)
        alg1.set_value_BC(pores=self.net.pores('front'), values=0)
        alg1.run()
        self.phase[alg1.settings['quantity']] = alg1[alg1.settings['quantity']]

        alg2 = op.algorithms.Dispersion(network=self.net,
                                                phase=self.phase)
        alg2.set_value_BC(pores=self.net.pores('back'), values=2)
        alg2.set_value_BC(pores=self.net.pores('front'), values=0)
        alg2.run()
        x = [0., 0., 0.,
             1.03441, 1.25552, 1.47347,
             1.71339, 1.87639, 1.85104,
             2., 2., 2.]
        y = sp.around(alg2[alg2.settings['quantity']], decimals=5)
        assert sp.all(x == y)

    def teardown_class(self):
        ws = op.Workspace()
        ws.clear()


if __name__ == '__main__':

    t = DispersionTest()
    t.setup_class()
    for item in t.__dir__():
        if item.startswith('test'):
            print('running test: '+item)
            t.__getattribute__(item)()
    self = t
