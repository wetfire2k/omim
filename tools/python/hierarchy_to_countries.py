#!/usr/bin/python
import sys, json, re
from optparse import OptionParser
import os.path

class CountryDict(dict):
  def __init__(self, *args, **kwargs):
    dict.__init__(self, *args, **kwargs)
    self.order = ['id', 'v', 'c', 's', 'g']

  def __iter__(self):
    for key in self.order:
      if key in self:
        yield key
    for key in dict.__iter__(self):
      if key not in self.order:
        yield key

  def iteritems(self):
    for key in self.__iter__():
      yield (key, self.__getitem__(key))

def get_size(path, name):
  if path == '0':
    return 0
  filename = os.path.join(path, '{0}.mwm'.format(name))
  try:
    return os.path.getsize(filename)
  except OSError:
    sys.stderr.write('Missing file: {0}\n'.format(filename))
    return -1

def collapse_single(root):
  for i in range(len(root['g'])):
    if 'g' in root['g'][i]:
      if len(root['g'][i]['g']) == 1:
        # replace group by a leaf
        if 'c' in root['g'][i]:
          root['g'][i]['g'][0]['c'] = root['g'][i]['c']
        root['g'][i] = root['g'][i]['g'][0]
      else:
        collapse_single(root['g'][i])

parser = OptionParser(add_help_option=False)
parser.add_option('-t', '--target', help='Path to mwm files')
parser.add_option('-h', '--hierarchy', default='hierarchy.txt', help='Hierarchy file')
parser.add_option('-c', '--old', help='old_vs_new.csv file')
parser.add_option('-v', '--version', type='int', default=151231, help='Version')
parser.add_option('-o', '--output', help='Output countries.txt file (default is stdout)')
parser.add_option('-m', '--help', action='store_true', help='Display this help')
(options, args) = parser.parse_args()

if options.help:
  parser.print_help()
  sys.exit(0)

if not os.path.isfile(options.hierarchy):
  parser.error('Hierarchy file is required.')

if options.old is None or not os.path.isfile(options.old):
  ovnpath = os.path.join(os.path.dirname(options.hierarchy), 'old_vs_new.csv')
else:
  ovnpath = options.old
oldvs = {}
try:
  with open(ovnpath, 'r') as f:
    for line in f:
      m = re.match(r'(.+?)\t(.+)', line.strip())
      if m:
        if m.group(2) in oldvs:
          oldvs[m.group(2)].append(m.group(1))
        else:
          oldvs[m.group(2)] = [m.group(1)]
except IOError:
  sys.stderr.write('Could not read old_vs_new file from {0}\n'.format(ovnpath))

mwmpath = '0' if not options.target else options.target
stack = [CountryDict({ "v": options.version, "id": "Countries", "g": [] })]
last = None
with open(options.hierarchy, 'r') as f:
  for line in f:
    m = re.match('( *)(.+?)\n', line)
    if m:
      depth = len(m.group(1))
      if last is not None:
        lastd = last['d']
        del last['d']
        if lastd < depth:
          # last is a group
          last['g'] = []
          stack.append(last)
        else:
          last['s'] = get_size(mwmpath, last['id'])
          if last['s'] >= 0:
            stack[-1]['g'].append(last)
      while depth < len(stack) - 1:
        # group ended, add it to higher group
        g = stack.pop()
        if len(g['g']) > 0:
          stack[-1]['g'].append(g)
      items = m.group(2).split(';')
      last = CountryDict({ "id": items[0], "d": depth })
      if items[0] in oldvs:
        last['old'] = oldvs[items[0]]
      #if len(items) > 2 and len(items[2]) > 0::
      #  last['c'] = items[2]
      #if len(items) > 3 and len(items[3]) > 0:
      #  last['lang'] = items[3].split(',')

# the last line is always a file
del last['d']
last['s'] = get_size(mwmpath, last['id'])
if last['s'] >= 0:
  stack[-1]['g'].append(last)
while len(stack) > 1:
  g = stack.pop()
  if len(g['g']) > 0:
    stack[-1]['g'].append(g)

collapse_single(stack[-1])
if options.output:
  with open(options.output, 'w') as f:
    json.dump(stack[-1], f, indent=1)
else:
  print json.dumps(stack[-1], indent=1)
