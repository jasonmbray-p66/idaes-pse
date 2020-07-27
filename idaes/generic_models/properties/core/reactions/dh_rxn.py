##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
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
Methods for calculating heat of reaction
"""
from pyomo.environ import Var

from idaes.core import MaterialFlowBasis


# -----------------------------------------------------------------------------
# Constant dh_rxn
class constant_dh_rxn():
    def build_parameters(rblock, config):
        units = rblock.parent_block().get_metadata().derived_units

        rbasis = rblock.parent_block().config.reaction_basis
        if rbasis == MaterialFlowBasis.molar:
            basis = "mole"
        elif rbasis == MaterialFlowBasis.mass:
            basis = "mass"

        rblock.dh_rxn_ref = Var(
                initialize=config.parameter_data["dh_rxn_ref"],
                doc="Specific heat of reaction at reference state",
                units=units["energy_"+basis])

    def return_expression(b, rblock, r_idx, T):
        return rblock.dh_rxn_ref
