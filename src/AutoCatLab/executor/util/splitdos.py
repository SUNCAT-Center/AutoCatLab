import numpy as np
from ase.io import read


class SplitDOS:
    """
    Writes DOS as separate atomic contributions.
    Code is adapted from split_dos.py which belongs to Jonsson and Henkelman groups.
    URL: http://theory.cm.utexas.edu/vtsttools/scripts.html
    """

    def __init__(self, file_dir='./', structure_file='CONTCAR'):
        self.file_dir = file_dir
        self.structure_file = self.file_dir + structure_file
        self.atoms = self.read_posfile()

        with open(self.file_dir + "/DOSCAR", 'r') as f:
            self.lines = f.readlines()
        self.natoms = int(self.lines[0].strip().split()[0])
        self.index = 5
        self.nedos = int(self.lines[self.index].strip().split()[2])
        self.efermi = float(self.lines[self.index].strip().split()[3])

    def read_posfile(self):
        try:
            atoms = read(self.structure_file)
        except IOError:
            print(
                "[__main__]: Couldn't open {} input file, atomic positions will not be written...\n".format(self.structure_file))
            atoms = None
        return atoms

    def write_dos0(self):
        print("location", self.file_dir+"/DOS0")
        with open(self.file_dir+"/DOS0", 'w') as fdos:
            line = self.lines[self.index+1].strip().split()
            self.ncols = int(len(line))
            for n in range(self.nedos):
                self.index += 1
                e = float(self.lines[self.index].strip().split()[0])
                e -= self.efermi
                fdos.write('%15.8f ' % (e))

                for col in range(1, self.ncols):
                    dos = float(self.lines[self.index].strip().split()[col])
                    fdos.write('%15.8f ' % (dos))
                fdos.write('\n')
        line = self.lines[self.index+2].strip().split()
        self.ncols = int(len(line))

    def write_nospin(self):
        if not self.atoms:
            pos = np.zeros((self.natoms, 3))
        else:
            pos = self.atoms.get_positions()

        for i in range(1, self.natoms+1):
            si = str(i)

            fdos = open(self.file_dir+"/DOS"+si, 'w')
            self.index += 1
            ia = i-1
            fdos.write('# %15.8f %15.8f %15.8f \n' %
                       (pos[ia, 0], pos[ia, 1], pos[ia, 2]))

            # LOOP OVER NEDOS
            for n in range(self.nedos):
                self.index += 1
                e = float(self.lines[self.index].strip().split()[0])
                e -= self.efermi
                fdos.write('%15.8f ' % (e))

                for col in range(1, self.ncols):
                    dos = float(self.lines[self.index].strip().split()[col])
                    fdos.write('%15.8f ' % (dos))
                fdos.write('\n')
        fdos.close()

    def write_spin(self):
        if not self.atoms:
            pos = np.zeros((self.natoms, 3))
        else:
            pos = self.atoms.get_positions()

        nsites = (self.ncols - 1) / 2

        for i in range(1, self.natoms+1):
            si = str(i)
            ## OPEN DOSi FOR WRITING ##
            with open(self.file_dir+"/DOS"+si, 'w') as fdos:
                self.index += 1
                ia = i-1
                fdos.write('# %d \n' % (self.ncols))
                fdos.write('# %15.8f %15.8f %15.8f \n' %
                           (pos[ia, 0], pos[ia, 1], pos[ia, 2]))

                ### LOOP OVER NEDOS ###
                for n in range(self.nedos):
                    self.index += 1
                    e = float(self.lines[self.index].strip().split()[0])
                    e -= self.efermi
                    fdos.write('%15.8f ' % (e))

                    for site in range(int(nsites)):
                        dos_up = float(
                            self.lines[self.index].strip().split()[site*2+1])
                        dos_down = float(
                            self.lines[self.index].strip().split()[site*2+2])*-1
                        fdos.write('%15.8f %15.8f ' % (dos_up, dos_down))
                    fdos.write('\n')
