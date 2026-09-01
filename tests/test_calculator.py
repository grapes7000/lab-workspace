import unittest
from lab_workspace.core.calculator import evaluate, mass_from_moles, molarity, dilution_final_volume

class CalculatorTests(unittest.TestCase):
    def test_expression(self): self.assertAlmostEqual(evaluate("sqrt(25)+sin(pi/2)"), 6.0)
    def test_blocks_unsafe_code(self):
        with self.assertRaises(ValueError): evaluate("__import__('os').system('echo no')")
    def test_mass(self): self.assertAlmostEqual(mass_from_moles(2, 18.015), 36.03)
    def test_molarity(self): self.assertAlmostEqual(molarity(0.5, 2), 0.25)
    def test_dilution(self): self.assertAlmostEqual(dilution_final_volume(10, 5, 2), 25)

if __name__ == "__main__": unittest.main()
