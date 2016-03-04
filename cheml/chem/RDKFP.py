import pandas as pd
import numpy as np
import os
import fnmatch
from rdkit import Chem



def _add_range(file,start_end):
    start = start_end[0::2]
    end = start_end[1::2]
    nit = file.count('%s')
    list_ranges = [str(range(start[it],end[it]+1))[1:-1] for it in range(len(start))]
    s = "pattern = '"+file+"'" + '%(' + str(list_ranges)[1:-1] + ')'
    exec(s)
    return pattern


class RDKFingerprint(object):
    """ An interface to RDKit fingerprints.
    
    Parameters
    ----------
    type: string, optional (default='Morgan')
        The available Fingerprints = ['Atom_pair', 'MACCS', Morgan', 'Topological_torsion']  

    vector: string, optional (default='bit')
        bit or int
        only availble for ... fingerprints
 
    nBits: integer, optional (default='bit')
        bit or int
        only availble for ... fingerprints
                 
    removeHs: boolean, optional (default=True)
        If True, 

    save: boolean, optional (default=False)
        If True, the data file would be saved in the current dirrectory.
                
    Returns
    -------
    Dragon Script and descriptors.
    """
    def __init__(self, removeHs=True, save=False,  type='Morgan', vector='bit',
                nBits=1024, ):
        self.type = type
        self.vector = vector
        self.nBits = nBits
        
        self.removeHs = removeHs
        self.save = save

    def MolfromFile(self, file, path=None, *arguments):
        """ Construct molecules from one or more input files.
        
        Parameters
        ----------
        file: string
            This is the place you define the file name and path. It can contain 
            any special character in the following list:
            
                *       : matches everything
                ?       : matches any single character
                [seq]   : matches any character in seq
                [!seq]  : matches any character not in seq
                /       : filename seperator

            The pattern matching is implemented by fnmatch - Unix filename pattern matching.
            Note: The pattern must include the extension at the end. A list of available 
            file extensions is provided here: 
            
                '.mol','.mol2'  : molecule files 
                '.pdb'          : protein data bank file
                '.tpl'          : TPL file
                '.smi'          : file of one or more lines of Smiles string
                '.smarts'       : file of one or more lines of Smarts string

        path: string, optional (default = None)            
            If path is None, this function tries to open the file as a single
            file (without any pattern matching). Therefore, none of the above 
            special characters except '/' are helpful when they are not part 
            of the file name or path.    
            If not None, it determines the path that this function walk through
            and look for every file that mathes the pattern in the file. To start
            walking from the curent directory, the path value should be '.'
        
        *arguments: integer
            If sequences in the special characters should be a range of integers,
            you can easily pass the start and the end arguments of range as extra 
            arguments. But, notice that:
                1- In this case remember to replace seq with %s. Then, you should 
                   have [%s] or [!%s] in the file pattern.
                2- for each %s you must pass two integers (always an even number 
                    of extra arguments must be passed). Also, the order is important
                    and it should be in the same order of '%s's. 
            
        examples
        --------
            (1)
            file: 'Mydir/1f/1_opt.smi'
            path: None
            >>> sample files to be read: 'Mydir/1f/1_opt.smi' 
            
            (2)
            file: '[1,2,3,4]?/*_opt.mol'
            path: 'Mydir'
            >>> sample files to be read: 'Mydir/1f/1_opt.mol', 'Mydir/2c/2_opt.mol', ... 
            
            (3)
            file: '[!1,2]?/*_opt.pdb'
            path: '.'
            >>> sample files to be read: './3f/3_opt.pdb', 'Mydir/7c/7_opt.pdb', ... 

            (4)
            file: '*['f','c']/*_opt.tpl'
            path: 'Mydir'
            >>> sample files to be read: 'Mydir/1f/1_opt.tpl', 'Mydir/2c/2_opt.tpl', ... 

            (5)
            file: '[%s]?/[!%s]_opt.mol2'
            arguments: 1,4,7,10
            path: 'Mydir/all'
            >>> sample files to be read: 'Mydir/all/1f/1_opt.mol2', 'Mydir/all/2c/2_opt.mol2', ... 
        """
        extensions = {'.mol':       Chem.MolFromMolFile,
                      '.mol2':      Chem.MolFromMol2File,
                      '.pdb':       Chem.MolFromPDBFile,
                      '.tpl':       Chem.MolFromTPLFile,
                      '.smi':       Chem.MolFromSmiles,
                      '.smarts':    Chem.MolFromSmarts,
                      '.inchi':     Chem.MolFromInchi
                      }
        file_name, file_extension = os.path.splitext(file)
        if file_extension == '':
            msg = 'file extension not determined'
            raise ValueError(msg)
        elif file_extension not in extensions:
            msg = "file extension '%s' not available"%file_extension
            raise ValueError(msg)
        start_end = [arg for arg in arguments]
        if len(start_end) != file_name.count('%s')*2:
            msg = "pass an even number of integers: 2 for each '%s'"
            raise ValueError(msg)        
        
        if path and '%s' in file:
            file = _add_range(file,start_end)
        
        self.molecules = []
        if path:
            for root, directories, filenames in os.walk(path):
                file_path = [os.path.join(root, filename) for filename in filenames]
                for filename in fnmatch.filter(file_path, os.path.join(path, file)):
                    if file_extension in ['.smi','.smarts']:
                        mols = open(filename, 'r')
                        mols = mols.readlines()
                        mols = [extensions[file_extension](x.strip,removeHs=self.removeHs) for x in mols]
                        self.molecules += mols
                    else:
                        self.molecules += [extensions[file_extension](filename,removeHs=self.removeHs)]
        else:
            if file_extension in ['.smi','.smarts']:
                mols = open(file, 'r')
                mols = mols.readlines()
                mols = [extensions[file_extension](x.strip,removeHs=self.removeHs) for x in mols]
                self.molecules += mols
            else:
                self.molecules += [extensions[file_extension](filename,removeHs=self.removeHs)]
    
    def fingerprint(self):
        if self.type == 'Hashed_atom_pair':
            if self.vector == 'int':
                HpairFps = [Chem.AtomPairs.Pairs.GetHashedAtomPairFingerprint(m,nBits=self.nBits) for m in self.molecules]
                dict_nonzero = [fp.GetNonzeroElements() for fp in HpairFps]
                data = pd.DataFrame(dict_nonzero,columns=range(self.nBits))
            if self.vector == 'bit':
                HpairFps = [Chem.rdMolDescriptors.GetHashedAtomPairFingerprintAsBitVect(m,nBits=self.nBits) for m in self.molecules]                
        
        elif self.type == 'Atom_pair':
                from rdkit.Chem.AtomPairs import Pairs
                pairFps = [Pairs.GetAtomPairFingerprint(m,nBits=) for m in self.molecules]
                pairScores = [] 
                for mol in pairFps:
                    pairScores+=[i for i in mol.GetNonzeroElements()]
                pairScores.sort()
            if self.vector == 'bit':


        elif self.type == 'MACCS':
            from rdkit.Chem import MACCSkeys
            fps = [MACCSkeys.GenMACCSKeys(m) for m in self.molecules]
            data = pd.DataFrame()
            for i,fp in enumerate(fps):
                data[i] = [el for el in fp]
            data = data.T
            if self.save:
                pd.to_csv('MACCS_fingerprints.csv',header=None)
            return data
        elif self.type == 'Morgan':

        elif self.type == 'Topological_torsion':
        