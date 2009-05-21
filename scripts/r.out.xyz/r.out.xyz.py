#!/usr/bin/env python
############################################################################
#
# MODULE:       r.out.xyz
# AUTHOR:       M. Hamish Bowman, Dept. Marine Science, Otago Univeristy,
#                 New Zealand
#		Converted to Python by Glynn Clements
# PURPOSE:      Export a raster map as x,y,z values based on cell centers
#               This is a simple wrapper script for "r.stats -1ng"
#
# COPYRIGHT:    (c) 2006 Hamish Bowman, and the GRASS Development Team
#		(c) 2008 Glynn Clements, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%Module
#% description: Export a raster map to a text file as x,y,z values based on cell centers.
#% keywords: raster, export
#%End
#%option
#% key: input
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Name of input raster map 
#% required: yes
#%end
#%option
#% key: output
#% type: string
#% gisprompt: new_file,file,output
#% key_desc: name
#% description: Name for output file (if omitted or "-" output to stdout)
#% required: no
#%end
#%option
#% key: fs
#% type: string
#% key_desc: character
#% description: Field separator
#% answer: |
#% required: no
#%end

import sys
from grass.script import core as grass

def main():
    # if no output filename, output to stdout
    output = options['output']
    if output == "" or output == "-":
	outf = sys.stdout
    else:
	outf = file(output)
    ret = grass.run_command("r.stats", flags = "1gn", input = options['input'], fs = options['fs'], stdout = outf)
    sys.exit(ret)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
