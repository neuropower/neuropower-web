import os

def model(num_subjects,dir):
    mat_txt = ['/NumWaves       1',
             '/NumPoints      %d' % num_subjects,
             '/PPheights      %e' % 1,
             '',
             '/Matrix']
    for i in range(num_subjects):
      mat_txt += ['%e' % 1]
    mat_txt = '\n'.join(mat_txt)

    con_txt = ['/ContrastName1   group mean',
             '/NumWaves       1',
             '/NumContrasts   1',
             '/PPheights          %e' % 1,
             '/RequiredEffect     100.0',
             '',
             '/Matrix',
             '%e' % 1]
    con_txt = '\n'.join(con_txt)

    grp_txt = ['/NumWaves       1',
             '/NumPoints      %d' % num_subjects,
             '',
             '/Matrix']
    for i in range(num_subjects):
      grp_txt += ['1']
    grp_txt = '\n'.join(grp_txt)

    txt = {'design.mat': mat_txt,
         'design.con': con_txt,
         'design.grp': grp_txt}

    # write design files
    for i, name in enumerate(['design.mat', 'design.con', 'design.grp']):
      f = open(os.path.join(dir, name), 'wt')
      f.write(txt[name])
      f.close()
