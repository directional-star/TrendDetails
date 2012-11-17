#Copyright (c) 2012, www.directionalstar.com 

#See the file LICENSE.txt for copying permission.

class FormInputs():
  def __init__(self, type, name, value = None):
    self.name = name
    self.value = value
    self.type = type
    self.funcName = 'input_%s' % (type)
#    self.func = self.__dict__.get(self.funcName, self.input_notype)
    self.func = getattr(self, self.funcName, self.input_notype)

  def html(self):
    return self.func('html')

  def input_notype(self, out = 'html'):
    return '<div class="error">Unknown input type: %s</div>' % (self.type)

  def input_bool(self, out = 'html'):
    val = bool(self.value)
    onselected = 'selected="selected"'
    offselected = ''
    if not val:
      onselected, offselected = offselected, onselected
    return '<select name="%s" data-type="bool"><option value="true" %s>on</option><option value="false" %s>off</option></select>' % \
      (self.name, onselected, offselected)

