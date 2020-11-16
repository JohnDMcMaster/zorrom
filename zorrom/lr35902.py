from zorrom import solver
'''
Reference
https://www.neviksti.com/DMG/

'''


class LR35902(solver.SolverMaskROM):
    def desc(self):
        return 'LR35902'

    def txtwh(self):
        # 128 bits across
        #   Physically organized in 16 groups of 8 bits
        #   Logically organized in 8 groups of 16 bits
        # 16 bits down
        return (128, 16)

    def invert(self):
        return False

    def solver_params(self):
        return {
            "rotate": 180,
            "flipx": True,
            "layout-alg": "cols-downr",
        }
