# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_showdoc.ipynb (unless otherwise specified).

__all__ = ['is_enum', 'is_lib_module', 're_digits_first', 'try_external_doc_link', 'is_doc_name', 'doc_link',
           'add_doc_links', 'get_source_link', 'colab_link', 'get_nb_source_link', 'nb_source_link', 'type_repr',
           'format_param', 'show_doc', 'md2html', 'get_doc_link', 'doc']

# Cell
from .imports import *
from .export import *
from .sync import *
from nbconvert import HTMLExporter

if IN_NOTEBOOK:
    from IPython.display import Markdown,display
    from IPython.core import page

# Cell
def is_enum(cls):
    "Check if `cls` is an enum or another type of class"
    return type(cls) in (enum.Enum, enum.EnumMeta)

# Cell
def is_lib_module(name):
    "Test if `name` is a library module."
    if name.startswith('_'): return False
    try:
        _ = importlib.import_module(f'{Config().lib_name}.{name}')
        return True
    except: return False

# Cell
re_digits_first = re.compile('^[0-9]+[a-z]*_')

# Cell
def try_external_doc_link(name, packages):
    "Try to find a doc link for `name` in `packages`"
    for p in packages:
        try:
            mod = importlib.import_module(f"{p}._nbdev")
            try_pack = source_nb(name, is_name=True, mod=mod)
            if try_pack:
                page = re_digits_first.sub('', try_pack).replace('.ipynb', '')
                return f'{mod.doc_url}{page}#{name}'
        except ModuleNotFoundError: return None

# Cell
def is_doc_name(name):
    "Test if `name` corresponds to a notebook that could be converted to a doc page"
    for f in Config().nbs_path.glob(f'*{name}.ipynb'):
        if re_digits_first.sub('', f.name) == f'{name}.ipynb': return True
    return False

# Cell
def doc_link(name, include_bt=True):
    "Create link to documentation for `name`."
    cname = f'`{name}`' if include_bt else name
    try:
        #Link to modules
        if is_lib_module(name) and is_doc_name(name): return f"[{cname}]({Config().doc_baseurl}{name}.html)"
        #Link to local functions
        try_local = source_nb(name, is_name=True)
        if try_local:
            page = re_digits_first.sub('', try_local).replace('.ipynb', '')
            return f'[{cname}]({Config().doc_baseurl}{page}.html#{name})'
        ##Custom links
        mod = get_nbdev_module()
        link = mod.custom_doc_links(name)
        return f'[{cname}]({link})' if link is not None else cname
    except: return cname

# Cell
_re_backticks = re.compile(r"""
# Catches any link of the form \[`obj`\](old_link) or just `obj`,
#   to either update old links or add the link to the docs of obj
\[`      #     Opening [ and `
([^`]*)  #     Catching group with anything but a `
`\]      #     ` then closing ]
(?:      #     Beginning of non-catching group
\(       #       Opening (
[^)]*    #       Anything but a closing )
\)       #       Closing )
)        #     End of non-catching group
|        # OR
`        #     Opening `
([^`]*)  #       Anything but a `
`        #     Closing `
""", re.VERBOSE)

# Cell
def add_doc_links(text, elt=None):
    "Search for doc links for any item between backticks in `text` and isnter them"
    def _replace_link(m):
        try:
            if m.group(2) in inspect.signature(elt).parameters: return f'`{m.group(2)}`'
        except: pass
        return doc_link(m.group(1) or m.group(2))
    return _re_backticks.sub(_replace_link, text)

# Cell
def _is_type_dispatch(x): return type(x).__name__ == "TypeDispatch"
def _unwrapped_type_dispatch_func(x): return x.first() if _is_type_dispatch(x) else x

def _is_property(x): return type(x)==property
def _has_property_getter(x): return _is_property(x) and hasattr(x, 'fget') and hasattr(x.fget, 'func')
def _property_getter(x): return x.fget.func if _has_property_getter(x) else x

def _unwrapped_func(x):
    x = _unwrapped_type_dispatch_func(x)
    x = _property_getter(x)
    return x

# Cell
def get_source_link(func):
    "Return link to `func` in source code"
    func = _unwrapped_func(func)
    try: line = inspect.getsourcelines(func)[1]
    except Exception: return ''
    mod = inspect.getmodule(func)
    module = mod.__name__.replace('.', '/') + '.py'
    try:
        nbdev_mod = importlib.import_module(mod.__package__.split('.')[0] + '._nbdev')
        return f"{nbdev_mod.git_url}{module}#L{line}"
    except: return f"{module}#L{line}"

# Cell
_re_header = re.compile(r"""
# Catches any header in markdown with the title in group 1
^\s*  # Beginning of text followed by any number of whitespace
\#+   # One # or more
\s*   # Any number of whitespace
(.*)  # Catching group with anything
$     # End of text
""", re.VERBOSE)

# Cell
def colab_link(path):
    "Get a link to the notebook at `path` on Colab"
    cfg = Config()
    res = f'https://colab.research.google.com/github/{cfg.user}/{cfg.lib_name}/blob/{cfg.branch}/{cfg.nbs_path.name}/{path}.ipynb'
    display(Markdown(f'[Open `{path}` in Colab]({res})'))

# Cell
def get_nb_source_link(func, local=False, is_name=None):
    "Return a link to the notebook where `func` is defined."
    func = _unwrapped_type_dispatch_func(func)
    pref = '' if local else Config().git_url.replace('github.com', 'nbviewer.jupyter.org/github')+ Config().nbs_path.name+'/'
    is_name = is_name or isinstance(func, str)
    src = source_nb(func, is_name=is_name, return_all=True)
    if src is None: return '' if is_name else get_source_link(func)
    find_name,nb_name = src
    nb = read_nb(nb_name)
    pat = re.compile(f'^{find_name}\s+=|^(def|class)\s+{find_name}\s*\(', re.MULTILINE)
    if len(find_name.split('.')) == 2:
        clas,func = find_name.split('.')
        pat2 = re.compile(f'@patch\s*\ndef\s+{func}\s*\([^:]*:\s*{clas}\s*(?:,|\))')
    else: pat2 = None
    for i,cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            if re.search(pat, cell['source']):  break
            if pat2 is not None and re.search(pat2, cell['source']): break
    if re.search(pat, cell['source']) is None and (pat2 is not None and re.search(pat2, cell['source']) is None):
        return '' if is_name else get_function_source(func)
    header_pat = re.compile(r'^\s*#+\s*(.*)$')
    while i >= 0:
        cell = nb['cells'][i]
        if cell['cell_type'] == 'markdown' and _re_header.search(cell['source']):
            title = _re_header.search(cell['source']).groups()[0]
            anchor = '-'.join([s for s in title.split(' ') if len(s) > 0])
            return f'{pref}{nb_name}#{anchor}'
        i-=1
    return f'{pref}{nb_name}'

# Cell
def nb_source_link(func, is_name=None, disp=True, local=True):
    "Show a relative link to the notebook where `func` is defined"
    is_name = is_name or isinstance(func, str)
    func_name = func if is_name else qual_name(func)
    link = get_nb_source_link(func, local=local, is_name=is_name)
    text = func_name if local else f'{func_name} (GitHub)'
    if disp: display(Markdown(f'[{text}]({link})'))
    else: return link

# Cell
from fastcore.script import Param

# Cell
def type_repr(t):
    "Representation of type `t` (in a type annotation)"
    if (isinstance(t, Param)): return f'"{t.help}"'
    if getattr(t, '__args__', None):
        args = t.__args__
        if len(args)==2 and args[1] == type(None):
            return f'`Optional`\[{type_repr(args[0])}\]'
        reprs = ', '.join([type_repr(o) for o in args])
        return f'{doc_link(get_name(t))}\[{reprs}\]'
    else: return doc_link(get_name(t))

# Cell
_arg_prefixes = {inspect._VAR_POSITIONAL: '\*', inspect._VAR_KEYWORD:'\*\*'}

def format_param(p):
    "Formats function param to `param:Type=val` with font weights: param=bold, val=italic"
    arg_prefix = _arg_prefixes.get(p.kind, '') # asterisk prefix for *args and **kwargs
    res = f"**{arg_prefix}`{p.name}`**"
    if hasattr(p, 'annotation') and p.annotation != p.empty: res += f':{type_repr(p.annotation)}'
    if p.default != p.empty:
        default = getattr(p.default, 'func', p.default) #For partials
        if hasattr(default,'__name__'): default = getattr(default, '__name__')
        else: default = repr(default)
        if is_enum(default.__class__):                  #Enum have a crappy repr
            res += f'=*`{default.__class__.__name__}.{default.name}`*'
        else: res += f'=*`{default}`*'
    return res

# Cell
def _format_enum_doc(enum, full_name):
    "Formatted `enum` definition to show in documentation"
    vals = ', '.join(enum.__members__.keys())
    return f'<code>{full_name}</code>',f'<code>Enum</code> = [{vals}]'

# Cell
def _escape_chars(s):
    return s.replace('_', '\_')

def _format_func_doc(func, full_name=None):
    "Formatted `func` definition to show in documentation"
    try:
        sig = inspect.signature(func)
        fmt_params = [format_param(param) for name,param
                  in sig.parameters.items() if name not in ('self','cls')]
    except: fmt_params = []
    name = f'<code>{full_name or func.__name__}</code>'
    arg_str = f"({', '.join(fmt_params)})"
    f_name = f"<code>class</code> {name}" if inspect.isclass(func) else name
    return f'{f_name}',f'{name}{arg_str}'

# Cell
def _format_cls_doc(cls, full_name):
    "Formatted `cls` definition to show in documentation"
    parent_class = inspect.getclasstree([cls])[-1][0][1][0]
    name,args = _format_func_doc(cls, full_name)
    if parent_class != object: args += f' :: {doc_link(get_name(parent_class))}'
    return name,args

# Cell
def show_doc(elt, doc_string=True, name=None, title_level=None, disp=True, default_cls_level=2):
    "Show documentation for element `elt`. Supported types: class, function, and enum."
    elt = getattr(elt, '__func__', elt)
    qname = name or qual_name(elt)
    if inspect.isclass(elt):
        if is_enum(elt): name,args = _format_enum_doc(elt, qname)
        else:            name,args = _format_cls_doc (elt, qname)
    elif callable(elt):  name,args = _format_func_doc(elt, qname)
    else:                name,args = f"<code>{qname}</code>", ''
    link = get_source_link(elt)
    source_link = f'<a href="{link}" class="source_link" style="float:right">[source]</a>'
    title_level = title_level or (default_cls_level if inspect.isclass(elt) else 4)
    doc =  f'<h{title_level} id="{qname}" class="doc_header">{name}{source_link}</h{title_level}>'
    doc += f'\n\n> {args}\n\n' if len(args) > 0 else '\n\n'
    if doc_string and inspect.getdoc(elt):
        s = inspect.getdoc(elt)
        # show_doc is used by doc so should not rely on Config
        try: monospace = (Config().get('monospace_docstrings') == 'True')
        except: monospace = False
        # doc links don't work inside markdown pre/code blocks
        s = f'```\n{s}\n```' if monospace else add_doc_links(s, elt)
        doc += s
    if disp: display(Markdown(doc))
    else: return doc

# Cell
def md2html(md):
    "Convert markdown `md` to HTML code"
    import nbconvert
    if nbconvert.__version__ < '5.5.0': return HTMLExporter().markdown2html(md)
    else: return HTMLExporter().markdown2html(collections.defaultdict(lambda: collections.defaultdict(dict)), md)

# Cell
def get_doc_link(func):
    mod = inspect.getmodule(func)
    module = mod.__name__.replace('.', '/') + '.py'
    try:
        nbdev_mod = importlib.import_module(mod.__package__.split('.')[0] + '._nbdev')
        try_pack = source_nb(func, mod=nbdev_mod)
        if try_pack:
            page = '.'.join(try_pack.split('_')[1:]).replace('.ipynb', '')
            return f'{nbdev_mod.doc_url}{page}#{qual_name(func)}'
    except: return None

# Cell
def doc(elt):
    "Show `show_doc` info in preview window when used in a notebook"
    md = show_doc(elt, disp=False)
    doc_link = get_doc_link(elt)
    if doc_link is not None:
        md += f'\n\n<a href="{doc_link}" target="_blank" rel="noreferrer noopener">Show in docs</a>'
    output = md2html(md)
    if IN_COLAB: get_ipython().run_cell_magic(u'html', u'', output)
    else:
        try: page.page({'text/html': output})
        except: display(Markdown(md))