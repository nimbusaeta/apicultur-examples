#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from apicultur.utils import ApiculturRateLimitSafe
try:
    from secret import ACCESS_TOKEN 
except ImportError:
    print(u"No encuentro el archivo 'secret.py' en este directorio con su ACCESS_TOKEN...")
    sys.exit(1)

from .combination import Combination

class Structure:

  APICULTUR = ApiculturRateLimitSafe(ACCESS_TOKEN, "example")

  PRONOUNS =  {
    'la':  'complemento directo',
    'las': 'complemento directo',
    'le':  'complemento indirecto',
    'les': 'complemento indirecto',
    'lo':  'complemento directo',
    'los': 'complemento directo',
    'nos': 'complemento directo o indirecto',
    'me':  'complemento directo o indirecto',
    'os':  'complemento directo o indirecto',
    'te':  'complemento directo o indirecto',
    'se':  'complemento indirecto, sustituyendo a "le" o "les"'
  }

  VERB_MESSAGES = {
    'valid' : {  
      True : u'\t\tTu forma verbal es un infinitivo, imperativo '
             u'o gerundio, por lo tanto se puede usar con enclíticos.\n',
      False: u'\t\tSin embargo, te advertimos que los enclíticos '
             u'deberían usarse solo con infinitivos, gerundios '
             u'e imperativos. En algunas regiones, por ejemplo '
             u'en Asturias, los pronombres pueden posponer al indicativo, condicional '
             u'y subjuntivo, pero en el castellano estándar está en desuso.\n'
    },
    'regular' : {
      True : u'',
      False: u'\t Sin embargo...(explicar por qué vamosnos o demossela '
             u'o tomados son incorrectos).\n'
    }
  }

  ENC_MESSAGES = [u'\tNo se han detectado enclíticos.',

                  u'\tTienes un enclítico de tipo {}: {}.',

                  u'\tTienes dos enclíticos:\n'\
                  u'\t\tEl primero es un {}: {}.\n'\
                  u'\t\tEl segundo es un {}: {}.',

                  u'\tTienes tres enclíticos:\n'\
                  u'\t\tEl primero es un {}: {}.\n'\
                  u'\t\tEl segundo es un {}: {}.\n'
                  u'\t\tEl tercero es un {}: {}.'

  ]

  def __init__(self, is_regular, lemas, enclitics):
    self.lemas = lemas
    self.enclitics = enclitics
    self.is_regular = is_regular
    self.valid = False

    self.infinitives, self.pers, self.num = self.get_forms()
    self.reflexive = self.is_reflexive()

    self.combination = None
    if len(enclitics) >= 2:     
      self.combination = Combination(enclitics)
    self.message = self.build_message()

  def get_forms(self):
    iig_infinitives = [] #infinitives for inf, imp and ger forms
    infinitives = []
    iig_pers, iig_num = [], []
    pers, num = [], []

    for lema in self.lemas:
      category = lema['categoria']

      if category[2] in ['M', 'G', 'N']:
        self.valid = True
      if not self.valid:
        infinitives.append(lema['lema'])
        #TODO remove repetition
        if self.enclitics:
          if category[2] != 'P':
            pers.append(category[4])
            num.append(category[5])
      else:    
        iig_infinitives.append(lema['lema'])
        if self.enclitics:
          if category[2] == 'M':
            iig_pers.append(category[4])
            iig_num.append(category[5])
    if iig_infinitives:
      infinitives = iig_infinitives
      pers, num = iig_pers, iig_num

    infinitives = list(set(infinitives))
    return infinitives, pers, num   

  def is_reflexive(self):
    if not self.enclitics:
      return (False, False)

    first = self.enclitics[0]
    length = len(self.enclitics)
    pr_pers, pr_num = None, None

    if first == 'se':
      if length == 1:
        return (True, True)
      elif length >= 2:
        second = self.enclitics[1]
        if length == 2:
          if not self.pers:
            if second in ['la', 'lo', 'las', 'los']:
              return (True, False)
            else:
              return (True, True)
          else:
            if '3' in self.pers:
              return (True, False)
        else:
          return (True, True)
              
        #TODO mark acerquémosele as invalid combination.

    elif first in ['me', 'te', 'nos', 'os'] and length != 3:
      if not self.pers:
        return (True, False)
      else:
        pr_lemas = self.APICULTUR.lematiza2(word=first)['lemas']
        for pr_lema in pr_lemas:
          pr_cat = pr_lema['categoria']
          if pr_cat[:2] == 'PP':
            pr_pers, pr_num = pr_cat[2], pr_cat[4]
            break
        if pr_pers in self.pers and pr_num in self.num:
          return (True, True) 
    #return (can it be reflexive, is it always reflexive)
    return (False, False)

  def build_message(self):
    length = len(self.enclitics)
    message = u'\tTienes un verbo que puede ser uno de los siguientes: {}.\n'
    if length >= 1:
      message += (self.VERB_MESSAGES['valid'][self.valid]
              + self.VERB_MESSAGES['regular'][self.is_regular])
 
    message += self.ENC_MESSAGES[length]
    elms = [(self.PRONOUNS[encl], encl) for encl in self.enclitics]
    elms = [item for elm in elms for item in elm]
    if length >= 2:     
      #if comb is valid, 1st encl is indir and 2nd one is dir
      if (not self.combination.error and 
                ''.join(self.enclitics) not in ['sele', 'seles']):
        elms[-4] = u'complemento indirecto'
        elms[-2] = u'complemento directo'
      if length == 3 and self.enclitics[0] == 'se':
        elms[0] = 'pronombre reflexivo '  


      message += self.combination.message

    if self.reflexive == (True, True):
      elms[0] = u'pronombre reflexivo (o impersonal, a ver cómo lo llamamos)'
    if self.reflexive == (True, False):
      elms[0] += u'. También puede ser un pronombre reflexivo'
    
    return message.format(', '.join(self.infinitives), *elms)


