##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2019, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Tests for CSTR unit model.
Authors: Andrew Lee, Vibhav Dabadghao
"""

import pytest
from pyomo.environ import ConcreteModel, SolverFactory
from idaes.core import FlowsheetBlock
from idaes.unit_models.cstr import CSTR
from idaes.property_models.examples.saponification_thermo import (
    SaponificationParameterBlock)
from idaes.property_models.examples.saponification_reactions import (
    SaponificationReactionParameterBlock)
from idaes.core.util.model_statistics import (degrees_of_freedom,
                                              number_variables,
                                              number_total_constraints,
                                              fixed_variables_set,
                                              activated_constraints_set,
                                              number_unused_variables)


# -----------------------------------------------------------------------------
# See if ipopt is available and set up solver
if SolverFactory('ipopt').available():
    solver = SolverFactory('ipopt')
    solver.options = {'tol': 1e-6,
                      'mu_init': 1e-8,
                      'bound_push': 1e-8}
else:
    solver = None


# -----------------------------------------------------------------------------
class TestSaponification(object):
    @pytest.fixture(scope="class")
    def sapon(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})

        m.fs.properties = SaponificationParameterBlock()
        m.fs.reactions = SaponificationReactionParameterBlock(default={
                                "property_package": m.fs.properties})

        m.fs.unit = CSTR(default={"property_package": m.fs.properties,
                                  "reaction_package": m.fs.reactions,
                                  "has_equilibrium_reactions": False,
                                  "has_heat_transfer": True,
                                  "has_heat_of_reaction": True,
                                  "has_pressure_change": True})

        return m

    @pytest.mark.build
    def test_build(self, sapon):

        assert hasattr(sapon.fs.unit, "inlet")
        assert len(sapon.fs.unit.inlet.vars) == 4
        assert hasattr(sapon.fs.unit.inlet, "flow_vol")
        assert hasattr(sapon.fs.unit.inlet, "conc_mol_comp")
        assert hasattr(sapon.fs.unit.inlet, "temperature")
        assert hasattr(sapon.fs.unit.inlet, "pressure")

        assert hasattr(sapon.fs.unit, "outlet")
        assert len(sapon.fs.unit.outlet.vars) == 4
        assert hasattr(sapon.fs.unit.outlet, "flow_vol")
        assert hasattr(sapon.fs.unit.outlet, "conc_mol_comp")
        assert hasattr(sapon.fs.unit.outlet, "temperature")
        assert hasattr(sapon.fs.unit.outlet, "pressure")

        assert hasattr(sapon.fs.unit, "cstr_performance_eqn")
        assert hasattr(sapon.fs.unit, "volume")
        assert hasattr(sapon.fs.unit, "heat_duty")
        assert hasattr(sapon.fs.unit, "deltaP")

        assert number_variables(sapon) == 27
        assert number_total_constraints(sapon) == 16
        assert number_unused_variables(sapon) == 0

    def test_dof(self, sapon):
        sapon.fs.unit.inlet.flow_vol.fix(1.0e-03)
        sapon.fs.unit.inlet.conc_mol_comp[0, "H2O"].fix(55388.0)
        sapon.fs.unit.inlet.conc_mol_comp[0, "NaOH"].fix(100.0)
        sapon.fs.unit.inlet.conc_mol_comp[0, "EthylAcetate"].fix(100.0)
        sapon.fs.unit.inlet.conc_mol_comp[0, "SodiumAcetate"].fix(0.0)
        sapon.fs.unit.inlet.conc_mol_comp[0, "Ethanol"].fix(0.0)

        sapon.fs.unit.inlet.temperature.fix(303.15)
        sapon.fs.unit.inlet.pressure.fix(101325.0)

        sapon.fs.unit.volume.fix(1.5e-03)
        sapon.fs.unit.heat_duty.fix(0)
        sapon.fs.unit.deltaP.fix(0)

        assert degrees_of_freedom(sapon) == 0

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_initialize(self, sapon):
        orig_fixed_vars = fixed_variables_set(sapon)
        orig_act_consts = activated_constraints_set(sapon)

        sapon.fs.unit.initialize(optarg={'tol': 1e-6})

        assert degrees_of_freedom(sapon) == 0

        fin_fixed_vars = fixed_variables_set(sapon)
        fin_act_consts = activated_constraints_set(sapon)

        assert len(fin_act_consts) == len(orig_act_consts)
        assert len(fin_fixed_vars) == len(orig_fixed_vars)

        for c in fin_act_consts:
            assert c in orig_act_consts
        for v in fin_fixed_vars:
            assert v in orig_fixed_vars

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_solution(self, sapon):
        assert (pytest.approx(101325.0, abs=1e-2) ==
                sapon.fs.unit.outlet.pressure[0].value)
        assert (pytest.approx(304.09, abs=1e-2) ==
                sapon.fs.unit.outlet.temperature[0].value)
        assert (pytest.approx(20.32, abs=1e-2) ==
                sapon.fs.unit.outlet.conc_mol_comp[0, "EthylAcetate"].value)

    @pytest.mark.ui
    def test_report(self, sapon):
        sapon.fs.unit.report()
