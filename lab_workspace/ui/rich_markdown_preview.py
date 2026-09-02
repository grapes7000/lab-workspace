import json
import os
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor
from PySide6.QtWebEngineWidgets import QWebEngineView


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "markdown"


class _LocalOnlyInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        if info.requestUrl().scheme() not in {"about", "data", "file", "qrc"}:
            info.block(True)


class _ExternalLinkPage(QWebEnginePage):
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if navigation_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return url.scheme() in {"about", "data", "file", "qrc"}


class RichMarkdownPreview(QWebEngineView):
    _interceptor = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document_path = None
        profile = QWebEngineProfile.defaultProfile()
        if RichMarkdownPreview._interceptor is None:
            RichMarkdownPreview._interceptor = _LocalOnlyInterceptor(profile)
            profile.setUrlRequestInterceptor(RichMarkdownPreview._interceptor)
        self.setPage(_ExternalLinkPage(profile, self))
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)

    @staticmethod
    def _asset_url(name):
        return (ASSET_DIR / name).as_uri()

    @classmethod
    def html_for_markdown(cls, markdown):
        source = json.dumps(markdown).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
        assets = {name: cls._asset_url(name) for name in (
            "katex.min.css", "highlight-github.min.css", "markdown-it.min.js",
            "markdown-it-task-lists.min.js", "katex.min.js", "mhchem.min.js", "katex-auto-render.min.js",
            "highlight.min.js", "mermaid.min.js",
        )}
        return f"""<!doctype html>
<html><head><meta charset=\"utf-8\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self' file: data:; img-src file: data:; style-src 'self' file: 'unsafe-inline'; script-src 'self' file: 'unsafe-inline'; font-src file: data:; connect-src 'none'\">
<link rel=\"stylesheet\" href=\"{assets['katex.min.css']}\"><link rel=\"stylesheet\" href=\"{assets['highlight-github.min.css']}\">
<style>body{{margin:12px;color:#292b2f;background:#fff;font:14px sans-serif;line-height:1.5}}img{{max-width:100%;height:auto}}pre{{padding:10px;background:#f5f5f6;border:1px solid #d3d4d7;border-radius:3px;overflow:auto}}code{{font-family:monospace}}table{{border-collapse:collapse}}th,td{{padding:6px 8px;border:1px solid #d3d4d7}}th{{background:#f0f0f1}}blockquote{{margin-left:0;padding-left:12px;border-left:3px solid #d3d4d7;color:#73767d}}mark{{background:#fff1a8;padding:0 2px;border-radius:2px}}.mermaid-error{{color:#9f2222;white-space:pre-wrap}}.callout{{margin:12px 0;padding:10px 12px;border-left:4px solid #4b8ec8;background:#eef6fd;color:#25313d}}.callout-title{{font-weight:700;text-transform:uppercase;font-size:12px;letter-spacing:.04em;margin-bottom:4px}}.callout-tip,.callout-note{{border-color:#378a63;background:#edf8f1}}.callout-warning{{border-color:#b57912;background:#fff8e6}}.callout-danger{{border-color:#bb4141;background:#fff0f0}}.callout-quote,.callout-example{{border-color:#73767d;background:#f4f5f6}}.wiki-link{{color:#2d6da3;text-decoration:underline;text-decoration-style:dotted;cursor:default}}.obsidian-embed{{display:block;padding:8px 10px;border:1px dashed #aeb3ba;border-radius:3px;color:#666d75;background:#fafafa;font-style:italic}}.markdown-tag{{display:inline-block;padding:0 5px;border-radius:9px;background:#e8eff6;color:#326c9c;font-size:.9em}}</style>
</head><body><main id=\"content\"></main>
<script src=\"{assets['markdown-it.min.js']}\"></script><script src=\"{assets['markdown-it-task-lists.min.js']}\"></script><script src=\"{assets['katex.min.js']}\"></script><script src=\"{assets['mhchem.min.js']}\"></script><script src=\"{assets['katex-auto-render.min.js']}\"></script><script src=\"{assets['highlight.min.js']}\"></script><script src=\"{assets['mermaid.min.js']}\"></script>
<script>
const source = {source};
const content = document.getElementById('content');
const renderer = window.markdownit({{html:false, linkify:true, typographer:false}}).use(window.markdownitTaskLists, {{enabled:true}});
content.innerHTML = renderer.render(source);
function installCallouts() {{
  content.querySelectorAll('blockquote').forEach((block) => {{
    const first = block.querySelector('p');
    if (!first) return;
    const match = first.textContent.match(/^\\[!([A-Za-z]+)\\](?:[+-])?(?:\\s+([^\\n]+))?/);
    if (!match) return;
    const type = match[1].toLowerCase();
    const title = match[2] || match[1];
    first.textContent = first.textContent.slice(match[0].length).replace(/^\\n/, '');
    if (!first.textContent) first.remove();
    const heading = document.createElement('div');
    heading.className = 'callout-title';
    heading.textContent = title;
    block.classList.add('callout', `callout-${{type}}`);
    block.prepend(heading);
  }});
}}
function replaceObsidianSyntax() {{
  const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  const pattern = /(!)?\\[\\[([^\\]|]+)(?:\\|([^\\]]+))?\\]\\]|==([^=\\n]+)==|(^|[\\s(])#([A-Za-z][\\w/-]*)/g;
  nodes.forEach((node) => {{
    const parent = node.parentElement;
    if (!parent || parent.closest('code, pre, script, style')) return;
    const value = node.nodeValue;
    pattern.lastIndex = 0;
    if (!pattern.test(value)) return;
    pattern.lastIndex = 0;
    const fragment = document.createDocumentFragment();
    let last = 0;
    value.replace(pattern, (match, bang, target, alias, highlight, prefix, tag, offset) => {{
      fragment.append(document.createTextNode(value.slice(last, offset)));
      if (target) {{
        const element = document.createElement(bang ? 'span' : 'span');
        element.className = bang ? 'obsidian-embed' : 'wiki-link';
        element.textContent = bang ? `Embedded item: ${{target}}` : (alias || target);
        element.dataset.target = target;
        fragment.append(element);
      }} else if (highlight) {{
        const mark = document.createElement('mark');
        mark.textContent = highlight;
        fragment.append(mark);
      }} else {{
        fragment.append(document.createTextNode(prefix));
        const badge = document.createElement('span');
        badge.className = 'markdown-tag';
        badge.textContent = `#${{tag}}`;
        fragment.append(badge);
      }}
      last = offset + match.length;
      return match;
    }});
    fragment.append(document.createTextNode(value.slice(last)));
    node.replaceWith(fragment);
  }});
}}
installCallouts();
replaceObsidianSyntax();
document.querySelectorAll('pre code').forEach((code) => {{
  if (!code.classList.contains('language-mermaid')) window.hljs.highlightElement(code);
}});
document.querySelectorAll('pre code.language-mermaid').forEach((code, index) => {{
  const diagram = document.createElement('pre');
  diagram.className = 'mermaid';
  diagram.id = `mermaid-${{index}}`;
  diagram.textContent = code.textContent;
  code.parentElement.replaceWith(diagram);
}});
window.mermaid.initialize({{startOnLoad:false, securityLevel:'strict', theme:'default'}});
window.mermaid.run({{nodes:document.querySelectorAll('.mermaid')}}).catch((error) => {{
  document.querySelectorAll('.mermaid').forEach((diagram) => {{
    const fallback = document.createElement('pre'); fallback.className = 'mermaid-error';
    fallback.textContent = `Mermaid rendering failed:\\n${{diagram.textContent}}`;
    diagram.replaceWith(fallback);
  }});
}}).finally(() => {{
  window.renderMathInElement(content, {{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}], throwOnError:false, ignoredTags:['script','noscript','style','textarea','pre','code']}});
}});
</script></body></html>"""

    def set_document_path(self, path):
        self.document_path = Path(path) if path else None

    def set_markdown(self, markdown, document_path=None):
        self.set_document_path(document_path)
        base = QUrl.fromLocalFile(str(self.document_path.parent) + os.sep) if self.document_path else QUrl.fromLocalFile(str(ASSET_DIR) + os.sep)
        self.setHtml(self.html_for_markdown(markdown), base)
