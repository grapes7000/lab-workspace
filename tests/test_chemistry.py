import unittest
from lab_workspace.core.chemistry import parse_formula,molar_mass,Species,derive,check_balance,calculate_reaction
class ChemistryTests(unittest.TestCase):
 def test_formula_parentheses(self):self.assertEqual(parse_formula('Ca(OH)2'),{'Ca':1.0,'O':2.0,'H':2.0})
 def test_molar_mass_water(self):self.assertAlmostEqual(molar_mass('H2O'),18.015,places=3)
 def test_density_chain(self):
  d=derive(Species('reactant',mw=100,volume=10,volume_unit='mL',density=0.8,density_unit='g/mL'))
  self.assertAlmostEqual(d['mass_g'],8);self.assertAlmostEqual(d['moles'],.08)
 def test_active_fraction_reduces_available_moles(self):
  d=derive(Species('reactant',mw=100,mass=10,purity=80,active_fraction=25))
  self.assertAlmostEqual(d['moles'],.02)
 def test_balanced(self):
  s=[Species('reactant',formula='H2',coefficient=2),Species('reactant',formula='O2'),Species('product',formula='H2O',coefficient=2)]
  self.assertTrue(check_balance(s)[0])
 def test_limiting_reagent(self):
  s=[Species('reactant',name='Hydrogen',formula='H2',coefficient=2,moles=5),Species('reactant',name='Oxygen',formula='O2',moles=2),Species('product',name='Water',formula='H2O',coefficient=2)]
  r=calculate_reaction(s);self.assertEqual(r.limiting,'Oxygen');self.assertAlmostEqual(r.extent,2);self.assertAlmostEqual(r.rows[2]['theoretical_moles'],4)
if __name__=='__main__':unittest.main()
