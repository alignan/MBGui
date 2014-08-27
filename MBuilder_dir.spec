# -*- mode: python -*-

def Datafiles(*filenames, **kw):
    import os
    
    def datafile(path, strip_path=True):
        parts = path.split('/')
        path = name = os.path.join(*parts)
        if strip_path:
            name = os.path.basename(path)
        return name, path, 'DATA'

    strip_path = kw.get('strip_path', True)
    return TOC(
        datafile(filename, strip_path=strip_path)
        for filename in filenames
        if os.path.isfile(filename))

datafile = Datafiles('transparent.ico', 'mmap.xml', 'cmd.txt', strip_path=False)
		
a = Analysis(['MBuilder.py'],
             pathex=['C:\\Users\\Prod\\Desktop\\REPOSITORIES\\Python\\Workspace\\MBGui'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='MBuilder.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='transparent.ico')
coll = COLLECT(exe,
			   a.binaries,
               a.zipfiles,
               a.datas,
			   datafile,
               strip=None,
               upx=True,
               name='MBuilder')
