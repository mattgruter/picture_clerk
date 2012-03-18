"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import worker


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
            string.append('%i: %s' % (i + 1, stage))
        return '\n'.join(string)

    def __repr__(self):
        return str(self)

    @classmethod
    def fromString(cls, list_as_string):
        return Recipe([eval(s.strip(), worker.__dict__)
                       for s in list_as_string.split(',')])


