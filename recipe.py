"""recipe.py

PictureClerk - The little helper for your picture workflow.
This file contains the Recipe class
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2008/11/18 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


class Recipe():
    """
    A recipe defines the workflow a pipeline has to accomodate
    """

    def __init__(self, instructions):
        (self.stage_names, self.stage_types) = self._parse_instructions(instructions)
#        self.stage_jobs = _parse_instructions(instructions)     
        self.num_stages = len(instructions)
        
        
    def _parse_instructions(self, instructions):
        """Create stage specifications from given instructions."""
        # TODO: How should instructions look like?
        return (instructions, instructions)
        
    def __str__(self):
        string = []
        for i, stage in enumerate(self.stage_names):
            string.append('%i: %s' % (i+1, stage))
        return '\n'.join(string)
        
    def __repr__(self):
        return str(self)

    
